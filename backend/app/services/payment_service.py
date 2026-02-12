from datetime import datetime
from typing import Optional, List, Tuple

from sqlalchemy import func
from sqlmodel import Session, select

from app.core.time import utc_now
from app.models import Payment, Sale, Customer

_ALLOWED_METHODS = {"现金", "微信", "支付宝", "转账", "其他"}


def _parse_iso_dt(dt_str: Optional[str]) -> datetime:
    if not dt_str:
        return utc_now()
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


def get_sale_paid_amount(session: Session, sale_id: int) -> float:
    amt = session.exec(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.sale_id == sale_id)).one()
    return float(amt or 0)


def get_sale_balance(session: Session, sale: Sale) -> Tuple[float, float]:
    paid = get_sale_paid_amount(session, sale.id)
    balance = round(float(sale.total_amount) - float(paid), 2)
    return round(paid, 2), balance


def calc_status(paid: float, balance: float) -> str:
    if paid <= 0:
        return "unpaid"
    if balance <= 0.000001:
        return "paid"
    return "partial"


def create_payment(session: Session, sale_id: int, amount: float, method: str, paid_at: Optional[str], note: Optional[str]):
    sale = session.get(Sale, sale_id)
    if not sale:
        raise ValueError("sale_not_found")

    if method not in _ALLOWED_METHODS:
        raise ValueError("invalid_payment_method")

    paid, balance = get_sale_balance(session, sale)
    if amount > balance + 1e-6:
        raise ValueError("amount_exceeds_balance")

    payment = Payment(
        customer_id=sale.customer_id,
        sale_id=sale.id,
        amount=round(float(amount), 2),
        method=method,
        paid_at=_parse_iso_dt(paid_at),
        note=note,
    )
    session.add(payment)
    session.commit()
    session.refresh(payment)
    return payment


def list_payments(session: Session, customer_id: Optional[int], sale_id: Optional[int], page: int, page_size: int):
    conds = []
    if customer_id is not None:
        conds.append(Payment.customer_id == customer_id)
    if sale_id is not None:
        conds.append(Payment.sale_id == sale_id)

    total_stmt = select(func.count()).select_from(Payment)
    for c in conds:
        total_stmt = total_stmt.where(c)
    total = session.exec(total_stmt).one()

    stmt = select(Payment)
    for c in conds:
        stmt = stmt.where(c)

    stmt = (
        stmt.order_by(Payment.paid_at.desc(), Payment.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = session.exec(stmt).all()
    return items, int(total)


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
    customer = session.get(Customer, customer_id)
    if not customer:
        raise ValueError("customer_not_found")

    if method not in _ALLOWED_METHODS:
        raise ValueError("invalid_payment_method")

    sales = session.exec(select(Sale).where(Sale.customer_id == customer_id, Sale.id.in_(sale_ids))).all()
    if not sales:
        raise ValueError("no_sales_found")

    sale_rows = []
    for s in sales:
        paid, bal = get_sale_balance(session, s)
        if bal > 0.000001:
            sale_rows.append((s, paid, bal))

    if not sale_rows:
        raise ValueError("all_sales_already_paid")

    sale_rows.sort(key=lambda x: (x[0].sale_date, x[0].id))  # FIFO

    total_balance = sum(b for _, _, b in sale_rows)
    if total_amount > total_balance + 1e-6:
        raise ValueError("amount_exceeds_total_balance")

    remaining = round(float(total_amount), 2)
    paid_at_dt = _parse_iso_dt(paid_at)

    allocations = []
    created = 0

    for s, paid, bal in sale_rows:
        if remaining <= 0:
            break
        apply_amt = min(bal, remaining)
        apply_amt = round(float(apply_amt), 2)
        if apply_amt <= 0:
            continue

        p = Payment(
            customer_id=customer_id,
            sale_id=s.id,
            amount=apply_amt,
            method=method,
            paid_at=paid_at_dt,
            note=note,
        )
        session.add(p)
        session.flush()
        created += 1

        after_paid = round(paid + apply_amt, 2)
        after_balance = round(float(s.total_amount) - after_paid, 2)
        after_status = calc_status(after_paid, after_balance)

        allocations.append(
            {
                "sale_id": s.id,
                "applied_amount": apply_amt,
                "after_paid_amount": after_paid,
                "after_balance": after_balance,
                "after_status": after_status,
            }
        )

        remaining = round(remaining - apply_amt, 2)

    session.commit()
    return created, allocations
