from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db.session import get_session
from app.services import purchase_service

router = APIRouter(prefix='/api/inventory', tags=['Inventory'])


@router.get('/ledger')
def inventory_ledger(
        warehouse_id: int | None = Query(None),
        product_id: int | None = Query(None),
        biz_type: str | None = Query(None),
        start_date: datetime | None = Query(None),
        end_date: datetime | None = Query(None),
        session: Session = Depends(get_session),
):
    return {'items': purchase_service.list_inventory_ledger(session, warehouse_id, product_id, biz_type, start_date, end_date)}
