from sqlmodel import Session, SQLModel, create_engine

from app.models import Product, Warehouse
from app.services import inventory_check_service, inventory_transfer_service


def _make_session():
    engine = create_engine('sqlite://', echo=False)
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_inventory_check_and_transfer_are_idempotent_for_post():
    with _make_session() as session:
        wh1 = Warehouse(code='W001', name='主仓')
        wh2 = Warehouse(code='W002', name='分仓')
        product = Product(name='机油', sku='OIL-01', stock_quantity=10)
        session.add(wh1)
        session.add(wh2)
        session.add(product)
        session.commit()
        session.refresh(wh1)
        session.refresh(wh2)
        session.refresh(product)

        check = inventory_check_service.create_check(session, type('obj', (), {'warehouse_id': wh1.id, 'product_id': product.id, 'actual_qty': 12, 'note': None}))
        check = inventory_check_service.post_check(session, check['id'])
        assert check['status'] == 'POSTED'
        check2 = inventory_check_service.post_check(session, check['id'])
        assert check2['status'] == 'POSTED'
        assert round(session.get(Product, product.id).stock_quantity, 2) == 12

        transfer = inventory_transfer_service.create_transfer(session, type('obj', (), {'from_warehouse_id': wh1.id, 'to_warehouse_id': wh2.id, 'product_id': product.id, 'qty': 2, 'note': None}))
        transfer = inventory_transfer_service.post_transfer(session, transfer['id'])
        assert transfer['status'] == 'POSTED'
        transfer2 = inventory_transfer_service.post_transfer(session, transfer['id'])
        assert transfer2['status'] == 'POSTED'
        assert round(session.get(Product, product.id).stock_quantity, 2) == 12
