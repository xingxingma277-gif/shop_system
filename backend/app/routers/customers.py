from math import ceil

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.customer import (
    CustomerCreate,
    CustomerRead,
    CustomerUpdate,
    CustomerPage,
    CustomerProfile,
)
from app.services import customer_service

router = APIRouter(prefix="/api/customers", tags=["Customers"])


class ARSummary(BaseModel):
    total_sales: float = 0.0     # 累计销售
    total_received: float = 0.0  # 累计已收
    total_ar: float = 0.0        # 累计欠款


@router.get("", response_model=CustomerPage)
def get_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, description="可选：客户名模糊搜索"),
    active_only: bool = Query(True, description="默认只返回启用客户"),
    session: Session = Depends(get_session),
):
    rows, total, page, page_size = customer_service.list_customers(
        session, page, page_size, q, active_only
    )

    pages = ceil(total / page_size) if page_size else 0

    # 关键修复：CustomerPage 需要 meta 字段（否则响应校验 500）
    return {
        "items": rows,
        "meta": {
            "total": total,
            "page": page,
            "page_size": page_size,
            "pages": pages,
        },
    }


@router.post("", response_model=CustomerRead)
def create_customer(
    payload: CustomerCreate,
    session: Session = Depends(get_session),
):
    # 保持原有逻辑：不要用 payload= 关键字（你之前就是这里报过错）
    return customer_service.create_customer(session, payload)


@router.patch("/{customer_id}", response_model=CustomerRead)
def patch_customer(
    customer_id: int,
    payload: CustomerUpdate,
    session: Session = Depends(get_session),
):
    return customer_service.update_customer(session, customer_id, payload)


@router.get("/{customer_id}/profile", response_model=CustomerProfile)
def customer_profile(
    customer_id: int,
    session: Session = Depends(get_session),
):
    customer, recent_sales = customer_service.get_customer_profile(
        session, customer_id, recent_limit=10
    )
    return CustomerProfile(customer=customer, recent_sales=recent_sales)


@router.get("/{customer_id}/ar_summary", response_model=ARSummary)
def customer_ar_summary(
    customer_id: int,
    session: Session = Depends(get_session),
):
    """
    前端客户详情页会请求这个接口：
      GET /api/customers/{id}/ar_summary

    - 如果 service 已经实现了函数，就用 service 的结果
    - 如果 service 没实现，先返回 0，保证不 404、不阻塞页面渲染
    """
    if hasattr(customer_service, "get_ar_summary"):
        return customer_service.get_ar_summary(session, customer_id)

    # fallback：避免 404 / 500 影响前端页面
    return ARSummary()
