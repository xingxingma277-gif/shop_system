from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.pagination import Page
from app.schemas.customer_contact import CustomerContactCreate, CustomerContactUpdate, CustomerContactRead
from app.services import customer_contact_service

router = APIRouter(prefix="/api", tags=["Contacts"])


@router.get("/customers/{customer_id}/contacts", response_model=Page[CustomerContactRead])
def list_contacts(customer_id: int, page: int = 1, page_size: int = 20, session: Session = Depends(get_session)):
    try:
        items, total = customer_contact_service.list_contacts(session, customer_id, page, page_size)
        return {"items": items, "total": total, "page": page, "page_size": page_size}
    except ValueError as e:
        if str(e) == "customer_not_found":
            raise HTTPException(status_code=404, detail="客户不存在")
        raise


@router.post("/customers/{customer_id}/contacts", response_model=CustomerContactRead)
def create_contact(customer_id: int, payload: CustomerContactCreate, session: Session = Depends(get_session)):
    try:
        c = customer_contact_service.create_contact(
            session,
            customer_id,
            name=payload.name,
            phone=payload.phone,
            role=payload.role,
            note=payload.note,
        )
        return c
    except ValueError as e:
        if str(e) == "customer_not_found":
            raise HTTPException(status_code=404, detail="客户不存在")
        raise


@router.patch("/contacts/{contact_id}", response_model=CustomerContactRead)
def update_contact(contact_id: int, payload: CustomerContactUpdate, session: Session = Depends(get_session)):
    try:
        c = customer_contact_service.update_contact(
            session,
            contact_id,
            name=payload.name,
            phone=payload.phone,
            role=payload.role,
            note=payload.note,
            is_active=payload.is_active,
        )
        return c
    except ValueError as e:
        if str(e) == "contact_not_found":
            raise HTTPException(status_code=404, detail="联系人不存在")
        raise


@router.post("/contacts/{contact_id}/toggle_active", response_model=CustomerContactRead)
def toggle_contact(contact_id: int, session: Session = Depends(get_session)):
    try:
        c = customer_contact_service.toggle_contact_active(session, contact_id)
        return c
    except ValueError as e:
        if str(e) == "contact_not_found":
            raise HTTPException(status_code=404, detail="联系人不存在")
        raise
