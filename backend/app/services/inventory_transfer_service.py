from datetime import datetime

from sqlmodel import Session, select

from app.core.errors import BadRequestError, NotFoundError
from app.core.time import utc_now
from app.models import InventoryTransfer, Product, Warehouse
from app.services.inventory_service import post_txn

_ALLOWED_STATUS = {'DRAFT', 'POSTED'}


def _gen_transfer_no() -> str:
    return f"TR{utc_now().strftime('%Y%m%d%H%M%S%f')}"


def create_transfer(session: Session, payload):
    from_wh = session.get(Warehouse, payload.from_warehouse_id)
    to_wh = session.get(Warehouse, payload.to_warehouse_id)
    if not from_wh or not to_wh:
        raise NotFoundError('仓库不存在')
    if from_wh.id == to_wh.id:
        raise BadRequestError('调出仓库和调入仓库不能相同')
    product = session.get(Product, payload.product_id)
    if not product:
        raise NotFoundError('商品不存在')
    qty = round(float(payload.qty), 2)
    if qty <= 0:
        raise BadRequestError('调拨数量必须大于0')

    transfer = InventoryTransfer(
        transfer_no=_gen_transfer_no(),
        from_warehouse_id=from_wh.id,
        to_warehouse_id=to_wh.id,
        product_id=product.id,
        qty=qty,
        status='DRAFT',
        note=payload.note,
    )
    session.add(transfer)
    session.commit()
    return get_transfer(session, transfer.id)


def post_transfer(session: Session, transfer_id: int):
    transfer = session.get(InventoryTransfer, transfer_id)
    if not transfer:
        raise NotFoundError('调拨单不存在')
    if transfer.status == 'POSTED':
        return get_transfer(session, transfer.id)
    if transfer.status not in _ALLOWED_STATUS:
        raise BadRequestError('调拨单状态不合法')

    post_txn(
        session,
        product_id=transfer.product_id,
        warehouse_id=transfer.from_warehouse_id,
        change_qty=-float(transfer.qty),
        biz_type='inventory_transfer_out',
        biz_id=transfer.id,
        note=f'库存调拨{transfer.transfer_no}调出',
    )
    post_txn(
        session,
        product_id=transfer.product_id,
        warehouse_id=transfer.to_warehouse_id,
        change_qty=float(transfer.qty),
        biz_type='inventory_transfer_in',
        biz_id=transfer.id,
        note=f'库存调拨{transfer.transfer_no}调入',
    )
    transfer.status = 'POSTED'
    transfer.posted_at = utc_now()
    session.add(transfer)
    session.commit()
    return get_transfer(session, transfer.id)


def list_transfers(session: Session, warehouse_id: int | None, product_id: int | None, status: str | None,
                   start_date: datetime | None, end_date: datetime | None):
    rows = session.exec(select(InventoryTransfer).order_by(InventoryTransfer.created_at.desc(), InventoryTransfer.id.desc())).all()
    items = []
    for transfer in rows:
        if warehouse_id and warehouse_id not in {transfer.from_warehouse_id, transfer.to_warehouse_id}:
            continue
        if product_id and transfer.product_id != product_id:
            continue
        if status and transfer.status != status:
            continue
        if start_date and transfer.created_at < start_date:
            continue
        if end_date and transfer.created_at > end_date:
            continue
        items.append(get_transfer(session, transfer.id))
    return items


def get_transfer(session: Session, transfer_id: int):
    transfer = session.get(InventoryTransfer, transfer_id)
    if not transfer:
        raise NotFoundError('调拨单不存在')
    from_wh = session.get(Warehouse, transfer.from_warehouse_id)
    to_wh = session.get(Warehouse, transfer.to_warehouse_id)
    product = session.get(Product, transfer.product_id)
    return {
        'id': transfer.id,
        'transfer_no': transfer.transfer_no,
        'from_warehouse_id': transfer.from_warehouse_id,
        'from_warehouse_name': from_wh.name if from_wh else '-',
        'to_warehouse_id': transfer.to_warehouse_id,
        'to_warehouse_name': to_wh.name if to_wh else '-',
        'product_id': transfer.product_id,
        'product_name': product.name if product else '-',
        'qty': transfer.qty,
        'status': transfer.status,
        'note': transfer.note,
        'posted_at': transfer.posted_at,
        'created_at': transfer.created_at,
    }
