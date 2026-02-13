from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import or_
from sqlmodel import Session, select

from app.models import Customer, Payment, PaymentAllocation, Product, Sale, SaleItem


def _parse_iso(v: Optional[str], *, end_of_day: bool = False):
    if not v:
        return None
    if len(v) == 10:
        dt = datetime.fromisoformat(f"{v}T00:00:00+00:00")
        return dt + timedelta(days=1) - timedelta(microseconds=1) if end_of_day else dt
    return datetime.fromisoformat(v.replace("Z", "+00:00"))


def _to_iso_z(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def list_sales_transactions(
    session: Session,
    *,
    page: int,
    page_size: int,
    start_date: Optional[str],
    end_date: Optional[str],
    q: Optional[str],
    status: Optional[str],
):
    start_dt = _parse_iso(start_date)
    end_dt = _parse_iso(end_date, end_of_day=True)

    stmt = select(Sale, Customer).join(Customer, Customer.id == Sale.customer_id)
    if start_dt:
        stmt = stmt.where(Sale.sale_date >= start_dt)
    if end_dt:
        stmt = stmt.where(Sale.sale_date <= end_dt)
    if status in {"unpaid", "partial", "paid"}:
        stmt = stmt.where(Sale.payment_status == status)
    if q and q.strip():
        like = f"%{q.strip()}%"
        stmt = stmt.outerjoin(SaleItem, SaleItem.sale_id == Sale.id).outerjoin(Product, Product.id == SaleItem.product_id).where(
            or_(
                Sale.sale_no.ilike(like),
                Customer.name.ilike(like),
                Product.name.ilike(like),
            )
        )

    rows_all = session.exec(stmt.order_by(Sale.sale_date.desc(), Sale.id.desc())).all()
    total = len(rows_all)
    rows = rows_all[(page - 1) * page_size : page * page_size]
    items = [
        {
            "occurred_at": _to_iso_z(s.sale_date),
            "sale_id": s.id,
            "sale_no": s.sale_no,
            "customer_id": c.id,
            "customer_name": c.name,
            "total_amount": s.total_amount,
            "paid_amount": s.paid_amount,
            "balance": s.ar_amount,
            "status": s.payment_status,
        }
        for s, c in rows
    ]
    return items, total


def list_payment_transactions(
    session: Session,
    *,
    page: int,
    page_size: int,
    start_date: Optional[str],
    end_date: Optional[str],
    q: Optional[str],
    method: Optional[str],
):
    start_dt = _parse_iso(start_date)
    end_dt = _parse_iso(end_date, end_of_day=True)

    stmt = select(Payment, Customer).join(Customer, Customer.id == Payment.customer_id)
    if start_dt:
        stmt = stmt.where(Payment.paid_at >= start_dt)
    if end_dt:
        stmt = stmt.where(Payment.paid_at <= end_dt)
    if method:
        stmt = stmt.where(Payment.method == method)

    rows_all = session.exec(stmt.order_by(Payment.paid_at.desc(), Payment.id.desc())).all()
    raw = []
    qv = (q or "").strip().lower()
    for p, c in rows_all:
        sale_nos = []
        if p.sale_id:
            sale = session.get(Sale, p.sale_id)
            if sale:
                sale_nos.append(sale.sale_no)
        alloc_sales = session.exec(
            select(Sale)
            .join(PaymentAllocation, PaymentAllocation.sale_id == Sale.id)
            .where(PaymentAllocation.payment_id == p.id)
            .order_by(Sale.sale_date.asc(), Sale.id.asc())
        ).all()
        for s in alloc_sales:
            if s.sale_no not in sale_nos:
                sale_nos.append(s.sale_no)

        row = {
            "occurred_at": _to_iso_z(p.paid_at),
            "payment_id": p.id,
            "customer_id": c.id,
            "customer_name": c.name,
            "method": p.method,
            "amount": p.amount,
            "sale_nos": sale_nos,
            "note": p.note,
        }
        if qv:
            hay = f"{row['customer_name']} {' '.join(row['sale_nos'])} {row.get('note') or ''}".lower()
            if qv not in hay:
                continue
        raw.append(row)

    total = len(raw)
    items = raw[(page - 1) * page_size : page * page_size]
    return items, total
