from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .purchase import Purchase


class PurchaseItem(SQLModel, table=True):
    __tablename__ = "purchase_item"

    id: Optional[int] = Field(default=None, primary_key=True)
    purchase_id: int = Field(foreign_key="purchase.id", index=True)
    product_id: int = Field(foreign_key="product.id", index=True)

    qty: float = Field(gt=0)
    received_qty: float = Field(default=0, ge=0)
    unit_cost: float = Field(ge=0)
    line_total: float = Field(default=0, ge=0)
    note: Optional[str] = Field(default=None, max_length=255)

    purchase: Mapped[Optional["Purchase"]] = Relationship(back_populates="items")
