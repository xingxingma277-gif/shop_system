from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field


class ProductRead(SQLModel):
    id: int
    name: str
    sku: Optional[str] = None
    unit: Optional[str] = None
    standard_price: float
    is_active: bool
    created_at: datetime


class ProductCreate(SQLModel):
    name: str = Field(min_length=1, max_length=120)
    sku: Optional[str] = Field(default=None, max_length=80)
    unit: Optional[str] = Field(default=None, max_length=20)
    standard_price: float = Field(default=0, ge=0)
    is_active: bool = True


class ProductUpdate(SQLModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=120)
    sku: Optional[str] = Field(default=None, max_length=80)
    unit: Optional[str] = Field(default=None, max_length=20)
    standard_price: Optional[float] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class ProductPage(SQLModel):
    items: List[ProductRead]
    total: int
    page: int
    page_size: int
