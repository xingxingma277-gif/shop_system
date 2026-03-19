from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Index, desc
from sqlalchemy.orm import Mapped
from sqlmodel import SQLModel, Field, Relationship

from app.core.time import utc_now

if TYPE_CHECKING:
    from .purchase_item import PurchaseItem


class Purchase(SQLModel, table=True):
    __tablename__ = "purchase"
    __table_args__ = (Index("ix_purchase_supplier_date_desc", "supplier_id", desc("purchase_date")),)

    id: Optional[int] = Field(default=None, primary_key=True)
    purchase_no: str = Field(default="", max_length=30, index=True, unique=True)
    supplier_id: int = Field(foreign_key="supplier.id", index=True)
    warehouse_id: int = Field(foreign_key="warehouse.id", index=True)
    purchase_date: datetime = Field(default_factory=utc_now, nullable=False, index=True)

    status: str = Field(default="DRAFT", max_length=30, index=True)
    note: Optional[str] = Field(default=None, max_length=255)

    total_amount: float = Field(default=0, ge=0, nullable=False)
    paid_amount: float = Field(default=0, ge=0, nullable=False)
    ap_amount: float = Field(default=0, ge=0, nullable=False)

    created_at: datetime = Field(default_factory=utc_now, nullable=False)

    items: Mapped[list["PurchaseItem"]] = Relationship(
        back_populates="purchase",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
    )
