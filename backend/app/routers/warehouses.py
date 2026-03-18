from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.core.errors import BadRequestError, NotFoundError
from app.db.session import get_session
from app.schemas.warehouse import WarehouseCreate, WarehouseRead, WarehouseUpdate
from app.services import audit_log_service, auth_service, warehouse_service

router = APIRouter(prefix='/api/warehouses', tags=['Warehouses'])


@router.get('', response_model=list[WarehouseRead])
def list_warehouses(status: str | None = Query(None), _: dict | None = Depends(auth_service.require_permissions('warehouse.manage')), session: Session = Depends(get_session)):
    return warehouse_service.list_warehouses(session, status=status)


@router.post('', response_model=WarehouseRead)
def create_warehouse(payload: WarehouseCreate, current: dict | None = Depends(auth_service.require_permissions('warehouse.manage')), session: Session = Depends(get_session)):
    try:
        warehouse = warehouse_service.create_warehouse(session, payload)
        if current:
            audit_log_service.record(session, action='CREATE', resource_type='warehouse', resource_id=warehouse.id, detail=f'创建仓库 {warehouse.name}', actor_user_id=current['id'], actor_name=current['display_name'])
            session.commit()
        return warehouse
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.put('/{warehouse_id}', response_model=WarehouseRead)
def update_warehouse(warehouse_id: int, payload: WarehouseUpdate, current: dict | None = Depends(auth_service.require_permissions('warehouse.manage')), session: Session = Depends(get_session)):
    try:
        warehouse = warehouse_service.update_warehouse(session, warehouse_id, payload)
        if current:
            audit_log_service.record(session, action='UPDATE', resource_type='warehouse', resource_id=warehouse.id, detail=f'更新仓库 {warehouse.name}', actor_user_id=current['id'], actor_name=current['display_name'])
            session.commit()
        return warehouse
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=exc.message)
