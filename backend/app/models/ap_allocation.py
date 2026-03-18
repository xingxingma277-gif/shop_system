from typing import Optional

from sqlmodel import SQLModel, Field


class APAllocation(SQLModel, table=True):
    __tablename__ = "ap_allocation"

    id: Optional[int] = Field(default=None, primary_key=True)
    payment_id: int = Field(foreign_key="supplier_payment.id", index=True)
    purchase_id: int = Field(foreign_key="purchase.id", index=True)
    amount: float = Field(gt=0)
