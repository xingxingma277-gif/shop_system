from sqlmodel import Session, SQLModel, create_engine

from app.models import AuditLog, Product, Purchase, Sale, Supplier, Warehouse
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

        purchase = Purchase(purchase_no='PO001', supplier_id=supplier.id, warehouse_id=warehouse.id, total_amount=100, paid_amount=30, ap_amount=70, status='CONFIRMED')
        sale = Sale(sale_no='SO001', customer_id=1, total_amount=200, paid_amount=80, ar_amount=120, order_stage='DELIVERY_PENDING', biz_status='NORMAL')
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
        assert len(data['low_stock_items']) == 1
        assert data['low_stock_items'][0]['name'] == '低库存商品'
        assert len(data['recent_audits']) == 1
