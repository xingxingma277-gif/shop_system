from typing import Optional, List
from pydantic import BaseModel, Field


class PaymentCreate(BaseModel):
    sale_id: int
    amount: float = Field(gt=0)
    method: str = Field(default="transfer")
    paid_at: Optional[str] = None
    note: Optional[str] = Field(default=None, max_length=255)


class PaymentRead(BaseModel):
    id: int
    customer_id: int
    sale_id: int
    pay_type: str
    amount: float
    method: str
    paid_at: str
    note: Optional[str] = None

    model_config = {"from_attributes": True}


class BatchPaymentApplyIn(BaseModel):
    customer_id: int
    sale_ids: List[int] = Field(min_length=1)
    total_amount: float = Field(gt=0)
    method: str = Field(default="transfer")
    paid_at: Optional[str] = None
    note: Optional[str] = Field(default=None, max_length=255)


class BatchPaymentAllocationRow(BaseModel):
    sale_id: int
    applied_amount: float
    after_paid_amount: float
    after_balance: float
    after_status: str


class BatchPaymentApplyOut(BaseModel):
    created_payments: int
    allocations: List[BatchPaymentAllocationRow]
