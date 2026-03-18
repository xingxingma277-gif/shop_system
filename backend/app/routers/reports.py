from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlmodel import Session

from app.db.session import get_session
from app.services import auth_service, report_service

router = APIRouter(prefix='/api/reports', tags=['Reports'])


@router.get('/ap-summary')
def ap_summary(
        supplier_id: int | None = Query(None),
        start_date: datetime | None = Query(None),
        end_date: datetime | None = Query(None),
        _: dict | None = Depends(auth_service.require_permissions('report.view')),
        session: Session = Depends(get_session),
):
    return report_service.ap_summary(session, supplier_id, start_date, end_date)


@router.get('/ap-aging')
def ap_aging(
        supplier_id: int | None = Query(None),
        as_of: datetime | None = Query(None),
        _: dict | None = Depends(auth_service.require_permissions('report.view')),
        session: Session = Depends(get_session),
):
    return report_service.ap_aging(session, supplier_id, as_of)


@router.get('/inventory-summary')
def inventory_summary(
        warehouse_id: int | None = Query(None),
        product_id: int | None = Query(None),
        start_date: datetime | None = Query(None),
        end_date: datetime | None = Query(None),
        _: dict | None = Depends(auth_service.require_permissions('report.view')),
        session: Session = Depends(get_session),
):
    return report_service.inventory_summary(session, warehouse_id, product_id, start_date, end_date)
