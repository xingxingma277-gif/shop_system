from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class InventoryTransferCreate(SQLModel):
    from_warehouse_id: int
    to_warehouse_id: int
    product_id: int
    qty: float = Field(gt=0)
    note: Optional[str] = None


class InventoryTransferRead(SQLModel):
    id: int
    transfer_no: str
    from_warehouse_id: int
    from_warehouse_name: str
    to_warehouse_id: int
    to_warehouse_name: str
    product_id: int
    product_name: str
    qty: float
    status: str
    note: Optional[str] = None
    posted_at: Optional[datetime] = None
    created_at: datetime
