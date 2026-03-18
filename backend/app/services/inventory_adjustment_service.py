from datetime import datetime

from sqlmodel import Session, select

from app.core.errors import BadRequestError, NotFoundError
from app.core.time import utc_now
from app.models import InventoryAdjustment, InventoryTxn, Product, Warehouse


def _gen_adj_no() -> str:
    return f"ADJ{utc_now().strftime('%Y%m%d%H%M%S%f')}"


def create_adjustment(session: Session, payload):
    warehouse = session.get(Warehouse, payload.warehouse_id)
    if not warehouse:
        raise NotFoundError('仓库不存在')
    product = session.get(Product, payload.product_id)
    if not product:
        raise NotFoundError('商品不存在')

    qty = round(float(payload.qty), 2)
    if qty <= 0:
        raise BadRequestError('调整数量必须大于0')

    before = round(float(product.stock_quantity or 0), 2)
    delta = qty if payload.adj_type == 'GAIN' else -qty
    after = round(before + delta, 2)

    if payload.adj_type not in {'GAIN', 'LOSS'}:
        raise BadRequestError('调整类型不合法')
    if after < 0:
        raise BadRequestError('库存不足，无法报损')

    adj = InventoryAdjustment(
        adj_no=_gen_adj_no(),
        warehouse_id=payload.warehouse_id,
        product_id=payload.product_id,
        adj_type=payload.adj_type,
        qty=qty,
        reason=payload.reason,
        note=payload.note,
    )
    session.add(adj)
    session.flush()

    product.stock_quantity = after
    session.add(product)

    session.add(InventoryTxn(
        product_id=product.id,
        warehouse_id=warehouse.id,
        change_qty=delta,
        after_qty=after,
        biz_type='inventory_adjustment',
        biz_id=adj.id,
        note=f'库存调整[{payload.adj_type}] {payload.reason or ""}'.strip(),
    ))

    session.commit()
    return get_adjustment(session, adj.id)


def list_adjustments(session: Session, warehouse_id: int | None, product_id: int | None, adj_type: str | None,
                     start_date: datetime | None, end_date: datetime | None):
    stmt = select(InventoryAdjustment, Warehouse, Product) \
        .join(Warehouse, Warehouse.id == InventoryAdjustment.warehouse_id) \
        .join(Product, Product.id == InventoryAdjustment.product_id)

    if warehouse_id:
        stmt = stmt.where(InventoryAdjustment.warehouse_id == warehouse_id)
    if product_id:
        stmt = stmt.where(InventoryAdjustment.product_id == product_id)
    if adj_type:
        stmt = stmt.where(InventoryAdjustment.adj_type == adj_type)
    if start_date:
        stmt = stmt.where(InventoryAdjustment.created_at >= start_date)
    if end_date:
        stmt = stmt.where(InventoryAdjustment.created_at <= end_date)

    rows = session.exec(stmt.order_by(InventoryAdjustment.created_at.desc(), InventoryAdjustment.id.desc())).all()
    return [
        {
            'id': a.id,
            'adj_no': a.adj_no,
            'warehouse_id': a.warehouse_id,
            'warehouse_name': w.name,
            'product_id': a.product_id,
            'product_name': p.name,
            'adj_type': a.adj_type,
            'qty': a.qty,
            'reason': a.reason,
            'note': a.note,
            'created_at': a.created_at,
        }
        for a, w, p in rows
    ]


def get_adjustment(session: Session, adjustment_id: int):
    row = session.exec(
        select(InventoryAdjustment, Warehouse, Product)
        .join(Warehouse, Warehouse.id == InventoryAdjustment.warehouse_id)
        .join(Product, Product.id == InventoryAdjustment.product_id)
        .where(InventoryAdjustment.id == adjustment_id)
    ).first()
    if not row:
        raise NotFoundError('调整记录不存在')
    a, w, p = row
    return {
        'id': a.id,
        'adj_no': a.adj_no,
        'warehouse_id': a.warehouse_id,
        'warehouse_name': w.name,
        'product_id': a.product_id,
        'product_name': p.name,
        'adj_type': a.adj_type,
        'qty': a.qty,
        'reason': a.reason,
        'note': a.note,
        'created_at': a.created_at,
    }
