from datetime import datetime
from typing import Optional, Tuple, List

from sqlalchemy import func
from sqlmodel import Session, select

from app.models import CustomerContact, Payment, Sale


def _parse_iso(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


def get_statement(
    session: Session,
    *,
    customer_id: int,
    start_date: Optional[str],
    end_date: Optional[str],
    page: int,
    page_size: int,
) -> Tuple[dict, List[dict], int]:
    start_dt = _parse_iso(start_date)
    end_dt = _parse_iso(end_date)

    count_stmt = select(func.count()).select_from(Sale).where(Sale.customer_id == customer_id)
    if start_dt:
        count_stmt = count_stmt.where(Sale.sale_date >= start_dt)
    if end_dt:
        count_stmt = count_stmt.where(Sale.sale_date <= end_dt)
    total = int(session.exec(count_stmt).one())

    stmt = select(Sale, CustomerContact).outerjoin(CustomerContact, CustomerContact.id == Sale.buyer_id).where(Sale.customer_id == customer_id)
    if start_dt:
        stmt = stmt.where(Sale.sale_date >= start_dt)
    if end_dt:
        stmt = stmt.where(Sale.sale_date <= end_dt)

    rows = session.exec(
        stmt.order_by(Sale.sale_date.desc(), Sale.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()

    items = []
    for sale, buyer in rows:
        items.append(
            {
                "id": sale.id,
                "date": sale.sale_date.isoformat(),
                "sale_date": sale.sale_date.isoformat(),
                "sale_no": f"S{sale.id}",
                "project": sale.project,
                "project_name": sale.project,
                "buyer_name": buyer.name if buyer else sale.contact_name_snapshot,
                "contact_name_snapshot": buyer.name if buyer else sale.contact_name_snapshot,
                "total": round(float(sale.total_amount), 2),
                "total_amount": round(float(sale.total_amount), 2),
                "paid": round(float(sale.paid_amount), 2),
                "paid_amount": round(float(sale.paid_amount), 2),
                "unpaid": round(float(sale.ar_amount), 2),
                "balance": round(float(sale.ar_amount), 2),
                "ar": round(float(sale.ar_amount), 2),
                "status": sale.payment_status,
                "payment_status": sale.payment_status,
                "note": sale.note,
            }
        )

    total_sales = float(session.exec(select(func.coalesce(func.sum(Sale.total_amount), 0)).where(Sale.customer_id == customer_id)).one() or 0)
    total_paid = float(session.exec(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.customer_id == customer_id)).one() or 0)

    summary = {
        "total_sales_amount": round(total_sales, 2),
        "total_paid_amount": round(total_paid, 2),
        "total_balance": round(total_sales - total_paid, 2),
    }

    return summary, items, total
