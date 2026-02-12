from datetime import date, datetime
from typing import Optional

from sqlmodel import SQLModel

from app.schemas.pagination import PageMeta
from app.schemas.contact import CustomerContactRead


# -------------------------
# Customer 基础 / CRUD
# -------------------------
class CustomerBase(SQLModel):
    name: str
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(SQLModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerRead(CustomerBase):
    id: int
    created_at: datetime


class CustomerPage(SQLModel):
    items: list[CustomerRead]
    meta: PageMeta


# -------------------------
# 客户档案页：最近销售单简表
# -------------------------
class CustomerSaleBrief(SQLModel):
    id: int
    sale_no: str
    sale_date: datetime
    total_amount: float
    paid_amount: float
    payment_status: str
    note: Optional[str] = None


# -------------------------
# AR 汇总（应收）
# -------------------------
class CustomerArSummary(SQLModel):
    customer_id: int
    total_sales: float
    total_paid: float
    total_ar: float


# -------------------------
# Customer Profile（档案页）
# -------------------------
class CustomerProfile(SQLModel):
    customer: CustomerRead
    contacts: list[CustomerContactRead]
    ar_summary: CustomerArSummary
    recent_sales: list[CustomerSaleBrief]


# 兼容别名：如果你的 router 写的是 CustomerProfileResponse
class CustomerProfileResponse(CustomerProfile):
    pass


# -------------------------
# 对账单 / 结算：明细行
# -------------------------
class StatementSaleLine(SQLModel):
    sale_id: int
    sale_no: str
    sale_date: datetime
    total_amount: float
    paid_amount: float
    payment_status: str
    note: Optional[str] = None


class StatementPaymentLine(SQLModel):
    payment_id: int
    sale_id: Optional[int] = None
    paid_at: datetime
    amount: float
    method: str
    note: Optional[str] = None


class CustomerStatementTotals(SQLModel):
    sales_total: float
    paid_total: float
    ar_total: float


class CustomerStatement(SQLModel):
    customer_id: int
    date_from: Optional[date] = None
    date_to: Optional[date] = None
    sales: list[StatementSaleLine]
    payments: list[StatementPaymentLine]
    totals: CustomerStatementTotals


# 兼容别名：如果你的 router 写的是 CustomerStatementResponse
class CustomerStatementResponse(CustomerStatement):
    pass
