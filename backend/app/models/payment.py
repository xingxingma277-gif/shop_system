from datetime import datetime
from typing import Optional, TYPE_CHECKING, List

from sqlalchemy.orm import Mapped
from sqlmodel import SQLModel, Field, Relationship

from app.core.time import utc_now

if TYPE_CHECKING:
    from .customer import Customer
    from .sale import Sale
    from .payment_allocation import PaymentAllocation


class Payment(SQLModel, table=True):
    __tablename__ = "payment"

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id", index=True)
    sale_id: Optional[int] = Field(default=None, foreign_key="sale.id", index=True)

    receipt_no: Optional[str] = Field(default=None, max_length=40, index=True)
    pay_type: str = Field(default="partial", max_length=20, index=True)
    amount: float = Field(gt=0)
    method: str = Field(default="transfer", max_length=20, index=True)

    paid_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)
    note: Optional[str] = Field(default=None, max_length=255)
    created_at: datetime = Field(default_factory=utc_now, nullable=False)

    customer: Mapped[Optional["Customer"]] = Relationship(back_populates="payments")
    sale: Mapped[Optional["Sale"]] = Relationship(back_populates="payments")
    allocations: Mapped[List["PaymentAllocation"]] = Relationship(
        back_populates="payment",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
    )
