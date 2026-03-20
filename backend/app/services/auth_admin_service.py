import hashlib

from sqlmodel import Session, delete, select

from app.core.config import APP_ENV, DEFAULT_ADMIN_PASSWORD, DEFAULT_ADMIN_USERNAME
from app.core.errors import BadRequestError, NotFoundError
from app.models import Permission, Role, RolePermission, User, UserRole
from app.services import audit_log_service


def _hash_password(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def _get_role_map(session: Session, role_ids: list[int]):
    roles = session.exec(select(Role).where(Role.id.in_(role_ids))).all() if role_ids else []
    if len(roles) != len(set(role_ids)):
        raise BadRequestError('存在无效角色')
    return {role.id: role for role in roles}


def _get_permission_map(session: Session, permission_ids: list[int]):
    perms = session.exec(select(Permission).where(Permission.id.in_(permission_ids))).all() if permission_ids else []
    if len(perms) != len(set(permission_ids)):
        raise BadRequestError('存在无效权限')
    return {perm.id: perm for perm in perms}


def list_users(session: Session, status: str | None = None):
    stmt = select(User)
    if status:
        stmt = stmt.where(User.status == status)
    users = session.exec(stmt.order_by(User.created_at.desc(), User.id.desc())).all()
    return [_to_user_read(session, user) for user in users]


def create_user(session: Session, payload):
    existing = session.exec(select(User).where(User.username == payload.username)).first()
    if existing:
        raise BadRequestError('用户名已存在')
    _get_role_map(session, list(payload.role_ids or []))
    user = User(
        username=payload.username.strip(),
        display_name=payload.display_name.strip(),
        password_hash=_hash_password(payload.password),
        status='ACTIVE',
        is_superuser=bool(payload.is_superuser),
    )
    session.add(user)
    session.flush()
    _replace_user_roles(session, user.id, list(payload.role_ids or []))
    audit_log_service.record(session, action='CREATE', resource_type='user', resource_id=user.id, detail=f'创建用户 {user.username}')
    session.commit()
    return _to_user_read(session, user)


def update_user(session: Session, user_id: int, payload):
    user = session.get(User, user_id)
    if not user:
        raise NotFoundError('用户不存在')
    if payload.display_name is not None:
        user.display_name = payload.display_name.strip()
    if payload.password:
        user.password_hash = _hash_password(payload.password)
    if payload.status is not None:
        user.status = payload.status
    if payload.is_superuser is not None:
        user.is_superuser = bool(payload.is_superuser)
    if payload.role_ids is not None:
        _get_role_map(session, list(payload.role_ids))
        _replace_user_roles(session, user.id, list(payload.role_ids))
    session.add(user)
    audit_log_service.record(session, action='UPDATE', resource_type='user', resource_id=user.id, detail=f'更新用户 {user.username}')
    session.commit()
    return _to_user_read(session, user)


def list_roles(session: Session, status: str | None = None):
    stmt = select(Role)
    if status:
        stmt = stmt.where(Role.status == status)
    roles = session.exec(stmt.order_by(Role.created_at.desc(), Role.id.desc())).all()
    return [_to_role_read(session, role) for role in roles]


def create_role(session: Session, payload):
    existing = session.exec(select(Role).where(Role.code == payload.code)).first()
    if existing:
        raise BadRequestError('角色编码已存在')
    _get_permission_map(session, list(payload.permission_ids or []))
    role = Role(code=payload.code.strip(), name=payload.name.strip(), status='ACTIVE')
    session.add(role)
    session.flush()
    _replace_role_permissions(session, role.id, list(payload.permission_ids or []))
    audit_log_service.record(session, action='CREATE', resource_type='role', resource_id=role.id, detail=f'创建角色 {role.code}')
    session.commit()
    return _to_role_read(session, role)


def update_role(session: Session, role_id: int, payload):
    role = session.get(Role, role_id)
    if not role:
        raise NotFoundError('角色不存在')
    if payload.name is not None:
        role.name = payload.name.strip()
    if payload.status is not None:
        role.status = payload.status
    if payload.permission_ids is not None:
        _get_permission_map(session, list(payload.permission_ids))
        _replace_role_permissions(session, role.id, list(payload.permission_ids))
    session.add(role)
    audit_log_service.record(session, action='UPDATE', resource_type='role', resource_id=role.id, detail=f'更新角色 {role.code}')
    session.commit()
    return _to_role_read(session, role)


def list_permissions(session: Session):
    return session.exec(select(Permission).order_by(Permission.resource.asc(), Permission.action.asc(), Permission.id.asc())).all()


def create_permission(session: Session, payload):
    existing = session.exec(select(Permission).where(Permission.code == payload.code)).first()
    if existing:
        raise BadRequestError('权限编码已存在')
    permission = Permission(code=payload.code.strip(), name=payload.name.strip(), resource=payload.resource.strip(), action=payload.action.strip())
    session.add(permission)
    session.flush()
    audit_log_service.record(session, action='CREATE', resource_type='permission', resource_id=permission.id, detail=f'创建权限 {permission.code}')
    session.commit()
    return permission


def _replace_user_roles(session: Session, user_id: int, role_ids: list[int]):
    session.exec(delete(UserRole).where(UserRole.user_id == user_id))
    for role_id in sorted(set(role_ids)):
        session.add(UserRole(user_id=user_id, role_id=role_id))
    session.flush()


def _replace_role_permissions(session: Session, role_id: int, permission_ids: list[int]):
    session.exec(delete(RolePermission).where(RolePermission.role_id == role_id))
    for permission_id in sorted(set(permission_ids)):
        session.add(RolePermission(role_id=role_id, permission_id=permission_id))
    session.flush()


def _to_user_read(session: Session, user: User):
    role_links = session.exec(select(UserRole).where(UserRole.user_id == user.id)).all()
    role_ids = [link.role_id for link in role_links]
    role_map = _get_role_map(session, role_ids) if role_ids else {}
    return {
        'id': user.id,
        'username': user.username,
        'display_name': user.display_name,
        'status': user.status,
        'is_superuser': user.is_superuser,
        'role_ids': role_ids,
        'role_names': [role_map[rid].name for rid in role_ids if rid in role_map],
        'created_at': user.created_at,
    }


def _to_role_read(session: Session, role: Role):
    perm_links = session.exec(select(RolePermission).where(RolePermission.role_id == role.id)).all()
    permission_ids = [link.permission_id for link in perm_links]
    perm_map = _get_permission_map(session, permission_ids) if permission_ids else {}
    return {
        'id': role.id,
        'code': role.code,
        'name': role.name,
        'status': role.status,
        'permission_ids': permission_ids,
        'permission_codes': [perm_map[pid].code for pid in permission_ids if pid in perm_map],
        'created_at': role.created_at,
    }


def ensure_dev_admin(session: Session):
    if APP_ENV.lower() != 'dev':
        return None
    existing = session.exec(select(User).limit(1)).first()
    if existing:
        return existing
    user = User(
        username=DEFAULT_ADMIN_USERNAME.strip(),
        display_name='开发管理员',
        password_hash=_hash_password(DEFAULT_ADMIN_PASSWORD),
        status='ACTIVE',
        is_superuser=True,
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
