from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.core.time import utc_now


class Role(SQLModel, table=True):
    __tablename__ = 'role'

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(default='', max_length=50, index=True, unique=True)
    name: str = Field(default='', max_length=100, index=True)
    status: str = Field(default='ACTIVE', max_length=20, index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)
