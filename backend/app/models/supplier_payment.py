from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field

from app.core.time import utc_now


class SupplierPayment(SQLModel, table=True):
    __tablename__ = "supplier_payment"

    id: Optional[int] = Field(default=None, primary_key=True)
    receipt_no: str = Field(default="", max_length=40, index=True, unique=True)
    supplier_id: int = Field(foreign_key="supplier.id", index=True)
    purchase_id: Optional[int] = Field(default=None, foreign_key="purchase.id", index=True)

    scene: str = Field(default="AP_PAYMENT", max_length=30, index=True)
    method: str = Field(default="bank_transfer", max_length=20, index=True)
    amount: float = Field(gt=0)

    paid_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)
    note: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)
