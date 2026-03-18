from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.core.errors import BadRequestError, NotFoundError
from app.db.session import get_session
from app.schemas.purchase import PurchaseCreate, PurchaseRead, PurchaseReceivePayload
from app.services import purchase_service

router = APIRouter(prefix='/api/purchases', tags=['Purchases'])


@router.get('', response_model=list[PurchaseRead])
def list_purchases(
        supplier_id: int | None = Query(None),
        status: str | None = Query(None),
        session: Session = Depends(get_session),
):
    return purchase_service.list_purchases(session, supplier_id=supplier_id, status=status)


@router.post('', response_model=PurchaseRead)
def create_purchase(payload: PurchaseCreate, session: Session = Depends(get_session)):
    try:
        return purchase_service.create_purchase(session, payload)
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.get('/{purchase_id}', response_model=PurchaseRead)
def get_purchase(purchase_id: int, session: Session = Depends(get_session)):
    try:
        return purchase_service.get_purchase(session, purchase_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)


@router.post('/{purchase_id}/confirm', response_model=PurchaseRead)
def confirm_purchase(purchase_id: int, session: Session = Depends(get_session)):
    try:
        return purchase_service.confirm_purchase(session, purchase_id)
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.post('/{purchase_id}/receive', response_model=PurchaseRead)
def receive_purchase(purchase_id: int, payload: PurchaseReceivePayload, session: Session = Depends(get_session)):
    try:
        return purchase_service.receive_purchase(session, purchase_id, payload)
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)
