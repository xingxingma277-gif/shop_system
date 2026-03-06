from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.core.config import SALE_EXCEL_TEMPLATE_PATH
from app.core.errors import BadRequestError, NotFoundError
from app.db.session import get_session
from app.schemas.sale import (
    SaleCreate,
    SaleOperationCreate,
    SalePage,
    SalePaymentCreate,
    SalePaymentSubmitResponse,
    SaleRead,
    SaleReverseSettlementCreate,
    SaleSettlementUpdate,
)
from app.services import payment_service, sale_export_service, sale_service, settlement_service

router = APIRouter(prefix="/api/sales", tags=["Sales"])


@router.get('/next_no')
def get_next_no(session: Session = Depends(get_session)):
    return {'sale_no': sale_service.next_sale_no(session)}


@router.post("", response_model=SaleRead)
def create_sale(payload: SaleCreate, session: Session = Depends(get_session)):
    try:
        return sale_service.create_sale(session, payload)
    except (NotFoundError, BadRequestError) as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.get("", response_model=SalePage)
def get_sales(
    customer_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session: Session = Depends(get_session),
):
    items, total, page, page_size = sale_service.list_sales(session, customer_id, page, page_size)
    return SalePage(items=items, total=int(total), page=page, page_size=page_size)


@router.get("/{sale_id}", response_model=SaleRead)
def get_sale_detail(sale_id: int, session: Session = Depends(get_session)):
    try:
        return sale_service.get_sale(session, sale_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)


@router.post("/{sale_id}/settlement", response_model=SaleRead)
def submit_settlement(sale_id: int, payload: SaleSettlementUpdate, session: Session = Depends(get_session)):
    try:
        return sale_service.update_settlement(
            session,
            sale_id=sale_id,
            settlement_status=payload.settlement_status,
            paid_amount=payload.paid_amount,
            payment_method=payload.payment_method,
            payment_note=payload.payment_note,
        )
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.post("/{sale_id}/payments", response_model=SalePaymentSubmitResponse)
def submit_sale_payment(sale_id: int, payload: SalePaymentCreate, session: Session = Depends(get_session)):
    try:
        sale, payment = payment_service.submit_sale_payment(
            session,
            sale_id=sale_id,
            pay_type=payload.pay_type,
            method=payload.method,
            amount=payload.amount,
            note=payload.note,
        )
        return {"sale": sale, "payment": payment}
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.get('/{sale_id}/payment_records')
def sale_payment_records(sale_id: int, session: Session = Depends(get_session)):
    try:
        items = payment_service.list_sale_payments(session, sale_id)
        return {'items': items}
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)


@router.post("/{sale_id}/void", response_model=SaleRead)
def void_sale(sale_id: int, payload: SaleOperationCreate, session: Session = Depends(get_session)):
    try:
        settlement_service.mark_sale_void(session, sale_id=sale_id, note=payload.note)
        return sale_service.get_sale(session, sale_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.post("/{sale_id}/reverse_settlement", response_model=SaleRead)
def reverse_sale_settlement(sale_id: int, payload: SaleReverseSettlementCreate, session: Session = Depends(get_session)):
    try:
        settlement_service.reverse_settlement(session, sale_id=sale_id, amount=payload.amount, note=payload.note)
        return sale_service.get_sale(session, sale_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=exc.message)


@router.get("/{sale_id}/operations")
def get_sale_operations(sale_id: int, session: Session = Depends(get_session)):
    try:
        return {"items": settlement_service.sale_operations(session, sale_id=sale_id)}
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)


@router.get("/{sale_id}/export_excel")
def export_sale_excel(sale_id: int, session: Session = Depends(get_session)):
    try:
        content, media_type, ext = sale_export_service.export_sale_excel(session, sale_id=sale_id, template_path=SALE_EXCEL_TEMPLATE_PATH)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)

    file_name = f"sales_list_{sale_id}.{ext}"
    return StreamingResponse(
        BytesIO(content),
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={file_name}"},
    )


@router.post("/{sale_id}/return", response_model=SaleRead)
def return_sale(sale_id: int, payload: SaleOperationCreate, session: Session = Depends(get_session)):
    try:
        settlement_service.return_sale_stock(session, sale_id=sale_id, note=payload.note)
        return sale_service.get_sale(session, sale_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except BadRequestError as exc:
        raise HTTPException(status_code=400, detail=exc.message)
