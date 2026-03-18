from sqlmodel import Session

from app.core.errors import BadRequestError, NotFoundError
from app.models import InventoryTxn, Product


def post_txn(
    session: Session,
    *,
    product_id: int,
    warehouse_id: int | None,
    change_qty: float,
    biz_type: str,
    biz_id: int,
    sale_id: int | None = None,
    note: str | None = None,
) -> InventoryTxn:
    qty = round(float(change_qty), 2)
    if abs(qty) < 1e-9:
        raise BadRequestError('库存变动数量不能为0')

    product = session.get(Product, product_id)
    if not product:
        raise NotFoundError('商品不存在')

    before = round(float(product.stock_quantity or 0), 2)
    after = round(before + qty, 2)
    if after < -1e-6:
        raise BadRequestError('库存不足，禁止负库存')

    product.stock_quantity = after
    session.add(product)

    txn = InventoryTxn(
        product_id=product_id,
        warehouse_id=warehouse_id,
        change_qty=qty,
        after_qty=after,
        biz_type=biz_type,
        biz_id=biz_id,
        sale_id=sale_id,
        note=note,
    )
    session.add(txn)
    session.flush()
    return txn
