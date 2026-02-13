from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlmodel import Session

from app.core.errors import NotFoundError
from app.db.session import get_session
from app.schemas.product import ProductCreate, ProductPage, ProductRead, ProductUpdate
from app.services import product_service

router = APIRouter(prefix="/api/products", tags=["Products"])


@router.get("", response_model=ProductPage)
def get_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, description="可选：商品名或SKU模糊搜索"),
    active_only: bool = Query(True, description="默认只返回启用商品"),
    session: Session = Depends(get_session),
):
    rows, total, page, page_size = product_service.list_products(session, page, page_size, q, active_only)
    return ProductPage(items=rows, total=int(total), page=page, page_size=page_size)


@router.post("", response_model=ProductRead)
def create_product(
    payload: ProductCreate,
    session: Session = Depends(get_session),
):
    return product_service.create_product(session, payload)


@router.patch("/{product_id}", response_model=ProductRead)
def patch_product(
    product_id: int,
    payload: ProductUpdate,
    session: Session = Depends(get_session),
):
    try:
        return product_service.update_product(session, product_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)


@router.put("/{product_id}", response_model=ProductRead)
def put_product(
    product_id: int,
    payload: ProductUpdate,
    session: Session = Depends(get_session),
):
    try:
        return product_service.update_product(session, product_id, payload)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)


@router.delete("/{product_id}", status_code=204)
def delete_product(
    product_id: int,
    session: Session = Depends(get_session),
):
    try:
        product_service.delete_product(session, product_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
    except ValueError as exc:
        if str(exc) == "product_has_related_records":
            raise HTTPException(status_code=409, detail="商品已被销售单引用，不能删除")
        raise
    return Response(status_code=204)


@router.post("/{product_id}/toggle_active", response_model=ProductRead)
def toggle_active(
    product_id: int,
    session: Session = Depends(get_session),
):
    try:
        return product_service.toggle_product_active(session, product_id)
    except NotFoundError as exc:
        raise HTTPException(status_code=404, detail=exc.message)
