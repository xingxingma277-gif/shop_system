from sqlmodel import Session, select
from app.core.errors import NotFoundError, BadRequestError
from app.core.time import utc_now
from app.models import Sale, SaleItem, Customer, Product
from app.schemas.sale import SaleRead, SaleItemRead, SaleSummary
from app.services.pagination import paginate


def create_sale(session: Session, data) -> SaleRead:
    customer = session.get(Customer, data.customer_id)
    if not customer:
        raise NotFoundError("客户不存在")
    if not customer.is_active:
        raise BadRequestError("客户已停用，不能开单")

    if not data.items or len(data.items) == 0:
        raise BadRequestError("至少需要 1 行商品明细")

    product_ids = list({i.product_id for i in data.items})
    products = session.exec(select(Product).where(Product.id.in_(product_ids))).all()
    prod_map = {p.id: p for p in products}

    missing = [pid for pid in product_ids if pid not in prod_map]
    if missing:
        raise BadRequestError(f"商品不存在：{missing}")

    inactive = [p.name for p in products if not p.is_active]
    if inactive:
        raise BadRequestError(f"以下商品已停用：{', '.join(inactive)}")

    sale = Sale(
        customer_id=data.customer_id,
        sale_date=data.sale_date or utc_now(),
        note=data.note,
        total_amount=0,
    )
    session.add(sale)
    session.flush()  # 获取 sale.id

    total = 0.0
    for it in data.items:
        qty = float(it.qty)
        price = float(it.sold_price)
        if qty <= 0:
            raise BadRequestError("数量必须大于 0")
        if price < 0:
            raise BadRequestError("成交价不能为负数")

        line_total = round(qty * price, 2)
        total += line_total

        si = SaleItem(
            sale_id=sale.id,
            product_id=it.product_id,
            qty=qty,
            sold_price=price,
            line_total=line_total,
            remark=it.remark,
        )
        session.add(si)

    sale.total_amount = round(total, 2)
    session.add(sale)
    session.commit()

    return get_sale(session, sale.id)


def list_sales(session: Session, customer_id: int | None, page: int, page_size: int):
    stmt = select(Sale, Customer).join(Customer, Customer.id == Sale.customer_id)
    if customer_id:
        stmt = stmt.where(Sale.customer_id == customer_id)
    stmt = stmt.order_by(Sale.sale_date.desc(), Sale.id.desc())

    rows, total, page, page_size = paginate(session, stmt, page, page_size)
    items = [
        SaleSummary(
            id=s.id,
            customer_id=s.customer_id,
            customer_name=c.name,
            sale_date=s.sale_date,
            note=s.note,
            total_amount=s.total_amount,
        )
        for (s, c) in rows
    ]
    return items, total, page, page_size


def get_sale(session: Session, sale_id: int) -> SaleRead:
    row = session.exec(
        select(Sale, Customer)
        .join(Customer, Customer.id == Sale.customer_id)
        .where(Sale.id == sale_id)
    ).first()
    if not row:
        raise NotFoundError("单据不存在")

    sale, customer = row

    item_rows = session.exec(
        select(SaleItem, Product)
        .join(Product, Product.id == SaleItem.product_id)
        .where(SaleItem.sale_id == sale_id)
        .order_by(SaleItem.id.asc())
    ).all()

    items = [
        SaleItemRead(
            id=si.id,
            product_id=si.product_id,
            product_name=p.name,
            sku=p.sku,
            unit=p.unit,
            qty=si.qty,
            sold_price=si.sold_price,
            line_total=si.line_total,
            remark=si.remark,
        )
        for (si, p) in item_rows
    ]

    return SaleRead(
        id=sale.id,
        customer_id=sale.customer_id,
        customer_name=customer.name,
        sale_date=sale.sale_date,
        note=sale.note,
        total_amount=sale.total_amount,
        created_at=sale.created_at,
        items=items,
    )
