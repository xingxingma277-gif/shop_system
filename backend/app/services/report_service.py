from datetime import datetime

from sqlalchemy import func
from sqlmodel import Session, select

from app.models import InventoryTxn, Purchase, Supplier, Warehouse


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
