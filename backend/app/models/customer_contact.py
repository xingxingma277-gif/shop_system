from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped
from sqlmodel import SQLModel, Field, Relationship

from app.core.time import utc_now

if TYPE_CHECKING:
    from .customer import Customer
    from .sale import Sale


class CustomerContact(SQLModel, table=True):
    __tablename__ = "customer_contact"

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id", index=True)

    name: str = Field(min_length=1, max_length=100, index=True)
    phone: Optional[str] = Field(default=None, max_length=50)
    role: str = Field(default="维修工", max_length=20, index=True)  # 维修工/老板/会计/采购/其他
    note: Optional[str] = Field(default=None, max_length=255)

    is_active: bool = Field(default=True, index=True)

    # ✅ 关键修复：必须有类型注解
    created_at: datetime = Field(default_factory=utc_now, nullable=False)

    customer: Mapped[Optional["Customer"]] = Relationship(back_populates="contacts")
    sales: Mapped[list["Sale"]] = Relationship(back_populates="contact")

