from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session, select

from app.models import Customer, Payment, Sale


def _parse_iso(v: Optional[str], *, end_of_day: bool = False):
    if not v:
        return None
    if len(v) == 10:
        dt = datetime.fromisoformat(f"{v}T00:00:00+00:00")
        return dt + timedelta(days=1) - timedelta(microseconds=1) if end_of_day else dt
    return datetime.fromisoformat(v.replace("Z", "+00:00"))


def _to_iso_z(dt: datetime) -> str:
    return dt.isoformat().replace("+00:00", "Z")


def list_transactions(session: Session, *, page: int, page_size: int, start_date: Optional[str], end_date: Optional[str], q: Optional[str], tx_type: Optional[str]):
    start_dt = _parse_iso(start_date)
    end_dt = _parse_iso(end_date, end_of_day=True)
    qv = (q or "").strip().lower()

    items = []

    if tx_type in (None, "sale"):
        sale_stmt = select(Sale, Customer).join(Customer, Customer.id == Sale.customer_id)
        if start_dt:
            sale_stmt = sale_stmt.where(Sale.sale_date >= start_dt)
        if end_dt:
            sale_stmt = sale_stmt.where(Sale.sale_date <= end_dt)
        for s, c in session.exec(sale_stmt).all():
            row = {
                "type": "sale",
                "occurred_at": _to_iso_z(s.sale_date),
                "customer_id": c.id,
                "customer_name": c.name,
                "sale_id": s.id,
                "sale_no": s.sale_no,
                "amount": s.total_amount,
                "paid": s.paid_amount,
                "balance": s.ar_amount,
                "status": s.payment_status,
                "note": s.note,
            }
            if qv and not any(qv in str((row.get(k) or "")).lower() for k in ["customer_name", "sale_no", "note"]):
                continue
            items.append(row)

    if tx_type in (None, "payment"):
        pay_stmt = select(Payment, Customer, Sale).join(Customer, Customer.id == Payment.customer_id).outerjoin(Sale, Sale.id == Payment.sale_id)
        if start_dt:
            pay_stmt = pay_stmt.where(Payment.paid_at >= start_dt)
        if end_dt:
            pay_stmt = pay_stmt.where(Payment.paid_at <= end_dt)
        for p, c, s in session.exec(pay_stmt).all():
            row = {
                "type": "payment",
                "occurred_at": _to_iso_z(p.paid_at),
                "customer_id": c.id,
                "customer_name": c.name,
                "payment_id": p.id,
                "sale_id": p.sale_id,
                "sale_no": s.sale_no if s else None,
                "amount": p.amount,
                "method": p.method,
                "status": "posted",
                "note": p.note,
            }
            if qv and not any(qv in str((row.get(k) or "")).lower() for k in ["customer_name", "sale_no", "note"]):
                continue
            items.append(row)

    items.sort(key=lambda x: x["occurred_at"], reverse=True)
    total = len(items)
    paged = items[(page - 1) * page_size : page * page_size]
    return paged, total
