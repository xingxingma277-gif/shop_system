from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.core.errors import BadRequestError, NotFoundError
from app.db.session import get_session
from app.schemas.supplier import SupplierCreate, SupplierRead, SupplierUpdate
from app.services import supplier_service

router = APIRouter(prefix='/api/suppliers', tags=['Suppliers'])


@router.get('', response_model=list[SupplierRead])
def list_suppliers(q: str | None = Query(None), status: str | None = Query(None), session: Session = Depends(get_session)):
    return supplier_service.list_suppliers(session, q=q, status=status)


@router.post('', response_model=SupplierRead)
def create_supplier(payload: SupplierCreate, session: Session = Depends(get_session)):
    try:
        return supplier_service.create_supplier(session, payload)
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.put('/{supplier_id}', response_model=SupplierRead)
def update_supplier(supplier_id: int, payload: SupplierUpdate, session: Session = Depends(get_session)):
    try:
        return supplier_service.update_supplier(session, supplier_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=exc.message)
