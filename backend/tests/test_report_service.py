from datetime import datetime, timedelta
from sqlmodel import Session, SQLModel, create_engine

from app.models import AuditLog, Customer, Product, Purchase, Sale, Supplier, Warehouse
from app.services import report_service


def _make_session():
    engine = create_engine('sqlite://', echo=False)
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_dashboard_summary_includes_kpis_low_stock_and_audits():
    with _make_session() as session:
        supplier = Supplier(code='SUP-1', name='供应商A')
        warehouse = Warehouse(code='MAIN', name='默认仓')
        low_stock_product = Product(name='低库存商品', stock_quantity=2, stock_warning_threshold=5, standard_price=10, standard_cost=6)
        session.add(supplier)
        session.add(warehouse)
        session.add(low_stock_product)
        session.commit()

        customer = Customer(name='客户A')
        session.add(customer)
        session.commit()

        purchase = Purchase(purchase_no='PO001', supplier_id=supplier.id, warehouse_id=warehouse.id, total_amount=100, paid_amount=30, ap_amount=70, status='CONFIRMED')
        sale = Sale(sale_no='SO001', customer_id=customer.id, total_amount=200, paid_amount=80, ar_amount=120, order_stage='DELIVERY_PENDING', biz_status='NORMAL')
        log = AuditLog(actor_name='管理员', action='CREATE', resource_type='purchase', resource_id=1, detail='创建采购单')
        session.add(purchase)
        session.add(sale)
        session.add(log)
        session.commit()

        data = report_service.dashboard_summary(session)

        assert data['kpis']['purchase_total_amount'] == 100
        assert data['kpis']['sale_total_amount'] == 200
        assert data['kpis']['delivery_pending_count'] == 1
        assert data['ap_aging']['total_ap_amount'] == 70
        assert data['order_stage_breakdown'][0]['order_stage'] == 'DELIVERY_PENDING'
        assert data['order_funnel'][0]['order_stage'] == 'QUOTE'
        assert data['top_ap_suppliers'][0]['supplier_name'] == '供应商A'
        assert data['top_customers'][0]['customer_name'] == '客户A'
        assert data['top_receivable_customers'][0]['customer_name'] == '客户A'
        assert data['ar_aging']['0_30'] == 120
        assert any(alert['code'] == 'LOW_STOCK' for alert in data['alerts'])
        assert len(data['low_stock_items']) == 1
        assert data['low_stock_items'][0]['name'] == '低库存商品'
        assert len(data['recent_audits']) == 1


def test_dashboard_summary_respects_date_range_filters():
    with _make_session() as session:
        supplier = Supplier(code='SUP-2', name='供应商B')
        warehouse = Warehouse(code='WH-2', name='仓库B')
        session.add(supplier)
        session.add(warehouse)
        session.commit()

        customer = Customer(name='客户B')
        session.add(customer)
        session.commit()

        now = datetime.utcnow()
        old_purchase = Purchase(purchase_no='PO-OLD', supplier_id=supplier.id, warehouse_id=warehouse.id, total_amount=50, paid_amount=10, ap_amount=40, status='CONFIRMED', purchase_date=now - timedelta(days=40))
        recent_purchase = Purchase(purchase_no='PO-NEW', supplier_id=supplier.id, warehouse_id=warehouse.id, total_amount=80, paid_amount=20, ap_amount=60, status='CONFIRMED', purchase_date=now - timedelta(days=2))
        old_sale = Sale(sale_no='SO-OLD', customer_id=customer.id, total_amount=90, paid_amount=20, ar_amount=70, order_stage='SALE_CONFIRMED', biz_status='NORMAL', sale_date=now - timedelta(days=45))
        recent_sale = Sale(sale_no='SO-NEW', customer_id=customer.id, total_amount=120, paid_amount=30, ar_amount=90, order_stage='QUOTE', biz_status='NORMAL', sale_date=now - timedelta(days=1))
        old_log = AuditLog(actor_name='旧记录', action='CREATE', resource_type='sale', detail='old', created_at=now - timedelta(days=50))
        new_log = AuditLog(actor_name='新记录', action='CREATE', resource_type='sale', detail='new', created_at=now - timedelta(days=1))
        session.add(old_purchase)
        session.add(recent_purchase)
        session.add(old_sale)
        session.add(recent_sale)
        session.add(old_log)
        session.add(new_log)
        session.commit()

        data = report_service.dashboard_summary(session, now - timedelta(days=7), now)

        assert data['kpis']['purchase_total_amount'] == 80
        assert data['kpis']['sale_total_amount'] == 120
        assert data['kpis']['quote_count'] == 1
        assert data['order_stage_breakdown'][0]['order_stage'] == 'QUOTE'
        assert data['order_funnel'][0]['count'] == 1
        assert data['top_ap_suppliers'][0]['supplier_name'] == '供应商B'
        assert data['top_customers'][0]['customer_name'] == '客户B'
        assert data['top_receivable_customers'][0]['customer_name'] == '客户B'
        assert data['ar_aging']['0_30'] == 90
        assert len(data['recent_audits']) == 1
        assert data['recent_audits'][0]['actor_name'] == '新记录'


def test_dashboard_summary_builds_actionable_alerts():
    with _make_session() as session:
        supplier = Supplier(code='SUP-3', name='供应商C')
        warehouse = Warehouse(code='WH-3', name='仓库C')
        customer = Customer(name='客户C')
        low_stock_product = Product(name='预警商品', stock_quantity=1, stock_warning_threshold=5, standard_price=10, standard_cost=5)
        session.add(supplier)
        session.add(warehouse)
        session.add(customer)
        session.add(low_stock_product)
        session.commit()

        old_purchase = Purchase(purchase_no='PO-ALERT', supplier_id=supplier.id, warehouse_id=warehouse.id, total_amount=200, paid_amount=20, ap_amount=180, status='CONFIRMED', purchase_date=datetime.utcnow() - timedelta(days=120))
        old_sale = Sale(sale_no='SO-ALERT', customer_id=customer.id, total_amount=300, paid_amount=50, ar_amount=250, order_stage='QUOTE', biz_status='NORMAL', sale_date=datetime.utcnow() - timedelta(days=120))
        session.add(old_purchase)
        session.add(old_sale)
        session.commit()

        data = report_service.dashboard_summary(session)
        codes = {alert['code'] for alert in data['alerts']}

        assert 'LOW_STOCK' in codes
        assert 'AP_90_PLUS' in codes
        assert 'AR_90_PLUS' in codes
