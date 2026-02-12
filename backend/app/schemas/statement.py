from datetime import datetime, date
from typing import Optional, List

from sqlmodel import SQLModel


# ------- Sale 列表（对账用） -------

class StatementSaleItem(SQLModel):
    id: int
    sale_no: str
    created_at: datetime
    total_amount: float
    paid_amount: float
    unpaid_amount: float
    payment_status: str  # "unpaid" | "partial" | "paid"


class ArSummaryResponse(SQLModel):
    customer_id: int
    date_from: Optional[date] = None
    date_to: Optional[date] = None

    total_amount: float
    total_paid: float
    total_unpaid: float

    sale_count: int
    unpaid_sale_count: int


class StatementResponse(SQLModel):
    summary: ArSummaryResponse
    sales: List[StatementSaleItem]
