from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.errors import BadRequestError, NotFoundError
from app.db.session import get_session
from app.schemas.payment import BatchPaymentApplyIn, BatchPaymentApplyOut, PaymentCreate, PaymentRead
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
            "pay_type": p.pay_type,
            "amount": p.amount,
            "method": p.method,
            "paid_at": p.paid_at.isoformat(),
            "note": p.note,
        }
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=exc.message)


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
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=exc.message)
