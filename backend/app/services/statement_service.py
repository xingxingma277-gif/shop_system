from datetime import datetime
from typing import Optional, Tuple, List

from sqlalchemy import func
from sqlmodel import Session, select

from app.models import Sale, Payment
from app.services.payment_service import calc_status


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

    # total count
    count_stmt = select(func.count()).select_from(Sale).where(Sale.customer_id == customer_id)
    if start_dt:
        count_stmt = count_stmt.where(Sale.sale_date >= start_dt)
    if end_dt:
        count_stmt = count_stmt.where(Sale.sale_date <= end_dt)
    total = int(session.exec(count_stmt).one())

    # list with paid sum
    paid_sum = func.coalesce(func.sum(Payment.amount), 0).label("paid_amount")
    stmt = (
        select(Sale, paid_sum)
        .outerjoin(Payment, Payment.sale_id == Sale.id)
        .where(Sale.customer_id == customer_id)
    )
    if start_dt:
        stmt = stmt.where(Sale.sale_date >= start_dt)
    if end_dt:
        stmt = stmt.where(Sale.sale_date <= end_dt)

    stmt = (
        stmt.group_by(Sale.id)
        .order_by(Sale.sale_date.desc(), Sale.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    rows = session.exec(stmt).all()

    items = []
    for sale, paid_amount in rows:
        paid_amount = round(float(paid_amount or 0), 2)
        balance = round(float(sale.total_amount) - paid_amount, 2)
        items.append(
            {
                "id": sale.id,
                "sale_date": sale.sale_date.isoformat(),
                "note": sale.note,
                "total_amount": round(float(sale.total_amount), 2),
                "paid_amount": paid_amount,
                "balance": balance,
                "payment_status": calc_status(paid_amount, balance),
                "contact_name_snapshot": sale.contact_name_snapshot,
                "project_name": sale.project_name,
            }
        )

    # summary
    total_sales_stmt = select(func.coalesce(func.sum(Sale.total_amount), 0)).where(Sale.customer_id == customer_id)
    if start_dt:
        total_sales_stmt = total_sales_stmt.where(Sale.sale_date >= start_dt)
    if end_dt:
        total_sales_stmt = total_sales_stmt.where(Sale.sale_date <= end_dt)
    total_sales = float(session.exec(total_sales_stmt).one() or 0)

    total_paid_stmt = (
        select(func.coalesce(func.sum(Payment.amount), 0))
        .select_from(Payment)
        .join(Sale, Sale.id == Payment.sale_id)
        .where(Sale.customer_id == customer_id)
    )
    if start_dt:
        total_paid_stmt = total_paid_stmt.where(Sale.sale_date >= start_dt)
    if end_dt:
        total_paid_stmt = total_paid_stmt.where(Sale.sale_date <= end_dt)
    total_paid = float(session.exec(total_paid_stmt).one() or 0)

    summary = {
        "total_sales_amount": round(total_sales, 2),
        "total_paid_amount": round(total_paid, 2),
        "total_balance": round(total_sales - total_paid, 2),
    }

    return summary, items, total
