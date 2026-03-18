from datetime import datetime

from sqlalchemy import func
from sqlmodel import Session, select

from app.models import AuditLog, InventoryTxn, Product, Purchase, Sale, Supplier, Warehouse


def ap_summary(session: Session, supplier_id: int | None, start_date: datetime | None, end_date: datetime | None):
    stmt = select(Purchase, Supplier).join(Supplier, Supplier.id == Purchase.supplier_id)
    if supplier_id:
        stmt = stmt.where(Purchase.supplier_id == supplier_id)
    if start_date:
        stmt = stmt.where(Purchase.purchase_date >= start_date)
    if end_date:
        stmt = stmt.where(Purchase.purchase_date <= end_date)

    rows = session.exec(stmt.order_by(Purchase.purchase_date.desc(), Purchase.id.desc())).all()
    items = [
        {
            "purchase_id": p.id,
            "purchase_no": p.purchase_no,
            "supplier_id": p.supplier_id,
            "supplier_name": s.name,
            "purchase_date": p.purchase_date,
            "total_amount": p.total_amount,
            "paid_amount": p.paid_amount,
            "ap_amount": p.ap_amount,
            "status": p.status,
        }
        for p, s in rows
    ]
    summary = {
        "total_purchase_amount": round(sum(float(x["total_amount"]) for x in items), 2),
        "total_paid_amount": round(sum(float(x["paid_amount"]) for x in items), 2),
        "total_ap_amount": round(sum(float(x["ap_amount"]) for x in items), 2),
        "count": len(items),
    }
    return {"items": items, "summary": summary}


def inventory_summary(session: Session, warehouse_id: int | None, product_id: int | None, start_date: datetime | None,
                      end_date: datetime | None):
    stmt = select(InventoryTxn, Warehouse).join(Warehouse, Warehouse.id == InventoryTxn.warehouse_id, isouter=True)
    if warehouse_id:
        stmt = stmt.where(InventoryTxn.warehouse_id == warehouse_id)
    if product_id:
        stmt = stmt.where(InventoryTxn.product_id == product_id)
    if start_date:
        stmt = stmt.where(InventoryTxn.created_at >= start_date)
    if end_date:
        stmt = stmt.where(InventoryTxn.created_at <= end_date)

    rows = session.exec(stmt.order_by(InventoryTxn.created_at.desc(), InventoryTxn.id.desc())).all()
    items = [
        {
            "txn_id": txn.id,
            "warehouse_id": txn.warehouse_id,
            "warehouse_name": wh.name if wh else "-",
            "product_id": txn.product_id,
            "biz_type": txn.biz_type,
            "change_qty": txn.change_qty,
            "after_qty": txn.after_qty,
            "created_at": txn.created_at,
            "note": txn.note,
        }
        for txn, wh in rows
    ]
    summary = {
        "in_qty": round(sum(float(i["change_qty"]) for i in items if float(i["change_qty"]) > 0), 2),
        "out_qty": round(sum(abs(float(i["change_qty"])) for i in items if float(i["change_qty"]) < 0), 2),
        "count": len(items),
    }
    return {"items": items, "summary": summary}



def ap_aging(session: Session, supplier_id: int | None, as_of: datetime | None):
    cutoff = as_of or datetime.utcnow()
    stmt = select(Purchase, Supplier).join(Supplier, Supplier.id == Purchase.supplier_id).where(Purchase.ap_amount > 0)
    if supplier_id:
        stmt = stmt.where(Purchase.supplier_id == supplier_id)
    rows = session.exec(stmt.order_by(Purchase.purchase_date.asc(), Purchase.id.asc())).all()
    buckets = {'0_30': 0.0, '31_60': 0.0, '61_90': 0.0, '90_plus': 0.0}
    items = []
    for purchase, supplier in rows:
        age_days = max((cutoff.date() - purchase.purchase_date.date()).days, 0)
        amount = round(float(purchase.ap_amount), 2)
        if age_days <= 30:
            bucket = '0_30'
        elif age_days <= 60:
            bucket = '31_60'
        elif age_days <= 90:
            bucket = '61_90'
        else:
            bucket = '90_plus'
        buckets[bucket] = round(buckets[bucket] + amount, 2)
        items.append({
            'purchase_id': purchase.id,
            'purchase_no': purchase.purchase_no,
            'supplier_id': purchase.supplier_id,
            'supplier_name': supplier.name,
            'purchase_date': purchase.purchase_date,
            'age_days': age_days,
            'ap_amount': amount,
            'bucket': bucket,
        })
    return {'items': items, 'summary': {'as_of': cutoff, **buckets, 'total_ap_amount': round(sum(x['ap_amount'] for x in items), 2), 'count': len(items)}}



def dashboard_summary(session: Session):
    ap = ap_summary(session, None, None, None)['summary']
    aging = ap_aging(session, None, None)['summary']
    inventory = inventory_summary(session, None, None, None, None)['summary']

    sale_rows = session.exec(select(Sale.total_amount, Sale.paid_amount, Sale.ar_amount, Sale.order_stage).where(Sale.biz_status != 'VOID')).all()
    sale_summary = {
        'sale_count': len(sale_rows),
        'sale_total_amount': round(sum(float(row[0] or 0) for row in sale_rows), 2),
        'sale_paid_amount': round(sum(float(row[1] or 0) for row in sale_rows), 2),
        'sale_ar_amount': round(sum(float(row[2] or 0) for row in sale_rows), 2),
        'quote_count': sum(1 for row in sale_rows if row[3] == 'QUOTE'),
        'delivery_pending_count': sum(1 for row in sale_rows if row[3] in {'DELIVERY_PENDING', 'DELIVERY_CREATED'}),
    }

    low_stock_items = session.exec(
        select(Product).where(
            Product.is_active == True,
            Product.stock_warning_threshold > 0,
            Product.stock_quantity <= Product.stock_warning_threshold,
        ).order_by(Product.stock_quantity.asc(), Product.id.asc()).limit(8)
    ).all()

    recent_audits = session.exec(
        select(AuditLog).order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(8)
    ).all()

    return {
        'kpis': {
            'purchase_total_amount': ap.get('total_purchase_amount', 0),
            'purchase_paid_amount': ap.get('total_paid_amount', 0),
            'purchase_ap_amount': ap.get('total_ap_amount', 0),
            'inventory_in_qty': inventory.get('in_qty', 0),
            'inventory_out_qty': inventory.get('out_qty', 0),
            'inventory_txn_count': inventory.get('count', 0),
            **sale_summary,
        },
        'ap_aging': aging,
        'low_stock_items': [
            {
                'id': item.id,
                'name': item.name,
                'sku': item.sku,
                'stock_quantity': item.stock_quantity,
                'stock_warning_threshold': item.stock_warning_threshold,
            }
            for item in low_stock_items
        ],
        'recent_audits': [
            {
                'id': log.id,
                'actor_name': log.actor_name,
                'action': log.action,
                'resource_type': log.resource_type,
                'resource_id': log.resource_id,
                'detail': log.detail,
                'created_at': log.created_at,
            }
            for log in recent_audits
        ],
    }
