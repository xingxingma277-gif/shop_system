from datetime import datetime
from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.core.errors import NotFoundError
from app.db.session import get_session
from app.services import buyer_service

router = APIRouter(prefix="/api/buyers", tags=["Buyers"])


def _parse(v: str | None):
    if not v:
        return None
    return datetime.fromisoformat(v.replace("Z", "+00:00"))


@router.get("/{buyer_id}/statement")
def buyer_statement(
    buyer_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: str | None = None,
    end_date: str | None = None,
    session: Session = Depends(get_session),
):
    try:
        _, items, total = buyer_service.buyer_statement(
            session,
            buyer_id=buyer_id,
            start_date=_parse(start_date),
            end_date=_parse(end_date),
            page=page,
            page_size=page_size,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)

    pages = ceil(total / page_size) if page_size else 0
    return {"items": items, "meta": {"total": total, "page": page, "page_size": page_size, "pages": pages}}
