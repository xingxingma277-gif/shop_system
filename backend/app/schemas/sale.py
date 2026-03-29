from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field


class SaleItemCreate(SQLModel):
    product_id: int
    qty: float = Field(gt=0)
    unit_price: float = Field(ge=0)
    note: Optional[str] = None


class SaleCreate(SQLModel):
    sale_no: Optional[str] = None
    customer_id: int
    order_type: Optional[str] = Field(default="sale_direct")
    buyer_id: Optional[int] = None
    project: Optional[str] = None
    sale_date: Optional[datetime] = None
    note: Optional[str] = Field(default=None, max_length=500)
    order_stage: Optional[str] = Field(default="SALE_CONFIRMED")
    needs_delivery: Optional[bool] = False
    receiver_name: Optional[str] = None
    receiver_phone: Optional[str] = None
    receiver_address: Optional[str] = None
    delivery_note: Optional[str] = None
    settlement_status: Optional[str] = None
    payment_method: Optional[str] = None
    paid_amount: Optional[float] = None
    payment_note: Optional[str] = None
    source_quote_id: Optional[int] = None
    quote_updated_at: Optional[datetime] = None
    items: List[SaleItemCreate]


class QuoteUpdate(SQLModel):
    customer_id: int
    buyer_id: Optional[int] = None
    project: Optional[str] = None
    note: Optional[str] = None
    quote_updated_at: datetime
    items: List[SaleItemCreate]


class SaleSettlementUpdate(SQLModel):
    settlement_status: str
    paid_amount: float
    payment_method: Optional[str] = None
    payment_note: Optional[str] = None




class QuoteConvertPayload(SQLModel):
    settlement_status: str = Field(default="UNPAID")
    payment_method: Optional[str] = None
    paid_amount: Optional[float] = None
    payment_note: Optional[str] = None
    needs_delivery: bool = False
    receiver_name: Optional[str] = None
    receiver_phone: Optional[str] = None
    receiver_address: Optional[str] = None
    delivery_note: Optional[str] = None


class DeliveryCreatePayload(SQLModel):
    receiver_name: Optional[str] = None
    receiver_phone: Optional[str] = None
    receiver_address: Optional[str] = None
    delivery_note: Optional[str] = None

class SaleItemRead(SQLModel):
    id: int
    product_id: int
    product_name: str
    sku: Optional[str] = None
    unit: Optional[str] = None
    qty: float
    unit_price: float
    line_total: float
    gross_profit: float = 0
    note: Optional[str] = None


class SaleOperationCreate(SQLModel):
    note: Optional[str] = None


class SaleReverseSettlementCreate(SQLModel):
    amount: Optional[float] = None
    note: Optional[str] = None


class SaleRead(SQLModel):
    id: int
    sale_no: str
    customer_id: int
    customer_name: str
    buyer_id: Optional[int] = None
    buyer_name: Optional[str] = None
    project: Optional[str] = None
    source_quote_id: Optional[int] = None
    source_quote_no: Optional[str] = None
    quote_status: Optional[str] = None
    updated_at: datetime

    order_type: str
    order_stage: str
    inventory_effected: bool
    needs_delivery: bool
    delivery_status: str
    receiver_name: Optional[str] = None
    receiver_phone: Optional[str] = None
    receiver_address: Optional[str] = None
    delivery_note: Optional[str] = None

    sale_date: datetime
    note: Optional[str] = None
    total_amount: float
    paid_amount: float
    ar_amount: float
    payment_status: str
    settlement_status: str
    payment_method: Optional[str] = None
    payment_note: Optional[str] = None
    quote_confirmed_at: Optional[datetime] = None
    sale_confirmed_at: Optional[datetime] = None
    delivery_created_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    gross_profit: float = 0
    biz_status: str = "NORMAL"
    created_at: datetime
    items: List[SaleItemRead] = []


class SaleSummary(SQLModel):
    id: int
    sale_no: str
    customer_id: int
    customer_name: str
    buyer_name: Optional[str] = None
    project: Optional[str] = None
    source_quote_id: Optional[int] = None
    source_quote_no: Optional[str] = None
    quote_status: Optional[str] = None
    updated_at: datetime

    order_type: str
    order_stage: str
    inventory_effected: bool
    needs_delivery: bool
    delivery_status: str
    receiver_name: Optional[str] = None
    receiver_phone: Optional[str] = None
    receiver_address: Optional[str] = None
    delivery_note: Optional[str] = None

    sale_date: datetime
    note: Optional[str] = None
    total_amount: float
    paid_amount: float
    ar_amount: float
    payment_status: str
    gross_profit: float = 0
    biz_status: str = "NORMAL"


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
    scene: Optional[str] = "POST_SALE_REPAYMENT"


class SalePaymentSubmitResponse(SQLModel):
    sale: SaleRead
    payment: dict