from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class InventoryAdjustmentCreate(SQLModel):
    warehouse_id: int
    product_id: int
    adj_type: str = Field(regex=r"^(GAIN|LOSS)$")
    qty: float = Field(gt=0)
    reason: Optional[str] = None
    note: Optional[str] = None


class InventoryAdjustmentRead(SQLModel):
    id: int
    adj_no: str
    warehouse_id: int
    warehouse_name: str
    product_id: int
    product_name: str
    adj_type: str
    qty: float
    reason: Optional[str] = None
    note: Optional[str] = None
    created_at: datetime