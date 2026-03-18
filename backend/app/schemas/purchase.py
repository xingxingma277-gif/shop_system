from datetime import datetime
from typing import Optional, List

from sqlmodel import SQLModel, Field


class PurchaseItemCreate(SQLModel):
    product_id: int
    qty: float = Field(gt=0)
    unit_cost: float = Field(ge=0)
    note: Optional[str] = None


class PurchaseCreate(SQLModel):
    purchase_no: Optional[str] = None
    supplier_id: int
    warehouse_id: int
    purchase_date: Optional[datetime] = None
    note: Optional[str] = None
    items: List[PurchaseItemCreate]


class PurchaseReceiveItem(SQLModel):
    purchase_item_id: int
    receive_qty: float = Field(gt=0)


class PurchaseReceivePayload(SQLModel):
    note: Optional[str] = None
    items: List[PurchaseReceiveItem]




class PurchaseReturnItem(SQLModel):
    purchase_item_id: int
    return_qty: float = Field(gt=0)


class PurchaseReturnPayload(SQLModel):
    note: Optional[str] = None
    items: List[PurchaseReturnItem]

class PurchaseItemRead(SQLModel):
    id: int
    product_id: int
    product_name: str
    qty: float
    received_qty: float
    unit_cost: float
    line_total: float
    note: Optional[str] = None


class PurchaseRead(SQLModel):
    id: int
    purchase_no: str
    supplier_id: int
    supplier_name: str
    warehouse_id: int
    warehouse_name: str
    purchase_date: datetime
    status: str
    total_amount: float
    paid_amount: float
    ap_amount: float
    note: Optional[str] = None
    created_at: datetime
    items: List[PurchaseItemRead] = []



class PurchasePage(SQLModel):
    items: List[PurchaseRead]
    total: int
    page: int
    page_size: int
