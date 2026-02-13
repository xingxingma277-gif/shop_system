from sqlalchemy import func
from sqlmodel import Session, col, select

from app.core.errors import NotFoundError
from app.models import Customer, Payment, Sale
from app.schemas.sale import SaleSummary
from app.services.pagination import paginate
from app.services.utils import to_update_dict


def list_customers(
    session: Session,
    page: int,
    page_size: int,
    q: str | None = None,
    active_only: bool = True,
):
    stmt = select(Customer)
    if active_only:
        stmt = stmt.where(Customer.is_active == True)  # noqa: E712
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(col(Customer.name).ilike(like))
    stmt = stmt.order_by(Customer.created_at.desc(), Customer.id.desc())
    return paginate(session, stmt, page, page_size)


def create_customer(session: Session, data) -> Customer:
    customer = Customer(
        name=data.name.strip(),
        phone=(data.phone.strip() if data.phone else None),
        address=(data.address.strip() if data.address else None),
        is_active=bool(data.is_active),
    )
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


def update_customer(session: Session, customer_id: int, data) -> Customer:
    customer = session.get(Customer, customer_id)
    if not customer:
        raise NotFoundError("客户不存在")

    updates = to_update_dict(data)
    if "name" in updates and updates["name"] is not None:
        updates["name"] = updates["name"].strip()

    for k, v in updates.items():
        setattr(customer, k, v)

    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


def delete_customer(session: Session, customer_id: int) -> None:
    customer = session.get(Customer, customer_id)
    if not customer:
        raise NotFoundError("客户不存在")

    sale_count = int(
        session.exec(select(func.count()).select_from(Sale).where(Sale.customer_id == customer_id)).one() or 0
    )
    payment_count = int(
        session.exec(select(func.count()).select_from(Payment).where(Payment.customer_id == customer_id)).one() or 0
    )

    if sale_count > 0 or payment_count > 0:
        raise ValueError("customer_has_related_records")

    session.delete(customer)
    session.commit()


def get_customer_or_404(session: Session, customer_id: int) -> Customer:
    customer = session.get(Customer, customer_id)
    if not customer:
        raise NotFoundError("客户不存在")
    return customer


def get_customer_profile(session: Session, customer_id: int, recent_limit: int = 10):
    customer = get_customer_or_404(session, customer_id)

    stmt = (
        select(Sale)
        .where(Sale.customer_id == customer_id)
        .order_by(Sale.sale_date.desc(), Sale.id.desc())
        .limit(recent_limit)
    )
    sales = session.exec(stmt).all()
    summaries = [
        SaleSummary(
            id=s.id,
            customer_id=s.customer_id,
            customer_name=customer.name,
            sale_date=s.sale_date,
            note=s.note,
            total_amount=s.total_amount,
        )
        for s in sales
    ]
    return customer, summaries


def get_ar_summary(session: Session, customer_id: int) -> dict:
    get_customer_or_404(session, customer_id)

    total_sales = float(
        session.exec(
            select(func.coalesce(func.sum(Sale.total_amount), 0)).where(Sale.customer_id == customer_id)
        ).one()
        or 0
    )

    total_received = float(
        session.exec(
            select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.customer_id == customer_id)
        ).one()
        or 0
    )

    return {
        "total_sales": round(total_sales, 2),
        "total_received": round(total_received, 2),
        "total_ar": round(total_sales - total_received, 2),
    }
