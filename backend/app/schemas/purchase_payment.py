from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field


class SupplierPaymentCreate(SQLModel):
    supplier_id: int
    purchase_id: Optional[int] = None
    amount: float = Field(gt=0)
    method: str
    paid_at: Optional[datetime] = None
    note: Optional[str] = None


class APAllocationItem(SQLModel):
    purchase_id: int
    amount: float = Field(gt=0)


class APAllocationCreate(SQLModel):
    items: List[APAllocationItem]


class SupplierPaymentRead(SQLModel):
    id: int
    receipt_no: str
    supplier_id: int
    purchase_id: Optional[int] = None
    scene: str
    method: str
    amount: float
    paid_at: datetime
    note: Optional[str] = None


class PurchaseOpenAPRead(SQLModel):
    purchase_id: int
    purchase_no: str
    purchase_date: datetime
    total_amount: float
    paid_amount: float
    ap_amount: float
