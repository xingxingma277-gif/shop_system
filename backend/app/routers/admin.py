from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.core.errors import BadRequestError, NotFoundError
from app.db.session import get_session
from app.schemas.auth_admin import AuditLogRead, PermissionCreate, PermissionRead, RoleCreate, RoleRead, RoleUpdate, UserCreate, UserRead, UserUpdate
from app.services import audit_log_service, auth_admin_service

router = APIRouter(prefix='/api/admin', tags=['Admin'])


@router.get('/users', response_model=list[UserRead])
def list_users(status: str | None = Query(None), session: Session = Depends(get_session)):
    return auth_admin_service.list_users(session, status=status)


@router.post('/users', response_model=UserRead)
def create_user(payload: UserCreate, session: Session = Depends(get_session)):
    try:
        return auth_admin_service.create_user(session, payload)
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.put('/users/{user_id}', response_model=UserRead)
def update_user(user_id: int, payload: UserUpdate, session: Session = Depends(get_session)):
    try:
        return auth_admin_service.update_user(session, user_id, payload)
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.get('/roles', response_model=list[RoleRead])
def list_roles(status: str | None = Query(None), session: Session = Depends(get_session)):
    return auth_admin_service.list_roles(session, status=status)


@router.post('/roles', response_model=RoleRead)
def create_role(payload: RoleCreate, session: Session = Depends(get_session)):
    try:
        return auth_admin_service.create_role(session, payload)
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.put('/roles/{role_id}', response_model=RoleRead)
def update_role(role_id: int, payload: RoleUpdate, session: Session = Depends(get_session)):
    try:
        return auth_admin_service.update_role(session, role_id, payload)
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.get('/permissions', response_model=list[PermissionRead])
def list_permissions(session: Session = Depends(get_session)):
    return auth_admin_service.list_permissions(session)


@router.post('/permissions', response_model=PermissionRead)
def create_permission(payload: PermissionCreate, session: Session = Depends(get_session)):
    try:
        return auth_admin_service.create_permission(session, payload)
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.get('/audit-logs', response_model=list[AuditLogRead])
def list_audit_logs(resource_type: str | None = Query(None), action: str | None = Query(None), actor_name: str | None = Query(None), session: Session = Depends(get_session)):
    return audit_log_service.list_logs(session, resource_type=resource_type, action=action, actor_name=actor_name)
