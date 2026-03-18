from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.core.errors import BadRequestError, NotFoundError
from app.db.session import get_session
from app.schemas.supplier import SupplierCreate, SupplierRead, SupplierUpdate
from app.services import audit_log_service, auth_service, supplier_service

router = APIRouter(prefix='/api/suppliers', tags=['Suppliers'])


@router.get('', response_model=list[SupplierRead])
def list_suppliers(q: str | None = Query(None), status: str | None = Query(None), _: dict | None = Depends(auth_service.require_permissions('supplier.manage')), session: Session = Depends(get_session)):
    return supplier_service.list_suppliers(session, q=q, status=status)


@router.post('', response_model=SupplierRead)
def create_supplier(payload: SupplierCreate, current: dict | None = Depends(auth_service.require_permissions('supplier.manage')), session: Session = Depends(get_session)):
    try:
        supplier = supplier_service.create_supplier(session, payload)
        if current:
            audit_log_service.record(session, action='CREATE', resource_type='supplier', resource_id=supplier.id, detail=f'创建供应商 {supplier.name}', actor_user_id=current['id'], actor_name=current['display_name'])
            session.commit()
        return supplier
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.put('/{supplier_id}', response_model=SupplierRead)
def update_supplier(supplier_id: int, payload: SupplierUpdate, current: dict | None = Depends(auth_service.require_permissions('supplier.manage')), session: Session = Depends(get_session)):
    try:
        supplier = supplier_service.update_supplier(session, supplier_id, payload)
        if current:
            audit_log_service.record(session, action='UPDATE', resource_type='supplier', resource_id=supplier.id, detail=f'更新供应商 {supplier.name}', actor_user_id=current['id'], actor_name=current['display_name'])
            session.commit()
        return supplier
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=exc.message)
