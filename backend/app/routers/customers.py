from math import ceil

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel
from sqlmodel import Session

from app.core.errors import BadRequestError, NotFoundError
from app.db.session import get_session
from app.schemas.customer import BuyerCreate, BuyerRead, CustomerCreate, CustomerPage, CustomerRead, CustomerUpdate
from app.schemas.payment import CustomerPaymentAllocateCreate, CustomerReceiptCreate
from app.services import auth_service, buyer_service, customer_service, payment_service, pricing_service, sale_service, statement_service

router = APIRouter(prefix="/api/customers", tags=["Customers"])


class ARSummary(BaseModel):
    total_sales: float = 0.0
    total_received: float = 0.0
    total_ar: float = 0.0


@router.get("", response_model=CustomerPage)
def get_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None),
    active_only: bool = Query(True),
    _: dict | None = Depends(auth_service.require_permissions('customer.view')),
    session: Session = Depends(get_session),
):
    rows, total, page, page_size = customer_service.list_customers(session, page, page_size, q, active_only)
    pages = ceil(total / page_size) if page_size else 0
    return {"items": rows, "meta": {"total": int(total), "page": page, "page_size": page_size, "pages": pages}}


@router.post("", response_model=CustomerRead)
def create_customer(payload: CustomerCreate, _: dict | None = Depends(auth_service.require_permissions('customer.manage')), session: Session = Depends(get_session)):
    try:
        return customer_service.create_customer(session, payload)
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.get("/{customer_id}", response_model=CustomerRead)
def get_customer_detail(customer_id: int, _: dict | None = Depends(auth_service.require_permissions('customer.view')), session: Session = Depends(get_session)):
    try:
        return customer_service.get_customer_or_404(session, customer_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)


@router.patch("/{customer_id}", response_model=CustomerRead)
@router.put("/{customer_id}", response_model=CustomerRead)
def update_customer(customer_id: int, payload: CustomerUpdate, _: dict | None = Depends(auth_service.require_permissions('customer.manage')), session: Session = Depends(get_session)):
    try:
        return customer_service.update_customer(session, customer_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.get("/{customer_id}/delete_check")
def customer_delete_check(customer_id: int, _: dict | None = Depends(auth_service.require_permissions('customer.manage')), session: Session = Depends(get_session)):
    try:
        return payment_service.customer_delete_check(session, customer_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)


@router.post("/{customer_id}/delete_records")
def customer_delete_records(customer_id: int, payload: dict, _: dict | None = Depends(auth_service.require_permissions('customer.manage')), session: Session = Depends(get_session)):
    sale_ids = list(payload.get("sale_ids") or [])
    payment_ids = list(payload.get("payment_ids") or [])
    try:
        return payment_service.delete_customer_records(
            session,
            customer_id=customer_id,
            sale_ids=sale_ids,
            payment_ids=payment_ids,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)


@router.delete("/{customer_id}", status_code=204)
def delete_customer(customer_id: int, _: dict | None = Depends(auth_service.require_permissions('customer.manage')), session: Session = Depends(get_session)):
    try:
        customer_service.delete_customer(session, customer_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except ValueError:
        raise HTTPException(status_code=409, detail="客户存在销售单或收款记录，不能删除")
    return Response(status_code=204)


@router.get("/{customer_id}/ar_summary", response_model=ARSummary)
def customer_ar_summary(customer_id: int, _: dict | None = Depends(auth_service.require_permissions('customer.view')), session: Session = Depends(get_session)):
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
    q: str | None = Query(None),
    payment_status: str | None = Query(None),
    sort_by: str = Query("date_desc"),
    _: dict | None = Depends(auth_service.require_permissions('customer.view')),
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
        q=q,
        payment_status=payment_status,
        sort_by=sort_by,
    )
    pages = ceil(total / page_size) if page_size else 0
    meta = {"total": int(total), "page": page, "page_size": page_size, "pages": pages}
    return {"items": items, "meta": meta, "summary": summary}


@router.get("/{customer_id}/sales")
def customer_sales(
    customer_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    _: dict | None = Depends(auth_service.require_permissions('sale.view')),
    session: Session = Depends(get_session),
):
    try:
        customer_service.get_customer_or_404(session, customer_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    items, total, page, page_size = sale_service.list_sales(session, customer_id, page, page_size)
    pages = ceil(total / page_size) if page_size else 0
    return {"items": items, "meta": {"total": int(total), "page": page, "page_size": page_size, "pages": pages}}


@router.get("/{customer_id}/statement/export")
def export_customer_statement(
    customer_id: int,
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    q: str | None = Query(None),
    payment_status: str | None = Query(None),
    sort_by: str = Query("date_desc"),
    format: str = Query("csv"),
    _: dict | None = Depends(auth_service.require_permissions('customer.view')),
    session: Session = Depends(get_session),
):
    if format != "csv":
        raise HTTPException(status_code=400, detail="仅支持 csv")
    content = statement_service.export_statement_csv(
        session,
        customer_id=customer_id,
        start_date=start_date,
        end_date=end_date,
        q=q,
        payment_status=payment_status,
        sort_by=sort_by,
    )
    return PlainTextResponse(content, media_type="text/csv; charset=utf-8")


@router.get("/{customer_id}/open_sales")
def customer_open_sales(
    customer_id: int,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None),
    start_date: str | None = Query(None),
    end_date: str | None = Query(None),
    _: dict | None = Depends(auth_service.require_permissions('sale.view')),
    session: Session = Depends(get_session),
):
    try:
        items, total = payment_service.list_open_sales(
            session,
            customer_id,
            page=page,
            page_size=page_size,
            q=q,
            start_date=start_date,
            end_date=end_date,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    pages = ceil(total / page_size) if page_size else 0
    return {"items": items, "meta": {"total": total, "page": page, "page_size": page_size, "pages": pages}}


@router.post("/{customer_id}/payments/allocate")
def customer_payment_allocate(customer_id: int, payload: CustomerPaymentAllocateCreate, _: dict | None = Depends(auth_service.require_permissions('customer.manage')), session: Session = Depends(get_session)):
    try:
        return payment_service.allocate_to_sales(
            session,
            customer_id=customer_id,
            sale_ids=payload.sale_ids,
            amount=payload.amount,
            method=payload.method,
            paid_at=payload.paid_at,
            note=payload.note,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=exc.message)
