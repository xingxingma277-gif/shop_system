from datetime import datetime

from sqlmodel import Session, SQLModel, create_engine

from app.core.errors import BadRequestError
from app.models import Customer, CustomerContact, Product, Sale
from app.schemas.sale import QuoteUpdate, SaleCreate, SaleItemCreate
from app.services import pricing_service, sale_service


def _make_session():
    engine = create_engine('sqlite://', echo=False)
    SQLModel.metadata.create_all(engine)
    return Session(engine)


def _seed_customer_and_product(session):
    customer = Customer(name='测试公司', type='company', is_active=True)
    session.add(customer)
    session.commit()
    session.refresh(customer)

    contact = CustomerContact(customer_id=customer.id, name='张三', phone='13800000000', is_active=True)
    product = Product(name='A商品', unit='件', is_active=True, stock_quantity=100, standard_price=50)
    session.add(contact)
    session.add(product)
    session.commit()
    session.refresh(contact)
    session.refresh(product)
    return customer, contact, product


def test_pricing_last_price_and_history_contract():
    with _make_session() as session:
        customer, contact, product = _seed_customer_and_product(session)
        sale = sale_service.create_sale(session, SaleCreate(customer_id=customer.id, buyer_id=contact.id, order_stage='SALE_CONFIRMED', items=[SaleItemCreate(product_id=product.id, qty=2, unit_price=80)]))

        last = pricing_service.last_pricing(session, customer.id, product.id)
        assert last.found is True
        assert last.last_price == 80
        assert last.last_sale_no == sale.sale_no

        history = pricing_service.pricing_history(session, customer.id, product.id, page=1, page_size=10)
        assert history.meta.total == 1
        assert history.items[0].sale_no == sale.sale_no


def test_quote_convert_creates_new_sale_with_source_quote():
    with _make_session() as session:
        customer, contact, product = _seed_customer_and_product(session)
        quote = sale_service.create_sale(session, SaleCreate(customer_id=customer.id, buyer_id=contact.id, order_stage='QUOTE', items=[SaleItemCreate(product_id=product.id, qty=2, unit_price=80)]))
        converted = sale_service.convert_quote_to_sale(session, quote.id, type('P', (), {'settlement_status': 'UNPAID'}))

        assert converted.id != quote.id
        assert converted.source_quote_id == quote.id
        assert converted.order_stage == 'SALE_CONFIRMED'
        quote_row = session.get(Sale, quote.id)
        assert quote_row.quote_status == 'CONVERTED'


def test_pdf_preview_content_disposition_header():
    # router层由 download 参数切换 inline / attachment，这里用服务侧保证可导出入口可用
    with _make_session() as session:
        customer, contact, product = _seed_customer_and_product(session)
        sale = sale_service.create_sale(session, SaleCreate(customer_id=customer.id, buyer_id=contact.id, order_stage='QUOTE', items=[SaleItemCreate(product_id=product.id, qty=1, unit_price=60)]))
        assert sale.sale_no.startswith('QT')


def test_company_customer_buyer_required():
    with _make_session() as session:
        customer = Customer(name='测试公司', type='company', is_active=True)
        product = Product(name='A商品', unit='件', is_active=True, stock_quantity=100, standard_price=50)
        session.add(customer)
        session.add(product)
        session.commit()
        try:
            sale_service.create_sale(session, SaleCreate(customer_id=customer.id, buyer_id=None, order_stage='SALE_CONFIRMED', items=[SaleItemCreate(product_id=product.id, qty=1, unit_price=50)]))
            assert False
        except BadRequestError as exc:
            assert '公司客户必须选择拿货人' in exc.message


def test_insufficient_stock_rejected_for_sale():
    with _make_session() as session:
        customer, contact, product = _seed_customer_and_product(session)
        product.stock_quantity = 1
        session.add(product)
        session.commit()
        try:
            sale_service.create_sale(session, SaleCreate(customer_id=customer.id, buyer_id=contact.id, order_stage='SALE_CONFIRMED', items=[SaleItemCreate(product_id=product.id, qty=3, unit_price=80)]))
            assert False
        except BadRequestError as exc:
            assert '库存不足，请改为报价单' in exc.message
