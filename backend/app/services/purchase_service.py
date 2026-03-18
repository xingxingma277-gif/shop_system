from datetime import datetime

from sqlmodel import Session, select

from app.core.errors import BadRequestError, NotFoundError
from app.core.time import utc_now
from app.models import Product, Purchase, PurchaseItem, Supplier, Warehouse
from app.services.inventory_service import post_txn

_ALLOWED_STATUS = {'DRAFT', 'CONFIRMED', 'RECEIVED_PARTIAL', 'RECEIVED', 'VOIDED'}


def _generate_purchase_no(session: Session, dt: datetime) -> str:
    day = dt.strftime('%Y%m%d')
    prefix = f'PO{day}-'
    last_no = session.exec(select(Purchase.purchase_no).where(Purchase.purchase_no.like(f"{prefix}%")).order_by(Purchase.purchase_no.desc()).limit(1)).first()
    seq = 1
    if last_no and '-' in last_no:
        try:
            seq = int(last_no.split('-')[-1]) + 1
        except Exception:
            seq = 1
    return f"{prefix}{seq:04d}"


def _compute_totals(p: Purchase):
    p.ap_amount = round(max(float(p.total_amount) - float(p.paid_amount), 0), 2)


def create_purchase(session: Session, data):
    supplier = session.get(Supplier, data.supplier_id)
    if not supplier:
        raise NotFoundError('供应商不存在')
    warehouse = session.get(Warehouse, data.warehouse_id)
    if not warehouse:
        raise NotFoundError('仓库不存在')
    if not data.items:
        raise BadRequestError('采购单至少一条商品')

    product_ids = [it.product_id for it in data.items]
    if len(set(product_ids)) != len(product_ids):
        raise BadRequestError('采购单中商品不能重复')

    products = session.exec(select(Product).where(Product.id.in_(product_ids))).all()
    pmap = {p.id: p for p in products}
    missing = [pid for pid in product_ids if pid not in pmap]
    if missing:
        raise BadRequestError(f'商品不存在: {missing}')

    purchase_date = data.purchase_date or utc_now()
    purchase_no = (data.purchase_no or '').strip() or _generate_purchase_no(session, purchase_date)
    purchase = Purchase(
        purchase_no=purchase_no,
        supplier_id=data.supplier_id,
        warehouse_id=data.warehouse_id,
        purchase_date=purchase_date,
        status='DRAFT',
        note=data.note,
        total_amount=0,
        paid_amount=0,
        ap_amount=0,
    )
    session.add(purchase)
    session.flush()

    total = 0.0
    for it in data.items:
        line_total = round(float(it.qty) * float(it.unit_cost), 2)
        total += line_total
        session.add(PurchaseItem(
            purchase_id=purchase.id,
            product_id=it.product_id,
            qty=float(it.qty),
            received_qty=0,
            unit_cost=float(it.unit_cost),
            line_total=line_total,
            note=it.note,
        ))
    purchase.total_amount = round(total, 2)
    _compute_totals(purchase)
    session.add(purchase)
    session.commit()
    return get_purchase(session, purchase.id)


def confirm_purchase(session: Session, purchase_id: int):
    p = session.get(Purchase, purchase_id)
    if not p:
        raise NotFoundError('采购单不存在')
    if p.status != 'DRAFT':
        raise BadRequestError('仅草稿采购单可确认')
    p.status = 'CONFIRMED'
    session.add(p)
    session.commit()
    return get_purchase(session, p.id)


def receive_purchase(session: Session, purchase_id: int, payload):
    p = session.get(Purchase, purchase_id)
    if not p:
        raise NotFoundError('采购单不存在')
    if p.status not in {'CONFIRMED', 'RECEIVED_PARTIAL'}:
        raise BadRequestError('当前状态不可入库')

    item_map = {it.id: it for it in session.exec(select(PurchaseItem).where(PurchaseItem.purchase_id == p.id)).all()}
    if not item_map:
        raise BadRequestError('采购单明细为空')

    for row in payload.items:
        it = item_map.get(row.purchase_item_id)
        if not it:
            raise BadRequestError(f'采购明细不存在: {row.purchase_item_id}')
        left = round(float(it.qty) - float(it.received_qty), 2)
        if row.receive_qty > left + 1e-6:
            raise BadRequestError('入库数量超过未入库数量')

    for row in payload.items:
        it = item_map[row.purchase_item_id]
        qty = round(float(row.receive_qty), 2)
        it.received_qty = round(float(it.received_qty) + qty, 2)
        post_txn(
            session,
            product_id=it.product_id,
            warehouse_id=p.warehouse_id,
            change_qty=qty,
            biz_type='purchase_receive',
            biz_id=p.id,
            note=f'采购单{p.purchase_no}入库',
        )
        session.add(it)

    all_items = list(item_map.values())
    if all(round(float(i.received_qty), 2) + 1e-6 >= round(float(i.qty), 2) for i in all_items):
        p.status = 'RECEIVED'
    else:
        p.status = 'RECEIVED_PARTIAL'
    if payload.note:
        p.note = payload.note
    session.add(p)
    session.commit()
    return get_purchase(session, p.id)


