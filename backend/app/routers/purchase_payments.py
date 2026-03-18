from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.errors import BadRequestError, NotFoundError
from app.db.session import get_session
from app.schemas.purchase_payment import APAllocationCreate, PurchaseOpenAPRead, SupplierPaymentCreate, SupplierPaymentRead
from app.services import auth_service, purchase_payment_service

router = APIRouter(prefix='/api/purchase-payments', tags=['PurchasePayments'])


@router.post('', response_model=SupplierPaymentRead)
def create_supplier_payment(payload: SupplierPaymentCreate, _: dict | None = Depends(auth_service.require_permissions('ap.manage')), session: Session = Depends(get_session)):
    try:
        return purchase_payment_service.create_supplier_payment(session, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.post('/{payment_id}/allocate')
def allocate_payment(payment_id: int, payload: APAllocationCreate, _: dict | None = Depends(auth_service.require_permissions('ap.manage')), session: Session = Depends(get_session)):
    try:
        return purchase_payment_service.allocate_payment(session, payment_id, payload)
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
