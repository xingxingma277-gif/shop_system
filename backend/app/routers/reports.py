from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db.session import get_session
from app.services import report_service

router = APIRouter(prefix='/api/reports', tags=['Reports'])


@router.get('/ap-summary')
def ap_summary(
        supplier_id: int | None = Query(None),
        start_date: datetime | None = Query(None),
        end_date: datetime | None = Query(None),
        session: Session = Depends(get_session),
):
    return report_service.ap_summary(session, supplier_id, start_date, end_date)


@router.get('/inventory-summary')
def inventory_summary(
        warehouse_id: int | None = Query(None),
        product_id: int | None = Query(None),
        start_date: datetime | None = Query(None),
        end_date: datetime | None = Query(None),
        session: Session = Depends(get_session),
):
    return report_service.inventory_summary(session, warehouse_id, product_id, start_date, end_date)
