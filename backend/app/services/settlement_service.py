from typing import Optional

from sqlmodel import Session

from app.core.errors import BadRequestError, NotFoundError
from app.core.time import utc_now
from app.models import Payment, Sale, SaleOperation
from app.services import payment_service

_ALLOWED_SETTLEMENT = {"UNPAID", "PARTIAL", "PAID"}
_ALLOWED_METHODS = {"cash", "wechat", "alipay", "bank_transfer", "bank", "transfer", "other", "现金", "微信", "支付宝", "银行卡", "转账", "其他"}


def _target_paid(total_amount: float, settlement_status: str, paid_amount: float, payment_method: Optional[str]) -> float:
    status = (settlement_status or "").upper()
    if status not in _ALLOWED_SETTLEMENT:
        raise BadRequestError("settlement_status 仅支持 UNPAID/PARTIAL/PAID")
    total = round(float(total_amount), 2)
    if status == "UNPAID":
        return 0.0
    if status == "PAID":
        if payment_method not in _ALLOWED_METHODS:
            raise BadRequestError("PAID 时必须选择付款方式")
        return total

    # PARTIAL
    paid = round(float(paid_amount or 0), 2)
    if not (0 < paid < total):
        raise BadRequestError("PARTIAL 时 paid_amount 必须大于0且小于应收")
    if payment_method not in _ALLOWED_METHODS:
        raise BadRequestError("PARTIAL 时必须选择付款方式")
    return paid


def apply_settlement_compat(
    session: Session,
    *,
    sale_id: int,
    settlement_status: str,
    paid_amount: float,
    payment_method: Optional[str],
    payment_note: Optional[str],
):
    sale = session.get(Sale, sale_id)
    if not sale:
        raise NotFoundError("单据不存在")

    target_paid = _target_paid(float(sale.total_amount), settlement_status, paid_amount, payment_method)
    current_paid = round(float(sale.paid_amount or 0), 2)
    delta = round(target_paid - current_paid, 2)

    if abs(delta) > 1e-6:
        pay = Payment(
            receipt_no=payment_service._gen_receipt_no(),
            customer_id=sale.customer_id,
            sale_id=sale.id,
            pay_type="settlement_adjust" if delta > 0 else "settlement_reverse",
            amount=delta,
            method=payment_method or "other",
            paid_at=utc_now(),
            note=payment_note,
        )
        session.add(pay)

    payment_service.recompute_sale_payment(session, sale)
    if settlement_status == "UNPAID":
        sale.payment_method = None
    else:
        sale.payment_method = payment_method
    sale.payment_note = payment_note if payment_note else None
    session.add(sale)
    session.commit()
    return sale


def mark_sale_void(session: Session, *, sale_id: int, note: Optional[str]):
    sale = session.get(Sale, sale_id)
    if not sale:
        raise NotFoundError("单据不存在")
    if sale.biz_status == "VOIDED":
        raise BadRequestError("单据已作废")

    sale.biz_status = "VOIDED"
    session.add(SaleOperation(sale_id=sale.id, op_type="VOID", amount=float(sale.total_amount), note=note))
    session.add(sale)
    session.commit()
    return sale


def reverse_settlement(session: Session, *, sale_id: int, amount: Optional[float], note: Optional[str]):
    sale = session.get(Sale, sale_id)
    if not sale:
        raise NotFoundError("单据不存在")

    can_reverse = round(float(sale.paid_amount), 2)
    reverse_amount = round(float(amount if amount is not None else can_reverse), 2)
    if reverse_amount <= 0:
        raise BadRequestError("反结算金额必须大于0")
    if reverse_amount > can_reverse + 1e-6:
        raise BadRequestError("反结算金额不能超过已收金额")

    session.add(
        Payment(
            receipt_no=payment_service._gen_receipt_no(),
            customer_id=sale.customer_id,
            sale_id=sale.id,
            pay_type="settlement_reverse",
            amount=round(-reverse_amount, 2),
            method="other",
            paid_at=utc_now(),
            note=note,
        )
    )
    session.add(SaleOperation(sale_id=sale.id, op_type="REVERSE_SETTLEMENT", amount=reverse_amount, note=note))
    payment_service.recompute_sale_payment(session, sale)
    session.add(sale)
    session.commit()
    return sale


def sale_operations(session: Session, *, sale_id: int):
    sale = session.get(Sale, sale_id)
    if not sale:
        raise NotFoundError("单据不存在")
    rows = sorted(sale.operations, key=lambda x: (x.created_at, x.id), reverse=True)
    return [
        {"id": row.id, "op_type": row.op_type, "amount": row.amount, "note": row.note, "created_at": row.created_at.isoformat().replace('+00:00', 'Z')}
        for row in rows
    ]
