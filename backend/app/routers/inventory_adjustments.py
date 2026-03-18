from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.core.errors import BadRequestError, NotFoundError
from app.db.session import get_session
from app.schemas.inventory_adjustment import InventoryAdjustmentCreate, InventoryAdjustmentRead
from app.services import inventory_adjustment_service

router = APIRouter(prefix='/api/inventory/adjustments', tags=['InventoryAdjustments'])


@router.get('', response_model=list[InventoryAdjustmentRead])
def list_adjustments(
        warehouse_id: int | None = Query(None),
        product_id: int | None = Query(None),
        adj_type: str | None = Query(None),
        start_date: datetime | None = Query(None),
        end_date: datetime | None = Query(None),
        session: Session = Depends(get_session),
):
    return inventory_adjustment_service.list_adjustments(session, warehouse_id, product_id, adj_type, start_date, end_date)


@router.post('', response_model=InventoryAdjustmentRead)
def create_adjustment(payload: InventoryAdjustmentCreate, session: Session = Depends(get_session)):
    try:
        return inventory_adjustment_service.create_adjustment(session, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=exc.message)
