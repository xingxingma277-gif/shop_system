from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel

from app.core.time import utc_now


class AuditLog(SQLModel, table=True):
    __tablename__ = 'audit_log'

    id: Optional[int] = Field(default=None, primary_key=True)
    actor_user_id: Optional[int] = Field(default=None, foreign_key='user.id', index=True)
    actor_name: str = Field(default='system', max_length=100, index=True)
    action: str = Field(default='', max_length=80, index=True)
    resource_type: str = Field(default='', max_length=50, index=True)
    resource_id: Optional[int] = Field(default=None, index=True)
    detail: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)
