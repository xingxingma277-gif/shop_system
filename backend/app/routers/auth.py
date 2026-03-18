from fastapi import APIRouter, Depends, Header, HTTPException
from sqlmodel import Session

from app.core.errors import BadRequestError, NotFoundError
from app.db.session import get_session
from app.schemas.auth import CurrentUserRead, LoginPayload
from app.services import auth_service

router = APIRouter(prefix='/api/auth', tags=['Auth'])


@router.post('/login', response_model=CurrentUserRead)
def login(payload: LoginPayload, session: Session = Depends(get_session)):
    try:
        return auth_service.authenticate(session, payload.username, payload.password)
    except (BadRequestError, NotFoundError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.get('/me', response_model=CurrentUserRead)
def me(x_auth_user: str | None = Header(default=None), session: Session = Depends(get_session)):
    user = auth_service.get_user_by_header(session, x_auth_user)
    if not user:
        raise HTTPException(status_code=401, detail='未登录')
    return auth_service.build_current_user(session, user)
