from typing import Optional
from sqlalchemy import func
from sqlmodel import Session, select

from app.models import Customer, CustomerContact


def get_customer_or_404(session: Session, customer_id: int) -> Customer:
    customer = session.get(Customer, customer_id)
    if not customer:
        raise ValueError("customer_not_found")
    return customer


def list_contacts(session: Session, customer_id: int, page: int, page_size: int):
    get_customer_or_404(session, customer_id)

    total = session.exec(
        select(func.count()).select_from(CustomerContact).where(CustomerContact.customer_id == customer_id)
    ).one()

    stmt = (
        select(CustomerContact)
        .where(CustomerContact.customer_id == customer_id)
        .order_by(CustomerContact.is_active.desc(), CustomerContact.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = session.exec(stmt).all()
    return items, int(total)


def create_contact(session: Session, customer_id: int, *, name: str, phone: Optional[str], role: str, note: Optional[str]):
    get_customer_or_404(session, customer_id)

    contact = CustomerContact(customer_id=customer_id, name=name, phone=phone, role=role, note=note, is_active=True)
    session.add(contact)
    session.commit()
    session.refresh(contact)
    return contact


def update_contact(
    session: Session,
    contact_id: int,
    *,
    name: Optional[str] = None,
    phone: Optional[str] = None,
    role: Optional[str] = None,
    note: Optional[str] = None,
    is_active: Optional[bool] = None,
):
    contact = session.get(CustomerContact, contact_id)
    if not contact:
        raise ValueError("contact_not_found")

    if name is not None:
        contact.name = name
    if phone is not None:
        contact.phone = phone
    if role is not None:
        contact.role = role
    if note is not None:
        contact.note = note
    if is_active is not None:
        contact.is_active = is_active

    session.add(contact)
    session.commit()
    session.refresh(contact)
    return contact


def toggle_contact_active(session: Session, contact_id: int):
    contact = session.get(CustomerContact, contact_id)
    if not contact:
        raise ValueError("contact_not_found")
    contact.is_active = not bool(contact.is_active)
    session.add(contact)
    session.commit()
    session.refresh(contact)
    return contact
