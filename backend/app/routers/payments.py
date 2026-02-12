from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.db.session import get_session
from app.schemas.pagination import Page
from app.schemas.payment import PaymentCreate, PaymentRead, BatchPaymentApplyIn, BatchPaymentApplyOut
from app.services import payment_service

router = APIRouter(prefix="/api", tags=["Payments"])


@router.post("/payments", response_model=PaymentRead)
def create_payment(payload: PaymentCreate, session: Session = Depends(get_session)):
    try:
        p = payment_service.create_payment(
            session,
            sale_id=payload.sale_id,
            amount=payload.amount,
            method=payload.method,
            paid_at=payload.paid_at,
            note=payload.note,
        )
        return {
            "id": p.id,
            "customer_id": p.customer_id,
            "sale_id": p.sale_id,
            "amount": p.amount,
            "method": p.method,
            "paid_at": p.paid_at.isoformat(),
            "note": p.note,
        }
    except ValueError as e:
        msg = str(e)
        mapping = {
            "sale_not_found": ("单据不存在", 404),
            "invalid_payment_method": ("付款方式不合法", 400),
            "amount_exceeds_balance": ("收款金额不能超过该单未付金额", 400),
        }
        if msg in mapping:
            detail, code = mapping[msg]
            raise HTTPException(status_code=code, detail=detail)
        raise


@router.get("/payments", response_model=Page[PaymentRead])
def list_payments(
    customer_id: int | None = None,
    sale_id: int | None = None,
    page: int = 1,
    page_size: int = 20,
    session: Session = Depends(get_session),
):
    items, total = payment_service.list_payments(session, customer_id, sale_id, page, page_size)
    # paid_at 转 string
    out_items = [
        {
            "id": p.id,
            "customer_id": p.customer_id,
            "sale_id": p.sale_id,
            "amount": p.amount,
            "method": p.method,
            "paid_at": p.paid_at.isoformat(),
            "note": p.note,
        }
        for p in items
    ]
    return {"items": out_items, "total": total, "page": page, "page_size": page_size}


@router.post("/payments/batch_apply", response_model=BatchPaymentApplyOut)
def batch_apply(payload: BatchPaymentApplyIn, session: Session = Depends(get_session)):
    try:
        created, allocations = payment_service.batch_apply(
            session,
            customer_id=payload.customer_id,
            sale_ids=payload.sale_ids,
            total_amount=payload.total_amount,
            method=payload.method,
            paid_at=payload.paid_at,
            note=payload.note,
        )
        return {"created_payments": created, "allocations": allocations}
    except ValueError as e:
        msg = str(e)
        mapping = {
            "customer_not_found": ("客户不存在", 404),
            "invalid_payment_method": ("付款方式不合法", 400),
            "no_sales_found": ("未找到可结算单据", 404),
            "all_sales_already_paid": ("所选单据均已结清", 400),
            "amount_exceeds_total_balance": ("收款金额超过所选单据总欠款", 400),
        }
        if msg in mapping:
            detail, code = mapping[msg]
            raise HTTPException(status_code=code, detail=detail)
        raise
