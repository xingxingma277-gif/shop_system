from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.core.errors import BadRequestError, NotFoundError
from app.db.session import get_session
from app.schemas.inventory_check import InventoryCheckCreate, InventoryCheckRead
from app.schemas.inventory_transfer import InventoryTransferCreate, InventoryTransferRead
from app.services import inventory_check_service, inventory_transfer_service, purchase_service

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


@router.get('/checks', response_model=list[InventoryCheckRead])
def list_checks(
        warehouse_id: int | None = Query(None),
        product_id: int | None = Query(None),
        status: str | None = Query(None),
        start_date: datetime | None = Query(None),
        end_date: datetime | None = Query(None),
        session: Session = Depends(get_session),
):
    return inventory_check_service.list_checks(session, warehouse_id, product_id, status, start_date, end_date)


@router.post('/checks', response_model=InventoryCheckRead)
def create_check(payload: InventoryCheckCreate, session: Session = Depends(get_session)):
    try:
        return inventory_check_service.create_check(session, payload)
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.post('/checks/{check_id}/post', response_model=InventoryCheckRead)
def post_check(check_id: int, session: Session = Depends(get_session)):
    try:
        return inventory_check_service.post_check(session, check_id)
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.get('/transfers', response_model=list[InventoryTransferRead])
def list_transfers(
        warehouse_id: int | None = Query(None),
        product_id: int | None = Query(None),
        status: str | None = Query(None),
        start_date: datetime | None = Query(None),
        end_date: datetime | None = Query(None),
        session: Session = Depends(get_session),
):
    return inventory_transfer_service.list_transfers(session, warehouse_id, product_id, status, start_date, end_date)


@router.post('/transfers', response_model=InventoryTransferRead)
def create_transfer(payload: InventoryTransferCreate, session: Session = Depends(get_session)):
    try:
        return inventory_transfer_service.create_transfer(session, payload)
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.post('/transfers/{transfer_id}/post', response_model=InventoryTransferRead)
def post_transfer(transfer_id: int, session: Session = Depends(get_session)):
    try:
        return inventory_transfer_service.post_transfer(session, transfer_id)
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)
