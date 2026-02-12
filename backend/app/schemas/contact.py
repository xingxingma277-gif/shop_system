from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel


class CustomerContactBase(SQLModel):
    customer_id: int
    name: str
    phone: Optional[str] = None
    remark: Optional[str] = None
    is_active: bool = True


class CustomerContactCreate(CustomerContactBase):
    pass


class CustomerContactUpdate(SQLModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    remark: Optional[str] = None
    is_active: Optional[bool] = None


class CustomerContactRead(CustomerContactBase):
    id: int
    created_at: datetime
