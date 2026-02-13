from datetime import datetime, timedelta
from typing import Optional, List

from sqlalchemy import func
from sqlmodel import Session, select

from app.core.errors import BadRequestError, NotFoundError
from app.core.time import utc_now
from app.models import Customer, Payment, PaymentAllocation, Sale
from app.services.sale_service import get_sale

_ALLOWED_METHODS = {"cash", "wechat", "alipay", "bank", "transfer", "other", "现金", "微信", "支付宝", "银行卡", "转账", "其他"}
_ALLOWED_PAY_TYPES = {"paid_full", "credit", "partial"}


def _parse_iso_dt(dt_str: Optional[str], *, end_of_day: bool = False) -> datetime:
    if not dt_str:
        return utc_now()
    if len(dt_str) == 10:
        dt = datetime.fromisoformat(f"{dt_str}T00:00:00+00:00")
        return dt + timedelta(days=1) - timedelta(microseconds=1) if end_of_day else dt
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


def _to_iso_z(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def _gen_receipt_no() -> str:
    return f"RC{utc_now().strftime('%Y%m%d%H%M%S%f')}"


def _sum_sale_paid(session: Session, sale_id: int) -> float:
    direct = float(session.exec(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.sale_id == sale_id)).one() or 0)
    alloc = float(
        session.exec(
            select(func.coalesce(func.sum(PaymentAllocation.amount), 0)).where(PaymentAllocation.sale_id == sale_id)
        ).one()
        or 0
    )
    return round(direct + alloc, 2)


def recompute_sale_payment(session: Session, sale: Sale):
    paid = _sum_sale_paid(session, sale.id)
    sale.paid_amount = round(paid, 2)
    sale.ar_amount = round(max(float(sale.total_amount) - sale.paid_amount, 0), 2)
    if sale.paid_amount <= 0:
        sale.payment_status = "unpaid"
    elif sale.paid_amount + 1e-6 >= float(sale.total_amount):
        sale.payment_status = "paid"
    else:
        sale.payment_status = "partial"
    session.add(sale)


def create_payment(session: Session, sale_id: int, amount: float, method: str, paid_at: Optional[str], note: Optional[str]):
    sale = session.get(Sale, sale_id)
    if not sale:
        raise NotFoundError("单据不存在")
    if method not in _ALLOWED_METHODS:
        raise BadRequestError("付款方式不合法")
    if amount <= 0:
        raise BadRequestError("金额必须大于0")
    if amount > float(sale.ar_amount) + 1e-6:
        raise BadRequestError("收款金额不能超过该单未付金额")

    payment = Payment(
        receipt_no=_gen_receipt_no(),
        customer_id=sale.customer_id,
        sale_id=sale.id,
        pay_type="partial",
        amount=round(float(amount), 2),
        method=method,
        paid_at=_parse_iso_dt(paid_at),
        note=note,
    )
    session.add(payment)
    session.flush()

    recompute_sale_payment(session, sale)
    session.commit()
    session.refresh(payment)
    return payment


def submit_sale_payment(session: Session, sale_id: int, pay_type: str, method: str, amount: Optional[float], note: Optional[str]):
    sale = session.get(Sale, sale_id)
    if not sale:
        raise NotFoundError("单据不存在")
    if pay_type not in _ALLOWED_PAY_TYPES:
        raise BadRequestError("pay_type 不合法")
    if method not in _ALLOWED_METHODS:
        raise BadRequestError("method 不合法")

    pay_amount = float(sale.ar_amount) if pay_type == "paid_full" else (0.0 if pay_type == "credit" else float(amount or 0))

    created = None
    if pay_amount > 0:
        created = Payment(
            receipt_no=_gen_receipt_no(),
            customer_id=sale.customer_id,
            sale_id=sale.id,
            pay_type=pay_type,
            amount=round(pay_amount, 2),
            method=method,
            paid_at=utc_now(),
            note=note,
        )
        session.add(created)
        session.flush()

    recompute_sale_payment(session, sale)
    session.commit()
    updated_sale = get_sale(session, sale.id)

    if created:
        session.refresh(created)
        payment_payload = {
            "id": created.id,
            "receipt_no": created.receipt_no,
            "sale_id": created.sale_id,
            "customer_id": created.customer_id,
            "pay_type": created.pay_type,
            "amount": created.amount,
            "method": created.method,
            "paid_at": _to_iso_z(created.paid_at),
            "note": created.note,
        }
    else:
        payment_payload = {
            "id": None,
            "receipt_no": None,
            "sale_id": sale.id,
            "customer_id": sale.customer_id,
            "pay_type": pay_type,
            "amount": 0,
            "method": method,
            "paid_at": _to_iso_z(utc_now()),
            "note": note,
        }
    return updated_sale, payment_payload


