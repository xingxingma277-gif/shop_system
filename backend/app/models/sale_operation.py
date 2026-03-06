from datetime import datetime
from typing import Optional, TYPE_CHECKING

from sqlalchemy.orm import Mapped
from sqlmodel import SQLModel, Field, Relationship

from app.core.time import utc_now

if TYPE_CHECKING:
    from .sale import Sale


class SaleOperation(SQLModel, table=True):
    __tablename__ = "sale_operation"

    id: Optional[int] = Field(default=None, primary_key=True)
    sale_id: int = Field(foreign_key="sale.id", index=True)
    op_type: str = Field(max_length=30, index=True)
    amount: float = Field(default=0, nullable=False)
    note: Optional[str] = Field(default=None, max_length=500)
    created_at: datetime = Field(default_factory=utc_now, nullable=False, index=True)

    sale: Mapped[Optional["Sale"]] = Relationship(back_populates="operations")
