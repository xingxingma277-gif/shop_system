from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel


class PricingLastResponse(SQLModel):
    found: bool
    standard_price: float
    last_price: Optional[float] = None
    last_date: Optional[datetime] = None
    last_qty: Optional[float] = None


class PricingHistoryItem(SQLModel):
    date: datetime
    qty: float
    sold_price: float
    sale_id: int


class ProductTrendItem(SQLModel):
    date: datetime
    qty: float
    sold_price: float
    sale_id: int
    customer_id: int
    customer_name: str
