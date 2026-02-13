from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy import Index, desc
from sqlalchemy.orm import Mapped
from sqlmodel import SQLModel, Field, Relationship

from app.core.time import utc_now

if TYPE_CHECKING:
    from .customer import Customer
    from .sale_item import SaleItem
    from .payment import Payment


class Sale(SQLModel, table=True):
    __tablename__ = "sale"
    __table_args__ = (
        Index("ix_sale_customer_saledate_desc", "customer_id", desc("sale_date")),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id", index=True)

    buyer_id: Optional[int] = Field(default=None, foreign_key="customer_contact.id", index=True)
    contact_id: Optional[int] = Field(default=None, foreign_key="customer_contact.id", index=True)
    contact_name_snapshot: Optional[str] = Field(default=None, max_length=100)
    project: Optional[str] = Field(default=None, max_length=200)
    project_name: Optional[str] = Field(default=None, max_length=200)
    signed_by: Optional[str] = Field(default=None, max_length=100)

    sale_date: datetime = Field(default_factory=utc_now, nullable=False, index=True)
    note: Optional[str] = Field(default=None, max_length=500)

    total_amount: float = Field(default=0, ge=0, nullable=False)
    paid_amount: float = Field(default=0, ge=0, nullable=False)
    ar_amount: float = Field(default=0, ge=0, nullable=False)
    payment_status: str = Field(default="unpaid", max_length=20, index=True)

    created_at: datetime = Field(default_factory=utc_now, nullable=False)

    customer: Mapped[Optional["Customer"]] = Relationship(back_populates="sales")
    items: Mapped[list["SaleItem"]] = Relationship(
        back_populates="sale",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
    )

    payments: Mapped[list["Payment"]] = Relationship(
        back_populates="sale",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
    )
