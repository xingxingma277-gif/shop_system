from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.core.time import utc_now


class User(SQLModel, table=True):
    __tablename__ = 'user'

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(default='', max_length=50, index=True, unique=True)
    display_name: str = Field(default='', max_length=100, index=True)
    password_hash: str = Field(default='', max_length=255)
    status: str = Field(default='ACTIVE', max_length=20, index=True)
    is_superuser: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)
