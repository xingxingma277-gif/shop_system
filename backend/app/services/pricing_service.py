from sqlmodel import Session, select

from app.core.errors import BadRequestError, NotFoundError
from app.models import Product, Sale, SaleItem, Customer
from app.schemas.pricing import PricingLastResponse, PricingHistoryItem, ProductTrendItem


def last_pricing(session: Session, customer_id: int, product_id: int) -> PricingLastResponse:
    customer = session.get(Customer, customer_id)
    if not customer:
        raise NotFoundError("客户不存在")

    product = session.get(Product, product_id)
    if not product:
        raise NotFoundError("商品不存在")

    stmt = (
        select(SaleItem, Sale)
        .join(Sale, Sale.id == SaleItem.sale_id)
        .where(Sale.customer_id == customer_id)
        .where(SaleItem.product_id == product_id)
        .order_by(Sale.sale_date.desc(), Sale.id.desc(), SaleItem.id.desc())
        .limit(1)
    )
    row = session.exec(stmt).first()

    if not row:
        return PricingLastResponse(found=False, standard_price=product.standard_price)

    si, sale = row
    return PricingLastResponse(
        found=True,
        standard_price=product.standard_price,
        last_price=si.sold_price,
        last_date=sale.sale_date,
        last_qty=si.qty,
    )


def pricing_history(session: Session, customer_id: int, product_id: int, limit: int = 20):
    limit = int(limit or 20)
    limit = max(1, min(limit, 200))

    customer = session.get(Customer, customer_id)
    if not customer:
        raise NotFoundError("客户不存在")

    product = session.get(Product, product_id)
    if not product:
        raise NotFoundError("商品不存在")

    stmt = (
        select(SaleItem, Sale)
        .join(Sale, Sale.id == SaleItem.sale_id)
        .where(Sale.customer_id == customer_id)
        .where(SaleItem.product_id == product_id)
        .order_by(Sale.sale_date.desc(), Sale.id.desc(), SaleItem.id.desc())
        .limit(limit)
    )
    rows = session.exec(stmt).all()
    return [
        PricingHistoryItem(
            date=sale.sale_date,
            qty=si.qty,
            sold_price=si.sold_price,
            sale_id=sale.id,
        )
        for (si, sale) in rows
    ]


def product_trend(session: Session, product_id: int, limit: int = 50):
    limit = int(limit or 50)
    limit = max(1, min(limit, 200))

    product = session.get(Product, product_id)
    if not product:
        raise NotFoundError("商品不存在")

    stmt = (
        select(SaleItem, Sale, Customer)
        .join(Sale, Sale.id == SaleItem.sale_id)
        .join(Customer, Customer.id == Sale.customer_id)
        .where(SaleItem.product_id == product_id)
        .order_by(Sale.sale_date.desc(), Sale.id.desc(), SaleItem.id.desc())
        .limit(limit)
    )
    rows = session.exec(stmt).all()

    return [
        ProductTrendItem(
            date=sale.sale_date,
            qty=si.qty,
            sold_price=si.sold_price,
            sale_id=sale.id,
            customer_id=c.id,
            customer_name=c.name,
        )
        for (si, sale, c) in rows
    ]
