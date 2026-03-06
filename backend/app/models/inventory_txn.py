from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped
from sqlmodel import SQLModel, Field, Relationship

from app.core.time import utc_now

if TYPE_CHECKING:
    from .product import Product


class InventoryTxn(SQLModel, table=True):
    __tablename__ = "inventory_txn"

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id", index=True)
    change_qty: float = Field(nullable=False)
    after_qty: float = Field(nullable=False)
    biz_type: str = Field(max_length=30, index=True)
    biz_id: Optional[int] = Field(default=None, index=True)
    sale_id: Optional[int] = Field(default=None, foreign_key="sale.id", index=True)
    note: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)

    product: Mapped[Optional["Product"]] = Relationship(back_populates="inventory_txns")
