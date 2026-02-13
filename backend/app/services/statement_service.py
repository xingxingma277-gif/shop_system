from datetime import datetime
from io import StringIO
from typing import Optional, Tuple, List
import csv

from sqlalchemy import func, or_
from sqlmodel import Session, select

from app.models import CustomerContact, Payment, Sale


def _parse_iso(dt_str: Optional[str]) -> Optional[datetime]:
    if not dt_str:
        return None
    if len(dt_str) == 10:
        dt_str = f"{dt_str}T00:00:00"
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


def _base_stmt(customer_id: int):
    return select(Sale, CustomerContact).outerjoin(CustomerContact, CustomerContact.id == Sale.buyer_id).where(Sale.customer_id == customer_id)


def get_statement(
    session: Session,
    *,
    customer_id: int,
    start_date: Optional[str],
    end_date: Optional[str],
    page: int,
    page_size: int,
    q: Optional[str] = None,
    payment_status: Optional[str] = None,
    sort_by: str = "date_desc",
) -> Tuple[dict, List[dict], int]:
    start_dt = _parse_iso(start_date)
    end_dt = _parse_iso(end_date)

    stmt = _base_stmt(customer_id)
    if start_dt:
        stmt = stmt.where(Sale.sale_date >= start_dt)
    if end_dt:
        stmt = stmt.where(Sale.sale_date <= end_dt)
    if payment_status in {"paid", "partial", "unpaid"}:
        stmt = stmt.where(Sale.payment_status == payment_status)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                Sale.sale_no.ilike(like),
                Sale.project.ilike(like),
                Sale.contact_name_snapshot.ilike(like),
            )
        )

    total = int(session.exec(select(func.count()).select_from(stmt.subquery())).one() or 0)

    if sort_by == "ar_desc":
        stmt = stmt.order_by(Sale.ar_amount.desc(), Sale.sale_date.desc(), Sale.id.desc())
    elif sort_by == "date_asc":
        stmt = stmt.order_by(Sale.sale_date.asc(), Sale.id.asc())
    else:
        stmt = stmt.order_by(Sale.sale_date.desc(), Sale.id.desc())

    rows = session.exec(stmt.offset((page - 1) * page_size).limit(page_size)).all()

    items = []
    for sale, buyer in rows:
        buyer_name = buyer.name if buyer else sale.contact_name_snapshot
        items.append(
            {
                "id": sale.id,
                "sale_id": sale.id,
                "sale_no": sale.sale_no,
                "date": sale.sale_date.isoformat(),
                "sale_date": sale.sale_date.isoformat(),
                "project": sale.project,
                "project_name": sale.project,
                "buyer_name": buyer_name,
                "contact_name_snapshot": buyer_name,
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


def export_statement_csv(session: Session, *, customer_id: int, start_date: Optional[str], end_date: Optional[str], q: Optional[str], payment_status: Optional[str], sort_by: str):
    _, items, _ = get_statement(
        session,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
        page=1,
        page_size=5000,
        q=q,
        payment_status=payment_status,
        sort_by=sort_by,
    )
    sio = StringIO()
    writer = csv.writer(sio)
    writer.writerow(["单号", "日期", "项目", "拿货人", "总额", "已付", "未付", "状态", "备注"])
    for it in items:
        writer.writerow([it["sale_no"], it["date"], it["project"], it["buyer_name"], it["total"], it["paid"], it["ar"], it["status"], it.get("note") or ""])
    return sio.getvalue()
