from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field


class SaleItemCreate(SQLModel):
    product_id: int
    qty: float = Field(gt=0)
    unit_price: float = Field(ge=0)
    note: Optional[str] = None


class SaleCreate(SQLModel):
    customer_id: int
    buyer_id: int
    project: str
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
    unit_price: float
    line_total: float
    note: Optional[str] = None


class SaleRead(SQLModel):
    id: int
    sale_no: str
    customer_id: int
    customer_name: str
    buyer_id: Optional[int] = None
    buyer_name: Optional[str] = None
    project: Optional[str] = None
    sale_date: datetime
    note: Optional[str] = None
    total_amount: float
    paid_amount: float
    ar_amount: float
    payment_status: str
    created_at: datetime
    items: List[SaleItemRead] = []


class SaleSummary(SQLModel):
    id: int
    sale_no: str
    customer_id: int
    customer_name: str
    buyer_name: Optional[str] = None
    project: Optional[str] = None
    sale_date: datetime
    note: Optional[str] = None
    total_amount: float
    paid_amount: float
    ar_amount: float
    payment_status: str


class SalePage(SQLModel):
    items: List[SaleSummary]
    total: int
    page: int
    page_size: int


class SalePaymentCreate(SQLModel):
    pay_type: str
    method: str
    amount: Optional[float] = None
    note: Optional[str] = None


class SalePaymentSubmitResponse(SQLModel):
    sale: SaleRead
    payment: dict
