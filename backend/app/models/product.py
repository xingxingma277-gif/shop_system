from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped
from sqlmodel import SQLModel, Field, Relationship

from app.core.time import utc_now

if TYPE_CHECKING:
    from .sale_item import SaleItem
    from .inventory_txn import InventoryTxn


class Product(SQLModel, table=True):
    __tablename__ = "product"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(min_length=1, max_length=120, index=True)
    sku: Optional[str] = Field(default=None, max_length=80, index=True)
    unit: Optional[str] = Field(default=None, max_length=20)
    standard_price: float = Field(default=0, ge=0)
    standard_cost: float = Field(default=0, ge=0)
    stock_quantity: float = Field(default=0)
    stock_warning_threshold: float = Field(default=0, ge=0)
    category: Optional[str] = Field(default=None, max_length=80, index=True)
    brand: Optional[str] = Field(default=None, max_length=80, index=True)
    barcode: Optional[str] = Field(default=None, max_length=80, index=True)
    spec: Optional[str] = Field(default=None, max_length=120)
    image: Optional[str] = Field(default=None, max_length=500)
    is_active: bool = Field(default=True, index=True)

    # ✅ 关键修复：必须有类型注解
    created_at: datetime = Field(default_factory=utc_now, nullable=False)

    sale_items: Mapped[list["SaleItem"]] = Relationship(back_populates="product")
    inventory_txns: Mapped[list["InventoryTxn"]] = Relationship(
        back_populates="product",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
    )