def list_sale_payments(session: Session, sale_id: int):
    sale = session.get(Sale, sale_id)
    if not sale:
        raise NotFoundError("单据不存在")

    rows = session.exec(select(Payment).where(Payment.sale_id == sale_id).order_by(Payment.paid_at.desc(), Payment.id.desc())).all()
    alloc_rows = session.exec(
        select(PaymentAllocation, Payment)
        .join(Payment, Payment.id == PaymentAllocation.payment_id)
        .where(PaymentAllocation.sale_id == sale_id)
        .order_by(Payment.paid_at.desc(), Payment.id.desc())
    ).all()

    items = [
        {
            "id": p.id,
            "receipt_no": p.receipt_no,
            "sale_id": sale_id,
            "amount": p.amount,
            "method": p.method,
            "pay_type": p.pay_type,
            "paid_at": _to_iso_z(p.paid_at),
            "note": p.note,
        }
        for p in rows
    ]
    for a, p in alloc_rows:
        items.append(
            {
                "id": p.id,
                "receipt_no": p.receipt_no,
                "sale_id": sale_id,
                "amount": a.amount,
                "method": p.method,
                "pay_type": p.pay_type,
                "paid_at": _to_iso_z(p.paid_at),
                "note": p.note,
            }
        )
    items.sort(key=lambda x: (x["paid_at"], x["id"]), reverse=True)
    return items


def list_customer_payments(session: Session, customer_id: int, *, page: int, page_size: int, start_date: Optional[str], end_date: Optional[str]):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise NotFoundError("客户不存在")

    stmt = select(Payment).where(Payment.customer_id == customer_id)
    if start_date:
        stmt = stmt.where(Payment.paid_at >= _parse_iso_dt(start_date))
    if end_date:
        stmt = stmt.where(Payment.paid_at <= _parse_iso_dt(end_date, end_of_day=True))

    rows_all = session.exec(stmt.order_by(Payment.paid_at.desc(), Payment.id.desc())).all()
    total = len(rows_all)
    rows = rows_all[(page - 1) * page_size : page * page_size]

    items = []
    for p in rows:
        sale_nos = []
        if p.sale_id:
            sale = session.get(Sale, p.sale_id)
            if sale:
                sale_nos = [sale.sale_no]
        alloc_sales = session.exec(
            select(Sale)
            .join(PaymentAllocation, PaymentAllocation.sale_id == Sale.id)
            .where(PaymentAllocation.payment_id == p.id)
            .order_by(Sale.sale_date.asc(), Sale.id.asc())
        ).all()
        for s in alloc_sales:
            if s.sale_no not in sale_nos:
                sale_nos.append(s.sale_no)

        items.append(
            {
                "id": p.id,
                "receipt_no": p.receipt_no,
                "sale_id": p.sale_id,
                "sale_no": sale_nos[0] if sale_nos else None,
                "sale_nos": sale_nos,
                "amount": p.amount,
                "method": p.method,
                "pay_type": p.pay_type,
                "paid_at": _to_iso_z(p.paid_at),
                "note": p.note,
                "has_allocations": len(sale_nos) > 1 or bool(alloc_sales),
            }
        )
    return items, total


def list_open_sales(session: Session, customer_id: int, *, page: int, page_size: int, q: Optional[str], start_date: Optional[str], end_date: Optional[str]):
    if not session.get(Customer, customer_id):
        raise NotFoundError("客户不存在")
    stmt = select(Sale).where(Sale.customer_id == customer_id, Sale.ar_amount > 0)
    if start_date:
        stmt = stmt.where(Sale.sale_date >= _parse_iso_dt(start_date))
    if end_date:
        stmt = stmt.where(Sale.sale_date <= _parse_iso_dt(end_date, end_of_day=True))
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where((Sale.sale_no.ilike(like)) | (Sale.note.ilike(like)) | (Sale.project.ilike(like)))
    rows_all = session.exec(stmt.order_by(Sale.sale_date.asc(), Sale.id.asc())).all()
    total = len(rows_all)
    rows = rows_all[(page - 1) * page_size : page * page_size]
    items = [
        {
            "id": s.id,
            "sale_no": s.sale_no,
            "sale_date": _to_iso_z(s.sale_date),
            "total_amount": s.total_amount,
            "paid_amount": s.paid_amount,
            "balance": s.ar_amount,
            "status": s.payment_status,
            "note": s.note,
        }
        for s in rows
    ]
    return items, total


