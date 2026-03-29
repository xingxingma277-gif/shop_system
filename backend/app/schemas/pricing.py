from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel


class PricingLastResponse(SQLModel):
    found: bool
    standard_price: Optional[float] = None
    last_price: Optional[float] = None
    last_sale_date: Optional[datetime] = None
    last_sale_no: Optional[str] = None
    last_qty: Optional[float] = None
    source_order_type: Optional[str] = None
    source_stage: Optional[str] = None


class PricingHistoryItem(SQLModel):
    sale_id: int
    sale_no: str
    sale_date: datetime
    order_type: Optional[str] = None
    order_stage: Optional[str] = None
    unit_price: float
    qty: float


class PricingHistoryMeta(SQLModel):
    total: int
    page: int
    page_size: int
    pages: int


class PricingHistoryResponse(SQLModel):
    items: list[PricingHistoryItem]
    meta: PricingHistoryMeta


class ProductTrendItem(SQLModel):
    date: datetime
    qty: float
    sold_price: float
    sale_id: int
    customer_id: int
    customer_name: str
