from sqlmodel import Session, SQLModel, create_engine

from app.models import Product, Warehouse
from app.services import inventory_adjustment_service


def _make_session():
    engine = create_engine('sqlite://', echo=False)
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_adjustment_gain_and_loss_constraints():
    with _make_session() as session:
        warehouse = Warehouse(code='W001', name='主仓')
        product = Product(name='机油', sku='OIL-01', stock_quantity=10)
        session.add(warehouse)
        session.add(product)
        session.commit()
        session.refresh(warehouse)
        session.refresh(product)

        gain = inventory_adjustment_service.create_adjustment(
            session,
            type('obj', (), {
                'warehouse_id': warehouse.id,
                'product_id': product.id,
                'adj_type': 'GAIN',
                'qty': 5,
                'reason': '盘盈',
                'note': None,
            })
        )
        assert gain['adj_type'] == 'GAIN'
        p = session.get(Product, product.id)
        assert round(p.stock_quantity, 2) == 15

        loss = inventory_adjustment_service.create_adjustment(
            session,
            type('obj', (), {
                'warehouse_id': warehouse.id,
                'product_id': product.id,
                'adj_type': 'LOSS',
                'qty': 3,
                'reason': '破损',
                'note': None,
            })
        )
        assert loss['adj_type'] == 'LOSS'
        p = session.get(Product, product.id)
        assert round(p.stock_quantity, 2) == 12
