from datetime import datetime

from sqlmodel import Session, SQLModel, create_engine

from app.models import Supplier, Warehouse, Purchase
from app.services import purchase_payment_service


def _make_session():
    engine = create_engine('sqlite://', echo=False)
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def test_create_supplier_payment_and_allocation_recompute_ap():
    with _make_session() as session:
        supplier = Supplier(code='S001', name='供应商A')
        wh = Warehouse(code='W001', name='主仓')
        session.add(supplier)
        session.add(wh)
        session.commit()
        session.refresh(supplier)
        session.refresh(wh)

        purchase = Purchase(
            purchase_no='PO20260101-0001',
            supplier_id=supplier.id,
            warehouse_id=wh.id,
            purchase_date=datetime.utcnow(),
            status='CONFIRMED',
            total_amount=1000,
            paid_amount=0,
            ap_amount=1000,
        )
        session.add(purchase)
        session.commit()
        session.refresh(purchase)

        payment = purchase_payment_service.create_supplier_payment(
            session,
            type('obj', (), {
                'supplier_id': supplier.id,
                'purchase_id': None,
                'amount': 600,
                'method': 'bank_transfer',
                'paid_at': None,
                'note': 'first pay',
            })
        )

        result = purchase_payment_service.allocate_payment(
            session,
            payment.id,
            type('obj', (), {'items': [type('obj', (), {'purchase_id': purchase.id, 'amount': 600})]})
        )

        assert result['allocated_amount'] == 600
        updated_purchase = session.get(Purchase, purchase.id)
        assert round(updated_purchase.paid_amount, 2) == 600
        assert round(updated_purchase.ap_amount, 2) == 400
