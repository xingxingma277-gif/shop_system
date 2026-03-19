from sqlmodel import Session, SQLModel, create_engine

from app.core.errors import BadRequestError
from app.models import Product
from app.services.inventory_service import post_txn


def _make_session():
    engine = create_engine('sqlite://', echo=False)
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_post_txn_updates_stock_and_blocks_negative_inventory():
    with _make_session() as session:
        product = Product(name='机油', sku='OIL-01', stock_quantity=5)
        session.add(product)
        session.commit()
        session.refresh(product)

        txn = post_txn(session, product_id=product.id, warehouse_id=None, change_qty=3, biz_type='manual', biz_id=1)
        assert round(txn.after_qty, 2) == 8
        session.commit()

        try:
            post_txn(session, product_id=product.id, warehouse_id=None, change_qty=-20, biz_type='manual', biz_id=2)
            raise AssertionError('expected BadRequestError')
        except BadRequestError:
            pass