def return_purchase(session: Session, purchase_id: int, payload):
    p = session.get(Purchase, purchase_id)
    if not p:
        raise NotFoundError('采购单不存在')
    if p.status not in {'RECEIVED', 'RECEIVED_PARTIAL'}:
        raise BadRequestError('当前状态不可退货')

    item_map = {it.id: it for it in session.exec(select(PurchaseItem).where(PurchaseItem.purchase_id == p.id)).all()}
    if not item_map:
        raise BadRequestError('采购单明细为空')

    for row in payload.items:
        it = item_map.get(row.purchase_item_id)
        if not it:
            raise BadRequestError(f'采购明细不存在: {row.purchase_item_id}')
        if float(row.return_qty) <= 0:
            raise BadRequestError('退货数量必须大于0')
        if float(row.return_qty) > float(it.received_qty) + 1e-6:
            raise BadRequestError('退货数量超过已入库数量')

    for row in payload.items:
        it = item_map[row.purchase_item_id]
        qty = round(float(row.return_qty), 2)
        it.received_qty = round(float(it.received_qty) - qty, 2)
        post_txn(
            session,
            product_id=it.product_id,
            warehouse_id=p.warehouse_id,
            change_qty=-qty,
            biz_type='purchase_return',
            biz_id=p.id,
            note=f'采购单{p.purchase_no}退货',
        )
        session.add(it)

    all_items = list(item_map.values())
    if all(round(float(i.received_qty), 2) <= 0 for i in all_items):
        p.status = 'CONFIRMED'
    elif all(round(float(i.received_qty), 2) + 1e-6 >= round(float(i.qty), 2) for i in all_items):
        p.status = 'RECEIVED'
    else:
        p.status = 'RECEIVED_PARTIAL'
    if payload.note:
        p.note = payload.note
    session.add(p)
    session.commit()
    return get_purchase(session, p.id)


def list_purchases(session: Session, supplier_id: int | None, status: str | None, page: int = 1, page_size: int = 20):
    from app.services.pagination import paginate

    stmt = select(Purchase)
    if supplier_id:
        stmt = stmt.where(Purchase.supplier_id == supplier_id)
    if status:
        stmt = stmt.where(Purchase.status == status)
    rows, total, page, page_size = paginate(session, stmt.order_by(Purchase.purchase_date.desc(), Purchase.id.desc()), page, page_size)
    return {
        'items': [get_purchase(session, r.id) for r in rows],
        'meta': {'total': int(total), 'page': page, 'page_size': page_size}
    }


def get_purchase(session: Session, purchase_id: int):
    p = session.get(Purchase, purchase_id)
    if not p:
        raise NotFoundError('采购单不存在')
    sup = session.get(Supplier, p.supplier_id)
    wh = session.get(Warehouse, p.warehouse_id)
    items = session.exec(select(PurchaseItem, Product).join(Product, Product.id == PurchaseItem.product_id).where(PurchaseItem.purchase_id == p.id).order_by(PurchaseItem.id.asc())).all()
    return {
        'id': p.id,
        'purchase_no': p.purchase_no,
        'supplier_id': p.supplier_id,
        'supplier_name': sup.name if sup else '-',
        'warehouse_id': p.warehouse_id,
        'warehouse_name': wh.name if wh else '-',
        'purchase_date': p.purchase_date,
        'status': p.status,
        'total_amount': p.total_amount,
        'paid_amount': p.paid_amount,
        'ap_amount': p.ap_amount,
        'note': p.note,
        'created_at': p.created_at,
        'items': [
            {
                'id': it.id,
                'product_id': it.product_id,
                'product_name': prod.name,
                'qty': it.qty,
                'received_qty': it.received_qty,
                'unit_cost': it.unit_cost,
                'line_total': it.line_total,
                'note': it.note,
            }
            for it, prod in items
        ]
    }


def list_inventory_ledger(session: Session, warehouse_id: int | None, product_id: int | None, biz_type: str | None, start_date: datetime | None, end_date: datetime | None):
    stmt = select(InventoryTxn, Product, Warehouse).join(Product, Product.id == InventoryTxn.product_id).join(
        Warehouse, Warehouse.id == InventoryTxn.warehouse_id, isouter=True
    )
    if warehouse_id:
        stmt = stmt.where(InventoryTxn.warehouse_id == warehouse_id)
    if product_id:
        stmt = stmt.where(InventoryTxn.product_id == product_id)
    if biz_type:
        stmt = stmt.where(InventoryTxn.biz_type == biz_type)
    if start_date:
        stmt = stmt.where(InventoryTxn.created_at >= start_date)
    if end_date:
        stmt = stmt.where(InventoryTxn.created_at <= end_date)

    rows = session.exec(stmt.order_by(InventoryTxn.created_at.desc(), InventoryTxn.id.desc())).all()
    return [
        {
            'id': txn.id,
            'created_at': txn.created_at,
            'product_id': txn.product_id,
            'product_name': prod.name,
            'warehouse_id': txn.warehouse_id,
            'warehouse_name': wh.name if wh else '-',
            'change_qty': txn.change_qty,
            'after_qty': txn.after_qty,
            'biz_type': txn.biz_type,
            'biz_id': txn.biz_id,
            'note': txn.note,
        }
        for txn, prod, wh in rows
    ]
