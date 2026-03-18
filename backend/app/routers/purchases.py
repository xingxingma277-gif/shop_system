from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.core.errors import BadRequestError, NotFoundError
from app.db.session import get_session
from app.schemas.purchase import PurchaseCreate, PurchasePage, PurchaseRead, PurchaseReceivePayload, PurchaseReturnPayload
from app.services import audit_log_service, auth_service, purchase_service

router = APIRouter(prefix='/api/purchases', tags=['Purchases'])


@router.get('', response_model=PurchasePage)
def list_purchases(
        supplier_id: int | None = Query(None),
        status: str | None = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(20, ge=1, le=100),
        _: dict | None = Depends(auth_service.require_permissions('purchase.view')),
        session: Session = Depends(get_session),
):
    data = purchase_service.list_purchases(session, supplier_id=supplier_id, status=status, page=page, page_size=page_size)
    meta = data['meta']
    return PurchasePage(items=data['items'], total=meta['total'], page=meta['page'], page_size=meta['page_size'])


@router.post('', response_model=PurchaseRead)
def create_purchase(payload: PurchaseCreate, current: dict | None = Depends(auth_service.require_permissions('purchase.manage')), session: Session = Depends(get_session)):
    try:
        purchase = purchase_service.create_purchase(session, payload)
        if current:
            audit_log_service.record(session, action='CREATE', resource_type='purchase', resource_id=purchase.id, detail=f'创建采购单 {purchase.purchase_no}', actor_user_id=current['id'], actor_name=current['display_name'])
            session.commit()
        return purchase
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.get('/{purchase_id}', response_model=PurchaseRead)
def get_purchase(purchase_id: int, _: dict | None = Depends(auth_service.require_permissions('purchase.view')), session: Session = Depends(get_session)):
    try:
        return purchase_service.get_purchase(session, purchase_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)


@router.post('/{purchase_id}/confirm', response_model=PurchaseRead)
def confirm_purchase(purchase_id: int, current: dict | None = Depends(auth_service.require_permissions('purchase.manage')), session: Session = Depends(get_session)):
    try:
        purchase = purchase_service.confirm_purchase(session, purchase_id)
        if current:
            audit_log_service.record(session, action='CONFIRM', resource_type='purchase', resource_id=purchase.id, detail=f'确认采购单 {purchase.purchase_no}', actor_user_id=current['id'], actor_name=current['display_name'])
            session.commit()
        return purchase
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.post('/{purchase_id}/receive', response_model=PurchaseRead)
def receive_purchase(purchase_id: int, payload: PurchaseReceivePayload, current: dict | None = Depends(auth_service.require_permissions('purchase.manage', 'inventory.manage')), session: Session = Depends(get_session)):
    try:
        purchase = purchase_service.receive_purchase(session, purchase_id, payload)
        if current:
            audit_log_service.record(session, action='RECEIVE', resource_type='purchase', resource_id=purchase.id, detail=f'采购入库 {purchase.purchase_no}', actor_user_id=current['id'], actor_name=current['display_name'])
            session.commit()
        return purchase
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.post('/{purchase_id}/return', response_model=PurchaseRead)
def return_purchase(purchase_id: int, payload: PurchaseReturnPayload, current: dict | None = Depends(auth_service.require_permissions('purchase.manage', 'inventory.manage')), session: Session = Depends(get_session)):
    try:
        purchase = purchase_service.return_purchase(session, purchase_id, payload)
        if current:
            audit_log_service.record(session, action='RETURN', resource_type='purchase', resource_id=purchase.id, detail=f'采购退货 {purchase.purchase_no}', actor_user_id=current['id'], actor_name=current['display_name'])
            session.commit()
        return purchase
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)
