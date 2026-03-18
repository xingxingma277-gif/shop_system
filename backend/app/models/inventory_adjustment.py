from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field

from app.core.time import utc_now


class InventoryAdjustment(SQLModel, table=True):
    __tablename__ = "inventory_adjustment"

    id: Optional[int] = Field(default=None, primary_key=True)
    adj_no: str = Field(default="", max_length=40, index=True, unique=True)
    warehouse_id: int = Field(foreign_key="warehouse.id", index=True)
    product_id: int = Field(foreign_key="product.id", index=True)

    adj_type: str = Field(max_length=20, index=True)  # GAIN/LOSS
    qty: float = Field(gt=0)
    reason: Optional[str] = Field(default=None, max_length=255)
    note: Optional[str] = Field(default=None, max_length=255)

    created_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)