def allocate_to_sales(session: Session, *, customer_id: int, sale_ids: List[int], amount: float, method: str, paid_at: Optional[str], note: Optional[str]):
    if amount <= 0:
        raise BadRequestError("金额必须大于0")
    if method not in _ALLOWED_METHODS:
        raise BadRequestError("付款方式不合法")
    customer = session.get(Customer, customer_id)
    if not customer:
        raise NotFoundError("客户不存在")

    sales = session.exec(select(Sale).where(Sale.customer_id == customer_id, Sale.id.in_(sale_ids))).all()
    if not sales:
        raise BadRequestError("未找到可分配订单")
    sales.sort(key=lambda s: (s.sale_date, s.id))

    open_sales = [s for s in sales if float(s.ar_amount) > 0]
    if not open_sales:
        raise BadRequestError("所选订单均已结清")

    selected_total = sum(float(s.ar_amount) for s in open_sales)
    if amount > selected_total + 1e-6:
        raise BadRequestError("收款金额超过所选订单未收合计")

    payment = Payment(
        receipt_no=_gen_receipt_no(),
        customer_id=customer_id,
        sale_id=None,
        pay_type="partial",
        amount=round(float(amount), 2),
        method=method,
        paid_at=_parse_iso_dt(paid_at),
        note=note,
    )
    session.add(payment)
    session.flush()

    remaining = round(float(amount), 2)
    allocations = []
    for s in open_sales:
        if remaining <= 0:
            break
        applied = round(min(float(s.ar_amount), remaining), 2)
        if applied <= 0:
            continue
        alloc = PaymentAllocation(payment_id=payment.id, sale_id=s.id, amount=applied)
        session.add(alloc)
        remaining = round(remaining - applied, 2)
        recompute_sale_payment(session, s)
        allocations.append({"sale_id": s.id, "sale_no": s.sale_no, "amount": applied})

    session.commit()
    for s in open_sales:
        session.refresh(s)

    return {
        "payment": {
            "id": payment.id,
            "receipt_no": payment.receipt_no,
            "customer_id": payment.customer_id,
            "amount": payment.amount,
            "method": payment.method,
            "paid_at": _to_iso_z(payment.paid_at),
            "note": payment.note,
        },
        "allocations": allocations,
        "sales": [
            {
                "sale_id": s.id,
                "sale_no": s.sale_no,
                "paid_amount": s.paid_amount,
                "balance": s.ar_amount,
                "status": s.payment_status,
            }
            for s in open_sales
        ],
    }


def get_payment_allocations(session: Session, *, customer_id: int, payment_id: int):
    payment = session.get(Payment, payment_id)
    if not payment or payment.customer_id != customer_id:
        raise NotFoundError("收款记录不存在")
    rows = session.exec(
        select(PaymentAllocation, Sale)
        .join(Sale, Sale.id == PaymentAllocation.sale_id)
        .where(PaymentAllocation.payment_id == payment_id)
        .order_by(PaymentAllocation.id.asc())
    ).all()
    items = [{"sale_id": s.id, "sale_no": s.sale_no, "amount": a.amount} for a, s in rows]
    return {"payment_id": payment_id, "items": items}


def batch_apply(
    session: Session,
    *,
    customer_id: int,
    sale_ids: List[int],
    total_amount: float,
    method: str,
    paid_at: Optional[str],
    note: Optional[str],
):
    result = allocate_to_sales(
        session,
        customer_id=customer_id,
        sale_ids=sale_ids,
        amount=total_amount,
        method=method,
        paid_at=paid_at,
        note=note,
    )
    return 1, [
        {
            "sale_id": row["sale_id"],
            "sale_no": row["sale_no"],
            "applied_amount": row["amount"],
            "after_paid_amount": next((s["paid_amount"] for s in result["sales"] if s["sale_id"] == row["sale_id"]), 0),
            "after_balance": next((s["balance"] for s in result["sales"] if s["sale_id"] == row["sale_id"]), 0),
            "after_status": next((s["status"] for s in result["sales"] if s["sale_id"] == row["sale_id"]), "unpaid"),
        }
        for row in result["allocations"]
    ]


