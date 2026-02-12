from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field


class SaleItemCreate(SQLModel):
    product_id: int
    qty: float = Field(gt=0)
    sold_price: float = Field(ge=0)
    remark: Optional[str] = Field(default=None, max_length=200)


class SaleCreate(SQLModel):
    customer_id: int
    sale_date: Optional[datetime] = None
    note: Optional[str] = Field(default=None, max_length=500)
    items: List[SaleItemCreate]


class SaleItemRead(SQLModel):
    id: int
    product_id: int
    product_name: str
    sku: Optional[str] = None
    unit: Optional[str] = None
    qty: float
    sold_price: float
    line_total: float
    remark: Optional[str] = None


class SaleRead(SQLModel):
    id: int
    customer_id: int
    customer_name: str
    sale_date: datetime
    note: Optional[str] = None
    total_amount: float
    created_at: datetime
    items: List[SaleItemRead] = []


class SaleSummary(SQLModel):
    id: int
    customer_id: int
    customer_name: str
    sale_date: datetime
    note: Optional[str] = None
    total_amount: float


class SalePage(SQLModel):
    items: List[SaleSummary]
    total: int
    page: int
    page_size: int
