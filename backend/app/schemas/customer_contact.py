from typing import Optional
from pydantic import BaseModel, Field


class CustomerContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=50)
    role: str = Field(default="维修工", max_length=20)
    note: Optional[str] = Field(default=None, max_length=255)


class CustomerContactUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    phone: Optional[str] = Field(default=None, max_length=50)
    role: Optional[str] = Field(default=None, max_length=20)
    note: Optional[str] = Field(default=None, max_length=255)
    is_active: Optional[bool] = None


class CustomerContactRead(BaseModel):
    id: int
    customer_id: int
    name: str
    phone: Optional[str] = None
    role: str
    note: Optional[str] = None
    is_active: bool

    model_config = {"from_attributes": True}
