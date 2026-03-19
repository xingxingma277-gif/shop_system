from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field

from app.core.time import utc_now


class Warehouse(SQLModel, table=True):
    __tablename__ = "warehouse"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(max_length=30, index=True, unique=True)
    name: str = Field(max_length=120, index=True)
    address: Optional[str] = Field(default=None, max_length=255)
    status: str = Field(default="ACTIVE", max_length=20, index=True)
    is_default: bool = Field(default=False, index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
