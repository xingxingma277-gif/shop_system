from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.sale import SaleCreate, SaleRead, SalePage
from app.services import sale_service

router = APIRouter(prefix="/api/sales", tags=["Sales"])


@router.post("", response_model=SaleRead)
def create_sale(
    payload: SaleCreate,
    session: Session = Depends(get_session),
):
    return sale_service.create_sale(session, payload)


@router.get("", response_model=SalePage)
def get_sales(
    customer_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    items, total, page, page_size = sale_service.list_sales(session, customer_id, page, page_size)
    return SalePage(items=items, total=total, page=page, page_size=page_size)


@router.get("/{sale_id}", response_model=SaleRead)
def get_sale_detail(
    sale_id: int,
    session: Session = Depends(get_session),
):
    return sale_service.get_sale(session, sale_id)
