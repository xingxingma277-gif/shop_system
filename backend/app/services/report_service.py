from datetime import datetime

from sqlalchemy import func
from sqlmodel import Session, select

from app.models import AuditLog, Customer, InventoryTxn, Product, Purchase, Sale, Supplier, Warehouse


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



def dashboard_summary(session: Session, start_date: datetime | None = None, end_date: datetime | None = None):
    ap = ap_summary(session, None, start_date, end_date)['summary']
    aging = ap_aging(session, None, end_date or start_date or None)['summary']
    inventory = inventory_summary(session, None, None, start_date, end_date)['summary']

    sale_stmt = select(Sale.total_amount, Sale.paid_amount, Sale.ar_amount, Sale.order_stage).where(Sale.biz_status != 'VOID')
    if start_date:
        sale_stmt = sale_stmt.where(Sale.sale_date >= start_date)
    if end_date:
        sale_stmt = sale_stmt.where(Sale.sale_date <= end_date)
    sale_rows = session.exec(sale_stmt).all()
    sale_summary = {
        'sale_count': len(sale_rows),
        'sale_total_amount': round(sum(float(row[0] or 0) for row in sale_rows), 2),
        'sale_paid_amount': round(sum(float(row[1] or 0) for row in sale_rows), 2),
        'sale_ar_amount': round(sum(float(row[2] or 0) for row in sale_rows), 2),
        'quote_count': sum(1 for row in sale_rows if row[3] == 'QUOTE'),
        'delivery_pending_count': sum(1 for row in sale_rows if row[3] in {'DELIVERY_PENDING', 'DELIVERY_CREATED'}),
    }
    stage_breakdown = {}
    funnel_config = [
        ('QUOTE', '报价中'),
        ('SALE_CONFIRMED', '已转销售'),
        ('DELIVERY_CREATED', '已生成送货单'),
        ('DELIVERED', '已送达'),
        ('COMPLETED', '已完成'),
    ]
    for total_amount, paid_amount, ar_amount, order_stage in sale_rows:
        stage = order_stage or 'UNKNOWN'
        item = stage_breakdown.setdefault(stage, {
            'order_stage': stage,
            'count': 0,
            'total_amount': 0.0,
            'paid_amount': 0.0,
            'ar_amount': 0.0,
        })
        item['count'] += 1
        item['total_amount'] = round(item['total_amount'] + float(total_amount or 0), 2)
        item['paid_amount'] = round(item['paid_amount'] + float(paid_amount or 0), 2)
        item['ar_amount'] = round(item['ar_amount'] + float(ar_amount or 0), 2)

    supplier_stmt = select(Purchase, Supplier).join(Supplier, Supplier.id == Purchase.supplier_id).where(Purchase.ap_amount > 0)
    if start_date:
        supplier_stmt = supplier_stmt.where(Purchase.purchase_date >= start_date)
    if end_date:
        supplier_stmt = supplier_stmt.where(Purchase.purchase_date <= end_date)
    supplier_rows = session.exec(supplier_stmt).all()
    supplier_ap_map = {}
    for purchase, supplier in supplier_rows:
        item = supplier_ap_map.setdefault(supplier.id, {
            'supplier_id': supplier.id,
            'supplier_name': supplier.name,
            'purchase_count': 0,
            'ap_amount': 0.0,
            'paid_amount': 0.0,
        })
        item['purchase_count'] += 1
        item['ap_amount'] = round(item['ap_amount'] + float(purchase.ap_amount or 0), 2)
        item['paid_amount'] = round(item['paid_amount'] + float(purchase.paid_amount or 0), 2)
    top_ap_suppliers = sorted(supplier_ap_map.values(), key=lambda row: (-row['ap_amount'], row['supplier_id']))[:5]

    customer_stmt = select(Sale, Customer).join(Customer, Customer.id == Sale.customer_id).where(Sale.biz_status != 'VOID')
    if start_date:
        customer_stmt = customer_stmt.where(Sale.sale_date >= start_date)
    if end_date:
        customer_stmt = customer_stmt.where(Sale.sale_date <= end_date)
    customer_rows = session.exec(customer_stmt).all()
    customer_rank_map = {}
    ar_aging = {'0_30': 0.0, '31_60': 0.0, '61_90': 0.0, '90_plus': 0.0}
    aging_cutoff = end_date or start_date or datetime.utcnow()
    for sale, customer in customer_rows:
        item = customer_rank_map.setdefault(customer.id, {
            'customer_id': customer.id,
            'customer_name': customer.name,
            'sale_count': 0,
            'total_amount': 0.0,
            'paid_amount': 0.0,
            'ar_amount': 0.0,
        })
        item['sale_count'] += 1
        item['total_amount'] = round(item['total_amount'] + float(sale.total_amount or 0), 2)
        item['paid_amount'] = round(item['paid_amount'] + float(sale.paid_amount or 0), 2)
        item['ar_amount'] = round(item['ar_amount'] + float(sale.ar_amount or 0), 2)
        if float(sale.ar_amount or 0) > 0:
            age_days = max((aging_cutoff.date() - sale.sale_date.date()).days, 0)
            bucket = '0_30' if age_days <= 30 else '31_60' if age_days <= 60 else '61_90' if age_days <= 90 else '90_plus'
            ar_aging[bucket] = round(ar_aging[bucket] + float(sale.ar_amount or 0), 2)
    top_customers = sorted(customer_rank_map.values(), key=lambda row: (-row['total_amount'], row['customer_id']))[:5]
    top_receivable_customers = sorted((row for row in customer_rank_map.values() if row['ar_amount'] > 0), key=lambda row: (-row['ar_amount'], row['customer_id']))[:5]

    funnel = []
    previous_count = None
    for stage_code, stage_label in funnel_config:
        row = stage_breakdown.get(stage_code, {'count': 0, 'total_amount': 0.0, 'paid_amount': 0.0, 'ar_amount': 0.0})
        count = int(row.get('count', 0) or 0)
        conversion_rate = None
        if previous_count and previous_count > 0:
            conversion_rate = round(count / previous_count * 100, 2)
        funnel.append({
            'order_stage': stage_code,
            'label': stage_label,
            'count': count,
            'total_amount': row.get('total_amount', 0.0),
            'paid_amount': row.get('paid_amount', 0.0),
            'ar_amount': row.get('ar_amount', 0.0),
            'conversion_rate': conversion_rate,
        })
        previous_count = count

    low_stock_items = session.exec(
        select(Product).where(
            Product.is_active == True,
            Product.stock_warning_threshold > 0,
            Product.stock_quantity <= Product.stock_warning_threshold,
        ).order_by(Product.stock_quantity.asc(), Product.id.asc()).limit(8)
    ).all()

    audit_stmt = select(AuditLog)
    if start_date:
        audit_stmt = audit_stmt.where(AuditLog.created_at >= start_date)
    if end_date:
        audit_stmt = audit_stmt.where(AuditLog.created_at <= end_date)
    recent_audits = session.exec(
        audit_stmt.order_by(AuditLog.created_at.desc(), AuditLog.id.desc()).limit(8)
    ).all()

    alerts = []
    if low_stock_items:
        alerts.append({
            'level': 'warning',
            'code': 'LOW_STOCK',
            'title': '低库存预警',
            'message': f'当前有 {len(low_stock_items)} 个商品触发低库存预警。',
            'action_label': '查看库存台账',
            'action_path': '/inventory-ledger',
        })
    if float(aging.get('90_plus', 0) or 0) > 0:
        alerts.append({
            'level': 'danger',
            'code': 'AP_90_PLUS',
            'title': '应付账龄超 90 天',
            'message': f"90 天以上应付余额为 {aging.get('90_plus', 0)}。",
            'action_label': '查看应付账龄',
            'action_path': '/reports',
            'action_query': {'tab': 'aging'},
        })
    if float(ar_aging.get('90_plus', 0) or 0) > 0:
        alerts.append({
            'level': 'danger',
            'code': 'AR_90_PLUS',
            'title': '应收账龄超 90 天',
            'message': f"90 天以上应收余额为 {ar_aging.get('90_plus', 0)}。",
            'action_label': '查看未收订单',
            'action_path': '/transactions',
            'action_query': {'tab': 'sales', 'status': 'unpaid'},
        })
    for idx, item in enumerate(funnel[1:], start=1):
        prev = funnel[idx - 1]
        if prev['count'] >= 3 and item['conversion_rate'] is not None and item['conversion_rate'] < 60:
            alerts.append({
                'level': 'warning',
                'code': f"FUNNEL_{prev['order_stage']}_{item['order_stage']}",
                'title': '订单流程转化偏低',
                'message': f"{prev['label']}→{item['label']} 转化率仅 {item['conversion_rate']}%。",
                'action_label': '查看订单走势',
                'action_path': '/dashboard',
            })

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
        'order_stage_breakdown': sorted(stage_breakdown.values(), key=lambda row: (-row['count'], row['order_stage'])),
        'order_funnel': funnel,
        'top_ap_suppliers': top_ap_suppliers,
        'top_customers': top_customers,
        'ar_aging': ar_aging,
        'top_receivable_customers': top_receivable_customers,
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
        'alerts': alerts,
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
