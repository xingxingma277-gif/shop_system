from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class WarehouseCreate(SQLModel):
    code: str = Field(min_length=1, max_length=30)
    name: str = Field(min_length=1, max_length=120)
    address: Optional[str] = None
    is_default: bool = False


class WarehouseUpdate(SQLModel):
    name: Optional[str] = None
    address: Optional[str] = None
    status: Optional[str] = None
    is_default: Optional[bool] = None


class WarehouseRead(SQLModel):
    id: int
    code: str
    name: str
    address: Optional[str] = None
    status: str
    is_default: bool
    created_at: datetime
