from math import ceil

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db.session import get_session
from app.services import transaction_service

router = APIRouter(prefix="/api/transactions", tags=["Transactions"])


@router.get("")
def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    q: str | None = Query(None),
    type: str | None = Query(None),
    session: Session = Depends(get_session),
):
    items, total = transaction_service.list_transactions(
        session,
        page=page,
        page_size=page_size,
        start_date=start_date,
        end_date=end_date,
        q=q,
        tx_type=type,
    )
    return {"items": items, "meta": {"total": total, "page": page, "page_size": page_size, "pages": ceil(total / page_size)}}
