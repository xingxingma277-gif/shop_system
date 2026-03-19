from datetime import timedelta
import secrets

from fastapi import Depends, Header, HTTPException  # <--- 添加了 Depends
from sqlmodel import Session, select

from app.core.errors import BadRequestError, NotFoundError
from app.core.time import utc_now
from app.models import AuthToken, Permission, Role, RolePermission, User, UserRole
from app.services.auth_admin_service import _hash_password
from app.db.session import get_session  # <--- 添加了 get_session


_TOKEN_TTL_SECONDS = 60 * 60 * 12


def authenticate(session: Session, username: str, password: str):
    user = session.exec(select(User).where(User.username == username.strip())).first()
    if not user or user.password_hash != _hash_password(password):
        raise BadRequestError('用户名或密码错误')
    if user.status != 'ACTIVE':
        raise BadRequestError('用户已停用')
    token = issue_token(session, user.id)
    session.commit()
    return {
        'token': token.token,
        'token_type': 'bearer',
        'expires_in': _TOKEN_TTL_SECONDS,
        'user': build_current_user(session, user),
    }


def issue_token(session: Session, user_id: int):
    token = AuthToken(user_id=user_id, token=secrets.token_hex(32), expires_at=utc_now() + timedelta(seconds=_TOKEN_TTL_SECONDS))
    session.add(token)
    session.flush()
    return token


def _extract_token(authorization: str | None, x_auth_token: str | None):
    if authorization and authorization.lower().startswith('bearer '):
        return authorization.split(' ', 1)[1].strip()
    if x_auth_token:
        return x_auth_token.strip()
    return None


def _is_expired(dt):
    if dt.tzinfo is None:
        return dt < utc_now().replace(tzinfo=None)
    return dt < utc_now()


def get_user_by_token(session: Session, authorization: str | None, x_auth_token: str | None):
    token_value = _extract_token(authorization, x_auth_token)
    if not token_value:
        return None
    token = session.exec(select(AuthToken).where(AuthToken.token == token_value)).first()
    if not token or _is_expired(token.expires_at):
        return None
    return session.get(User, token.user_id)


def revoke_token(session: Session, authorization: str | None, x_auth_token: str | None):
    token_value = _extract_token(authorization, x_auth_token)
    if not token_value:
        return
    token = session.exec(select(AuthToken).where(AuthToken.token == token_value)).first()
    if token:
        session.delete(token)
        session.commit()


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
    def dependency(
        session: Session = Depends(get_session),  # <--- 修改了这里，加上了 = Depends(get_session)
        authorization: str | None = Header(default=None),
        x_auth_token: str | None = Header(default=None)
    ):
        existing_users = session.exec(select(User.id).limit(1)).first()
        user = get_user_by_token(session, authorization, x_auth_token)
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