from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.errors import BadRequestError, NotFoundError
from app.db.session import get_session
from app.schemas.purchase_payment import APAllocationCreate, PurchaseOpenAPRead, SupplierPaymentCreate, SupplierPaymentRead
from app.services import audit_log_service, auth_service, purchase_payment_service

router = APIRouter(prefix='/api/purchase-payments', tags=['PurchasePayments'])


@router.post('', response_model=SupplierPaymentRead)
def create_supplier_payment(payload: SupplierPaymentCreate, current: dict | None = Depends(auth_service.require_permissions('ap.manage')), session: Session = Depends(get_session)):
    try:
        payment = purchase_payment_service.create_supplier_payment(session, payload)
        if current:
            audit_log_service.record(session, action='PAY', resource_type='supplier_payment', resource_id=payment.id, detail=f'创建供应商付款 {payment.receipt_no}', actor_user_id=current['id'], actor_name=current['display_name'])
            session.commit()
        return payment
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.post('/{payment_id}/allocate')
def allocate_payment(payment_id: int, payload: APAllocationCreate, current: dict | None = Depends(auth_service.require_permissions('ap.manage')), session: Session = Depends(get_session)):
    try:
        result = purchase_payment_service.allocate_payment(session, payment_id, payload)
        if current:
            audit_log_service.record(session, action='ALLOCATE', resource_type='supplier_payment', resource_id=payment_id, detail=f'核销供应商付款 #{payment_id}', actor_user_id=current['id'], actor_name=current['display_name'])
            session.commit()
        return result
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.get('/supplier/{supplier_id}/open-purchases', response_model=list[PurchaseOpenAPRead])
def supplier_open_purchases(supplier_id: int, _: dict | None = Depends(auth_service.require_permissions('ap.manage')), session: Session = Depends(get_session)):
    try:
        rows = purchase_payment_service.list_supplier_open_purchases(session, supplier_id)
        return [
            {
                'purchase_id': p.id,
                'purchase_no': p.purchase_no,
                'purchase_date': p.purchase_date,
                'total_amount': p.total_amount,
                'paid_amount': p.paid_amount,
                'ap_amount': p.ap_amount,
            }
            for p in rows
        ]
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)


@router.get('/supplier/{supplier_id}/records')
def supplier_payment_records(supplier_id: int, _: dict | None = Depends(auth_service.require_permissions('ap.manage')), session: Session = Depends(get_session)):
    try:
        return {'items': purchase_payment_service.list_supplier_payments(session, supplier_id)}
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
