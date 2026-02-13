from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel
from sqlmodel import Session

from app.core.errors import NotFoundError
from app.db.session import get_session
from app.schemas.customer import (
    CustomerCreate,
    CustomerPage,
    CustomerProfile,
    CustomerRead,
    CustomerUpdate,
)
from app.services import customer_service, statement_service

router = APIRouter(prefix="/api/customers", tags=["Customers"])


class ARSummary(BaseModel):
    total_sales: float = 0.0
    total_received: float = 0.0
    total_ar: float = 0.0


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
    return {
        "items": rows,
        "meta": {
            "total": int(total),
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
    return customer_service.create_customer(session, payload)


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer_detail(
    customer_id: int,
    session: Session = Depends(get_session),
):
    try:
        return customer_service.get_customer_or_404(session, customer_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)


@router.patch("/{customer_id}", response_model=CustomerRead)
def patch_customer(
    customer_id: int,
    payload: CustomerUpdate,
    session: Session = Depends(get_session),
):
    try:
        return customer_service.update_customer(session, customer_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)


@router.put("/{customer_id}", response_model=CustomerRead)
def put_customer(
    customer_id: int,
    payload: CustomerUpdate,
    session: Session = Depends(get_session),
):
    try:
        return customer_service.update_customer(session, customer_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)


@router.delete("/{customer_id}", status_code=204)
def delete_customer(
    customer_id: int,
    session: Session = Depends(get_session),
):
    try:
        customer_service.delete_customer(session, customer_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except ValueError as exc:
        if str(exc) == "customer_has_related_records":
            raise HTTPException(status_code=409, detail="客户存在销售单或收款记录，不能删除")
        raise
    return Response(status_code=204)


@router.get("/{customer_id}/profile", response_model=CustomerProfile)
def customer_profile(
    customer_id: int,
    session: Session = Depends(get_session),
):
    customer, recent_sales = customer_service.get_customer_profile(
        session, customer_id, recent_limit=10
    )
    return CustomerProfile(
        customer=customer,
        contacts=[],
        ar_summary={"customer_id": customer.id, "total_sales": 0, "total_paid": 0, "total_ar": 0},
        recent_sales=recent_sales,
    )


@router.get("/{customer_id}/ar_summary", response_model=ARSummary)
def customer_ar_summary(
    customer_id: int,
    session: Session = Depends(get_session),
):
    try:
        return customer_service.get_ar_summary(session, customer_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)


@router.get("/{customer_id}/statement")
def customer_statement(
    customer_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    session: Session = Depends(get_session),
):
    try:
        customer_service.get_customer_or_404(session, customer_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)

    summary, items, total = statement_service.get_statement(
        session,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
        page=page,
        page_size=page_size,
    )
    pages = ceil(total / page_size) if page_size else 0
    meta = {
        "total": int(total),
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }
    return {
        "items": items,
        "meta": meta,
        "summary": summary,
        "total": int(total),
        "page": page,
        "page_size": page_size,
    }
