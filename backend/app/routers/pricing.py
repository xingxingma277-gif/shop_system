from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.pricing import PricingHistoryResponse, PricingLastResponse, ProductTrendItem
from app.services import pricing_service

router = APIRouter(prefix="/api/pricing", tags=["Pricing/History"])


@router.get("/last-price", response_model=PricingLastResponse)
def get_last_price(
    customer_id: int = Query(..., ge=1),
    product_id: int = Query(..., ge=1),
    session: Session = Depends(get_session),
):
    return pricing_service.last_pricing(session, customer_id, product_id)


@router.get("/history", response_model=PricingHistoryResponse)
def get_history(
    customer_id: int = Query(..., ge=1),
    product_id: int = Query(..., ge=1),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    session: Session = Depends(get_session),
):
    return pricing_service.pricing_history(
        session,
        customer_id,
        product_id,
        page=page,
        page_size=page_size,
        start_date=start_date,
        end_date=end_date,
    )


@router.get("/product_trend", response_model=list[ProductTrendItem])
def get_product_trend(
    product_id: int = Query(..., ge=1),
    limit: int = Query(50, ge=1, le=200),
    session: Session = Depends(get_session),
):
    return pricing_service.product_trend(session, product_id, limit=limit)
