from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .payment import Payment
    from .sale import Sale


class PaymentAllocation(SQLModel, table=True):
    __tablename__ = "payment_allocation"

    id: Optional[int] = Field(default=None, primary_key=True)
    payment_id: int = Field(foreign_key="payment.id", index=True)
    sale_id: int = Field(foreign_key="sale.id", index=True)
    amount: float = Field(gt=0)

    payment: Mapped[Optional["Payment"]] = Relationship(back_populates="allocations")
    sale: Mapped[Optional["Sale"]] = Relationship(back_populates="payment_allocations")
