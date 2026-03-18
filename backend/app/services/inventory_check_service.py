from datetime import datetime

from sqlmodel import Session, select

from app.core.errors import BadRequestError, NotFoundError
from app.core.time import utc_now
from app.models import InventoryCheck, Product, Warehouse
from app.services.inventory_service import post_txn

_ALLOWED_STATUS = {'DRAFT', 'POSTED'}


def _gen_check_no() -> str:
    return f"IC{utc_now().strftime('%Y%m%d%H%M%S%f')}"


def create_check(session: Session, payload):
    warehouse = session.get(Warehouse, payload.warehouse_id)
    if not warehouse:
        raise NotFoundError('仓库不存在')
    product = session.get(Product, payload.product_id)
    if not product:
        raise NotFoundError('商品不存在')

    book_qty = round(float(product.stock_quantity or 0), 2)
    actual_qty = round(float(payload.actual_qty), 2)
    diff_qty = round(actual_qty - book_qty, 2)
    check = InventoryCheck(
        check_no=_gen_check_no(),
        warehouse_id=payload.warehouse_id,
        product_id=payload.product_id,
        status='DRAFT',
        book_qty=book_qty,
        actual_qty=actual_qty,
        diff_qty=diff_qty,
        note=payload.note,
    )
    session.add(check)
    session.commit()
    return get_check(session, check.id)


def post_check(session: Session, check_id: int):
    check = session.get(InventoryCheck, check_id)
    if not check:
        raise NotFoundError('盘点单不存在')
    if check.status == 'POSTED':
        return get_check(session, check.id)
    if check.status not in _ALLOWED_STATUS:
        raise BadRequestError('盘点单状态不合法')
    if abs(float(check.diff_qty)) < 1e-9:
        check.status = 'POSTED'
        check.posted_at = utc_now()
        session.add(check)
        session.commit()
        return get_check(session, check.id)

    post_txn(
        session,
        product_id=check.product_id,
        warehouse_id=check.warehouse_id,
        change_qty=check.diff_qty,
        biz_type='inventory_check',
        biz_id=check.id,
        note=f'库存盘点{check.check_no}过账',
    )
    check.status = 'POSTED'
    check.posted_at = utc_now()
    session.add(check)
    session.commit()
    return get_check(session, check.id)


def list_checks(session: Session, warehouse_id: int | None, product_id: int | None, status: str | None,
                start_date: datetime | None, end_date: datetime | None):
    stmt = select(InventoryCheck, Warehouse, Product).join(Warehouse, Warehouse.id == InventoryCheck.warehouse_id).join(
        Product, Product.id == InventoryCheck.product_id
    )
    if warehouse_id:
        stmt = stmt.where(InventoryCheck.warehouse_id == warehouse_id)
    if product_id:
        stmt = stmt.where(InventoryCheck.product_id == product_id)
    if status:
        stmt = stmt.where(InventoryCheck.status == status)
    if start_date:
        stmt = stmt.where(InventoryCheck.created_at >= start_date)
    if end_date:
        stmt = stmt.where(InventoryCheck.created_at <= end_date)
    rows = session.exec(stmt.order_by(InventoryCheck.created_at.desc(), InventoryCheck.id.desc())).all()
    return [_to_read(item) for item in rows]


def get_check(session: Session, check_id: int):
    row = session.exec(
        select(InventoryCheck, Warehouse, Product)
        .join(Warehouse, Warehouse.id == InventoryCheck.warehouse_id)
        .join(Product, Product.id == InventoryCheck.product_id)
        .where(InventoryCheck.id == check_id)
    ).first()
    if not row:
        raise NotFoundError('盘点单不存在')
    return _to_read(row)


def _to_read(row):
    check, warehouse, product = row
    return {
        'id': check.id,
        'check_no': check.check_no,
        'warehouse_id': check.warehouse_id,
        'warehouse_name': warehouse.name,
        'product_id': check.product_id,
        'product_name': product.name,
        'status': check.status,
        'book_qty': check.book_qty,
        'actual_qty': check.actual_qty,
        'diff_qty': check.diff_qty,
        'note': check.note,
        'posted_at': check.posted_at,
        'created_at': check.created_at,
    }
