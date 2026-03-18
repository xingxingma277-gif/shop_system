from fastapi import Header, HTTPException
from sqlmodel import Session, select

from app.core.errors import BadRequestError, NotFoundError
from app.models import Permission, Role, RolePermission, User, UserRole
from app.services.auth_admin_service import _hash_password


def authenticate(session: Session, username: str, password: str):
    user = session.exec(select(User).where(User.username == username.strip())).first()
    if not user or user.password_hash != _hash_password(password):
        raise BadRequestError('用户名或密码错误')
    if user.status != 'ACTIVE':
        raise BadRequestError('用户已停用')
    return build_current_user(session, user)


def get_user_by_header(session: Session, x_auth_user: str | None):
    if not x_auth_user:
        return None
    return session.exec(select(User).where(User.username == x_auth_user.strip())).first()


def build_current_user(session: Session, user: User):
    role_links = session.exec(select(UserRole).where(UserRole.user_id == user.id)).all()
    role_ids = [link.role_id for link in role_links]
    roles = session.exec(select(Role).where(Role.id.in_(role_ids))).all() if role_ids else []
    perm_ids = [link.permission_id for link in session.exec(select(RolePermission).where(RolePermission.role_id.in_(role_ids))).all()] if role_ids else []
    permissions = session.exec(select(Permission).where(Permission.id.in_(perm_ids))).all() if perm_ids else []
    return {
        'id': user.id,
        'username': user.username,
        'display_name': user.display_name,
        'is_superuser': user.is_superuser,
        'role_ids': role_ids,
        'role_names': [role.name for role in roles],
        'permission_codes': sorted({perm.code for perm in permissions}),
    }


def require_permissions(*codes: str):
    def dependency(session: Session, x_auth_user: str | None = Header(default=None)):
        existing_users = session.exec(select(User.id).limit(1)).first()
        user = get_user_by_header(session, x_auth_user)
        if not existing_users:
            return None
        if not user:
            raise HTTPException(status_code=401, detail='请先登录')
        current = build_current_user(session, user)
        if current['is_superuser']:
            return current
        missing = [code for code in codes if code not in current['permission_codes']]
        if missing:
            raise HTTPException(status_code=403, detail='无权限执行该操作')
        return current

    return dependency
