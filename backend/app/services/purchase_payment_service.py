from datetime import datetime

from sqlalchemy import func
from sqlmodel import Session, select

from app.core.errors import BadRequestError, NotFoundError
from app.core.time import utc_now
from app.models import APAllocation, Purchase, Supplier, SupplierPayment

_ALLOWED_METHODS = {"cash", "wechat", "alipay", "bank_transfer", "other"}
_METHOD_ALIASES = {"现金": "cash", "微信": "wechat", "支付宝": "alipay", "转账": "bank_transfer", "bank": "bank_transfer", "transfer": "bank_transfer", "其他": "other"}


def _normalize_method(method: str) -> str:
    value = _METHOD_ALIASES.get(method, method)
    if value not in _ALLOWED_METHODS:
        raise BadRequestError("付款方式不合法")
    return value


def _gen_receipt_no() -> str:
    return f"SP{utc_now().strftime('%Y%m%d%H%M%S%f')}"


def _sum_allocated(session: Session, payment_id: int) -> float:
    return float(session.exec(select(func.coalesce(func.sum(APAllocation.amount), 0)).where(APAllocation.payment_id == payment_id)).one() or 0)


def _recompute_purchase_ap(session: Session, purchase: Purchase):
    direct_paid = float(session.exec(select(func.coalesce(func.sum(SupplierPayment.amount), 0)).where(
        SupplierPayment.purchase_id == purchase.id)).one() or 0)
    alloc_paid = float(session.exec(select(func.coalesce(func.sum(APAllocation.amount), 0)).where(
        APAllocation.purchase_id == purchase.id)).one() or 0)
    paid = round(direct_paid + alloc_paid, 2)
    purchase.paid_amount = paid
    purchase.ap_amount = round(max(float(purchase.total_amount) - paid, 0), 2)
    session.add(purchase)


def create_supplier_payment(session: Session, payload):
    supplier = session.get(Supplier, payload.supplier_id)
    if not supplier:
        raise NotFoundError("供应商不存在")
    method = _normalize_method(payload.method)

    purchase = None
    if payload.purchase_id is not None:
        purchase = session.get(Purchase, payload.purchase_id)
        if not purchase or purchase.supplier_id != supplier.id:
            raise BadRequestError("采购单不存在或不属于该供应商")

    payment = SupplierPayment(
        receipt_no=_gen_receipt_no(),
        supplier_id=supplier.id,
        purchase_id=payload.purchase_id,
        scene="AP_PAYMENT",
        method=method,
        amount=round(float(payload.amount), 2),
        paid_at=payload.paid_at or utc_now(),
        note=payload.note,
    )
    session.add(payment)
    session.flush()

    if purchase is not None:
        session.add(APAllocation(payment_id=payment.id, purchase_id=purchase.id, amount=payment.amount))
        _recompute_purchase_ap(session, purchase)

    session.commit()
    session.refresh(payment)
    return payment


def allocate_payment(session: Session, payment_id: int, payload):
    payment = session.get(SupplierPayment, payment_id)
    if not payment:
        raise NotFoundError("付款记录不存在")

    allocated = _sum_allocated(session, payment.id)
    remain = round(float(payment.amount) - allocated, 2)

    total_to_allocate = round(sum(float(it.amount) for it in payload.items), 2)
    if total_to_allocate <= 0:
        raise BadRequestError("核销金额必须大于0")
    if total_to_allocate > remain + 1e-6:
        raise BadRequestError("核销金额超过付款剩余可分配金额")

    purchase_ids = [it.purchase_id for it in payload.items]
    purchases = session.exec(select(Purchase).where(Purchase.id.in_(purchase_ids))).all()
    pmap = {p.id: p for p in purchases}

    for it in payload.items:
        purchase = pmap.get(it.purchase_id)
        if not purchase or purchase.supplier_id != payment.supplier_id:
            raise BadRequestError("存在无效采购单")
        if float(it.amount) > float(purchase.ap_amount) + 1e-6:
            raise BadRequestError("核销金额超过采购单应付余额")

    for it in payload.items:
        session.add(APAllocation(payment_id=payment.id, purchase_id=it.purchase_id, amount=round(float(it.amount), 2)))

    for p in purchases:
        _recompute_purchase_ap(session, p)

    session.commit()
    return {"payment_id": payment.id, "allocated_amount": total_to_allocate, "remain_amount": round(remain - total_to_allocate, 2)}


def list_supplier_open_purchases(session: Session, supplier_id: int):
    supplier = session.get(Supplier, supplier_id)
    if not supplier:
        raise NotFoundError("供应商不存在")
    rows = session.exec(select(Purchase).where(Purchase.supplier_id == supplier_id, Purchase.ap_amount > 0).order_by(Purchase.purchase_date.asc(), Purchase.id.asc())).all()
    return rows


def list_supplier_payments(session: Session, supplier_id: int):
    supplier = session.get(Supplier, supplier_id)
    if not supplier:
        raise NotFoundError("供应商不存在")
    rows = session.exec(select(SupplierPayment).where(SupplierPayment.supplier_id == supplier_id).order_by(SupplierPayment.paid_at.desc(), SupplierPayment.id.desc())).all()
    items = []
    for p in rows:
        allocated = _sum_allocated(session, p.id)
        items.append({
            "id": p.id,
            "receipt_no": p.receipt_no,
            "supplier_id": p.supplier_id,
            "purchase_id": p.purchase_id,
            "scene": p.scene,
            "method": p.method,
            "amount": p.amount,
            "allocated_amount": round(allocated, 2),
            "remain_amount": round(float(p.amount) - float(allocated), 2),
            "paid_at": p.paid_at,
            "note": p.note,
        })
    return items
