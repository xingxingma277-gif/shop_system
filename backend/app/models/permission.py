from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.core.time import utc_now


class Permission(SQLModel, table=True):
    __tablename__ = 'permission'

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(default='', max_length=80, index=True, unique=True)
    name: str = Field(default='', max_length=120, index=True)
    resource: str = Field(default='', max_length=50, index=True)
    action: str = Field(default='', max_length=50, index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)