def allocate_customer_receipt(session: Session, *, customer_id: int, method: str, amount: float, note: Optional[str], allocate_mode: str = "oldest_first"):
    if allocate_mode != "oldest_first":
        raise BadRequestError("目前仅支持 oldest_first")
    sales = session.exec(select(Sale.id).where(Sale.customer_id == customer_id, Sale.ar_amount > 0).order_by(Sale.sale_date.asc(), Sale.id.asc())).all()
    sale_ids = [sid for sid in sales]
    result = allocate_to_sales(session, customer_id=customer_id, sale_ids=sale_ids, amount=amount, method=method, paid_at=None, note=note)
    return 1, result["allocations"]


def customer_delete_check(session: Session, customer_id: int):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise NotFoundError("客户不存在")

    sales = session.exec(select(Sale).where(Sale.customer_id == customer_id).order_by(Sale.sale_date.desc(), Sale.id.desc())).all()
    payments = session.exec(select(Payment).where(Payment.customer_id == customer_id).order_by(Payment.paid_at.desc(), Payment.id.desc())).all()

    pay_rows = []
    for p in payments:
        sale_nos = []
        if p.sale_id:
            s = session.get(Sale, p.sale_id)
            if s:
                sale_nos.append(s.sale_no)
        alloc_sales = session.exec(
            select(Sale)
            .join(PaymentAllocation, PaymentAllocation.sale_id == Sale.id)
            .where(PaymentAllocation.payment_id == p.id)
        ).all()
        for s in alloc_sales:
            if s.sale_no not in sale_nos:
                sale_nos.append(s.sale_no)
        pay_rows.append({
            "id": p.id,
            "paid_at": _to_iso_z(p.paid_at),
            "amount": p.amount,
            "method": p.method,
            "sale_nos": sale_nos,
        })

    return {
        "can_delete": len(sales) == 0 and len(payments) == 0,
        "sales_count": len(sales),
        "payments_count": len(payments),
        "sales": [{"id": s.id, "sale_no": s.sale_no, "created_at": _to_iso_z(s.created_at), "balance": s.ar_amount} for s in sales],
        "payments": pay_rows,
    }


def delete_customer_records(session: Session, *, customer_id: int, sale_ids: List[int], payment_ids: List[int]):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise NotFoundError("客户不存在")

    touched_sale_ids = set()

    # delete payments first (and rollback sales by recompute)
    for pid in payment_ids:
        p = session.get(Payment, pid)
        if not p or p.customer_id != customer_id:
            continue
        if p.sale_id:
            touched_sale_ids.add(p.sale_id)
        allocs = session.exec(select(PaymentAllocation).where(PaymentAllocation.payment_id == p.id)).all()
        for a in allocs:
            touched_sale_ids.add(a.sale_id)
            session.delete(a)
        session.delete(p)

    # delete sales and cleanup allocations/payments that become empty
    for sid in sale_ids:
        s = session.get(Sale, sid)
        if not s or s.customer_id != customer_id:
            continue
        touched_sale_ids.add(s.id)

        allocs = session.exec(select(PaymentAllocation).where(PaymentAllocation.sale_id == s.id)).all()
        affected_payment_ids = set(a.payment_id for a in allocs)
        for a in allocs:
            session.delete(a)

        # cleanup orphan payments after removing allocations
        for pid in affected_payment_ids:
            pay = session.get(Payment, pid)
            if not pay:
                continue
            alloc_count = int(session.exec(select(func.count()).select_from(PaymentAllocation).where(PaymentAllocation.payment_id == pid)).one() or 0)
            if alloc_count == 0 and (pay.sale_id is None or pay.sale_id == s.id):
                session.delete(pay)
            elif pay.sale_id == s.id:
                pay.sale_id = None
                session.add(pay)

        session.delete(s)

    session.flush()

    # recompute remaining touched sales
    for sid in list(touched_sale_ids):
        s = session.get(Sale, sid)
        if s:
            recompute_sale_payment(session, s)

    session.commit()

    left_sales = int(session.exec(select(func.count()).select_from(Sale).where(Sale.customer_id == customer_id)).one() or 0)
    left_payments = int(session.exec(select(func.count()).select_from(Payment).where(Payment.customer_id == customer_id)).one() or 0)
    return {
        "deleted_sale_ids": sale_ids,
        "deleted_payment_ids": payment_ids,
        "left_sales": left_sales,
        "left_payments": left_payments,
    }
