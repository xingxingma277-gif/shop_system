from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field

from app.core.time import utc_now


class InventoryTransfer(SQLModel, table=True):
    __tablename__ = "inventory_transfer"

    id: Optional[int] = Field(default=None, primary_key=True)
    transfer_no: str = Field(default="", max_length=40, index=True, unique=True)
    from_warehouse_id: int = Field(foreign_key="warehouse.id", index=True)
    to_warehouse_id: int = Field(foreign_key="warehouse.id", index=True)
    product_id: int = Field(foreign_key="product.id", index=True)
    qty: float = Field(nullable=False)
    status: str = Field(default="DRAFT", max_length=20, index=True)
    note: Optional[str] = Field(default=None, max_length=255)
    posted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)
