from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class InventoryCheckCreate(SQLModel):
    warehouse_id: int
    product_id: int
    actual_qty: float = Field(ge=0)
    note: Optional[str] = None


class InventoryCheckRead(SQLModel):
    id: int
    check_no: str
    warehouse_id: int
    warehouse_name: str
    product_id: int
    product_name: str
    status: str
    book_qty: float
    actual_qty: float
    diff_qty: float
    note: Optional[str] = None
    posted_at: Optional[datetime] = None
    created_at: datetime
