from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field

from app.core.time import utc_now


class Supplier(SQLModel, table=True):
    __tablename__ = "supplier"

    id: Optional[int] = Field(default=None, primary_key=True)
    code: str = Field(max_length=30, index=True, unique=True)
    name: str = Field(max_length=120, index=True)
    contact_name: Optional[str] = Field(default=None, max_length=60)
    phone: Optional[str] = Field(default=None, max_length=50)
    address: Optional[str] = Field(default=None, max_length=255)
    note: Optional[str] = Field(default=None, max_length=255)
    status: str = Field(default="ACTIVE", max_length=20, index=True)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
