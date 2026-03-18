from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.core.time import utc_now


class AuthToken(SQLModel, table=True):
    __tablename__ = 'auth_token'

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='user.id', index=True)
    token: str = Field(default='', max_length=128, index=True, unique=True)
    expires_at: datetime = Field(nullable=False, index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)
