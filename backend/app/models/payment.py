from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped
from sqlmodel import SQLModel, Field, Relationship

from app.core.time import utc_now

if TYPE_CHECKING:
    from .customer import Customer
    from .sale import Sale


class Payment(SQLModel, table=True):
    __tablename__ = "payment"

    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id", index=True)
    sale_id: int = Field(foreign_key="sale.id", index=True)

    amount: float = Field(gt=0)
    method: str = Field(default="转账", max_length=20, index=True)  # 现金/微信/支付宝/转账/其他

    # ✅ 关键修复：必须有类型注解
    paid_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)

    note: Optional[str] = Field(default=None, max_length=255)

    # ✅ 关键修复：必须有类型注解
    created_at: datetime = Field(default_factory=utc_now, nullable=False)

    customer: Mapped[Optional["Customer"]] = Relationship(back_populates="payments")
    sale: Mapped[Optional["Sale"]] = Relationship(back_populates="payments")
