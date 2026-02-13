from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped
from sqlmodel import SQLModel, Field, Relationship

from app.core.time import utc_now

if TYPE_CHECKING:
    from .sale import Sale
    from .customer_contact import CustomerContact
    from .payment import Payment


class Customer(SQLModel, table=True):
    __tablename__ = "customer"

    id: Optional[int] = Field(default=None, primary_key=True)
    type: str = Field(default="company", max_length=20, index=True)  # company/personal
    name: str = Field(min_length=1, max_length=100, index=True)
    contact_name: str = Field(default="", max_length=100)
    phone: str = Field(default="", max_length=50)
    address: str = Field(default="", max_length=255)
    is_active: bool = Field(default=True, index=True)

    created_at: datetime = Field(default_factory=utc_now, nullable=False)

    sales: Mapped[list["Sale"]] = Relationship(back_populates="customer")
    contacts: Mapped[list["CustomerContact"]] = Relationship(
        back_populates="customer",
        sa_relationship_kwargs={"lazy": "selectin", "cascade": "all, delete-orphan"},
    )
    payments: Mapped[list["Payment"]] = Relationship(
        back_populates="customer",
        sa_relationship_kwargs={"lazy": "selectin"},
    )
