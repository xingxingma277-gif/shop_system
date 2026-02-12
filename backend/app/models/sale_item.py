from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped
from sqlmodel import SQLModel, Field, Relationship

from app.core.time import utc_now

if TYPE_CHECKING:
    from .sale import Sale
    from .product import Product


class SaleItem(SQLModel, table=True):
    __tablename__ = "sale_item"

    id: Optional[int] = Field(default=None, primary_key=True)
    sale_id: int = Field(foreign_key="sale.id", index=True)
    product_id: int = Field(foreign_key="product.id", index=True)

    qty: float = Field(gt=0)
    sold_price: float = Field(ge=0)
    line_total: float = Field(default=0, ge=0, nullable=False)

    remark: Optional[str] = Field(default=None, max_length=200)

    # ✅ 关键修复：必须有类型注解
    created_at: datetime = Field(default_factory=utc_now, nullable=False)

    sale: Mapped[Optional["Sale"]] = Relationship(back_populates="items")
    product: Mapped[Optional["Product"]] = Relationship(back_populates="sale_items")
