from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field

from app.core.time import utc_now


class InventoryCheck(SQLModel, table=True):
    __tablename__ = "inventory_check"

    id: Optional[int] = Field(default=None, primary_key=True)
    check_no: str = Field(default="", max_length=40, index=True, unique=True)
    warehouse_id: int = Field(foreign_key="warehouse.id", index=True)
    product_id: int = Field(foreign_key="product.id", index=True)
    status: str = Field(default="DRAFT", max_length=20, index=True)
    book_qty: float = Field(default=0, nullable=False)
    actual_qty: float = Field(default=0, nullable=False)
    diff_qty: float = Field(default=0, nullable=False)
    note: Optional[str] = Field(default=None, max_length=255)
    posted_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)
