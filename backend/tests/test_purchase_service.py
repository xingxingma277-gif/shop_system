from datetime import datetime

from sqlmodel import Session, SQLModel, create_engine

from app.models import Product, Supplier, Warehouse
from app.services import purchase_service


def _make_session():
    engine = create_engine('sqlite://', echo=False)
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_purchase_receive_and_return_flow():
    with _make_session() as session:
        supplier = Supplier(code='S001', name='供应商A')
        warehouse = Warehouse(code='W001', name='主仓')
        product = Product(name='机油', sku='OIL-01', stock_quantity=10)
        session.add(supplier)
        session.add(warehouse)
        session.add(product)
        session.commit()
        session.refresh(supplier)
        session.refresh(warehouse)
        session.refresh(product)

        purchase = purchase_service.create_purchase(
            session,
            type('obj', (), {
                'purchase_no': None,
                'supplier_id': supplier.id,
                'warehouse_id': warehouse.id,
                'purchase_date': datetime.utcnow(),
                'note': None,
                'items': [type('obj', (), {'product_id': product.id, 'qty': 5, 'unit_cost': 10, 'note': None})],
            })
        )
        purchase = purchase_service.confirm_purchase(session, purchase['id'])
        purchase = purchase_service.receive_purchase(
            session,
            purchase['id'],
            type('obj', (), {'note': None, 'items': [type('obj', (), {'purchase_item_id': purchase['items'][0]['id'], 'receive_qty': 5})]})
        )
        assert purchase['status'] == 'RECEIVED'
        assert round(session.get(Product, product.id).stock_quantity, 2) == 15

        purchase = purchase_service.return_purchase(
            session,
            purchase['id'],
            type('obj', (), {'note': None, 'items': [type('obj', (), {'purchase_item_id': purchase['items'][0]['id'], 'return_qty': 2})]})
        )
        assert purchase['status'] == 'RECEIVED_PARTIAL'
        assert round(session.get(Product, product.id).stock_quantity, 2) == 13
