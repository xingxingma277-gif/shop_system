from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped
from sqlmodel import SQLModel, Field, Relationship

from app.core.time import utc_now

if TYPE_CHECKING:
    from .sale_item import SaleItem


class Product(SQLModel, table=True):
    __tablename__ = "product"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(min_length=1, max_length=120, index=True)
    sku: Optional[str] = Field(default=None, max_length=80, index=True)
    unit: Optional[str] = Field(default=None, max_length=20)
    standard_price: float = Field(default=0, ge=0)
    is_active: bool = Field(default=True, index=True)

    # ✅ 关键修复：必须有类型注解
    created_at: datetime = Field(default_factory=utc_now, nullable=False)

    sale_items: Mapped[list["SaleItem"]] = Relationship(back_populates="product")
