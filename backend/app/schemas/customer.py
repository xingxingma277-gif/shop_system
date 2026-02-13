from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel

from app.schemas.pagination import PageMeta


class CustomerBase(SQLModel):
    type: str = "company"
    name: str
    contact_name: str
    phone: str
    address: str
    is_active: bool = True


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(SQLModel):
    type: Optional[str] = None
    name: Optional[str] = None
    contact_name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerRead(CustomerBase):
    id: int
    created_at: datetime


class CustomerPage(SQLModel):
    items: list[CustomerRead]
    meta: PageMeta


class BuyerRead(SQLModel):
    id: int
    customer_id: int
    name: str
    phone: Optional[str] = None
    note: Optional[str] = None
    is_active: bool
    created_at: datetime


class BuyerCreate(SQLModel):
    name: str
    phone: Optional[str] = None
    note: Optional[str] = None


class CustomerSaleBrief(SQLModel):
    id: int
    sale_no: str
    sale_date: datetime
    total_amount: float
    paid_amount: float
    payment_status: str
    note: Optional[str] = None


class CustomerArSummary(SQLModel):
    customer_id: int
    total_sales: float
    total_paid: float
    total_ar: float


class CustomerProfile(SQLModel):
    customer: CustomerRead
    contacts: list[BuyerRead]
    ar_summary: CustomerArSummary
    recent_sales: list[CustomerSaleBrief]


class CustomerProfileResponse(CustomerProfile):
    pass
