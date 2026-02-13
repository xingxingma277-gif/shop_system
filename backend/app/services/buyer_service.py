from sqlalchemy import func
from sqlmodel import Session, select

from app.core.errors import NotFoundError
from app.models import Customer, CustomerContact, Payment, Sale


def list_buyers(session: Session, customer_id: int):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise NotFoundError("客户不存在")
    stmt = (
        select(CustomerContact)
        .where(CustomerContact.customer_id == customer_id)
        .order_by(CustomerContact.is_active.desc(), CustomerContact.id.desc())
    )
    return session.exec(stmt).all()


def create_buyer(session: Session, customer_id: int, name: str, phone: str | None = None, note: str | None = None):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise NotFoundError("客户不存在")
    buyer = CustomerContact(customer_id=customer_id, name=name.strip(), phone=phone, note=note, role="拿货人", is_active=True)
    session.add(buyer)
    session.commit()
    session.refresh(buyer)
    return buyer


def ensure_default_personal_buyer(session: Session, customer: Customer) -> CustomerContact:
    exists = session.exec(
        select(CustomerContact).where(CustomerContact.customer_id == customer.id, CustomerContact.name == customer.name)
    ).first()
    if exists:
        return exists
    buyer = CustomerContact(
        customer_id=customer.id,
        name=customer.name,
        phone=customer.phone,
        role="本人",
        note="个人客户默认拿货人",
        is_active=True,
    )
    session.add(buyer)
    session.commit()
    session.refresh(buyer)
    return buyer


def buyer_statement(
    session: Session,
    buyer_id: int,
    start_date=None,
    end_date=None,
    page: int = 1,
    page_size: int = 20,
):
    buyer = session.get(CustomerContact, buyer_id)
    if not buyer:
        raise NotFoundError("拿货人不存在")

    stmt = select(Sale).where(Sale.buyer_id == buyer_id)
    if start_date:
        stmt = stmt.where(Sale.sale_date >= start_date)
    if end_date:
        stmt = stmt.where(Sale.sale_date <= end_date)

    total = int(session.exec(select(func.count()).select_from(stmt.subquery())).one() or 0)
    rows = session.exec(
        stmt.order_by(Sale.sale_date.desc(), Sale.id.desc()).offset((page - 1) * page_size).limit(page_size)
    ).all()

    items = [
        {
            "date": s.sale_date.isoformat().replace("+00:00", "Z"),
            "sale_id": s.id,
            "project": s.project,
            "buyer_name": buyer.name,
            "total": float(s.total_amount),
            "paid": float(s.paid_amount),
            "ar": float(s.ar_amount),
            "status": s.payment_status,
            "note": s.note,
        }
        for s in rows
    ]
    return buyer, items, total
