from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class SupplierCreate(SQLModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=120)
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    note: Optional[str] = None


class SupplierUpdate(SQLModel):
    name: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    note: Optional[str] = None
    status: Optional[str] = None


class SupplierRead(SQLModel):
    id: int
    code: str
    name: str
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    note: Optional[str] = None
    status: str
    created_at: datetime
