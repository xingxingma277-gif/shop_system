from sqlmodel import Session, select

from app.core.errors import BadRequestError, NotFoundError
from app.core.time import utc_now
from app.models import Customer, CustomerContact, Product, Sale, SaleItem
from app.schemas.sale import SaleItemRead, SaleRead, SaleSummary
from app.services.pagination import paginate


def _compute_payment_status(total_amount: float, paid_amount: float) -> str:
    if paid_amount <= 0:
        return "unpaid"
    if paid_amount + 1e-6 >= total_amount:
        return "paid"
    return "partial"


def _generate_sale_no(session: Session, sale_date: datetime) -> str:
    day = sale_date.strftime("%Y%m%d")
    prefix = f"SO{day}-"
    last_no = session.exec(
        select(Sale.sale_no).where(Sale.sale_no.like(f"{prefix}%")).order_by(Sale.sale_no.desc()).limit(1)
    ).first()
    seq = 1
    if last_no and "-" in last_no:
        try:
            seq = int(last_no.split("-")[-1]) + 1
        except Exception:
            seq = 1
    return f"{prefix}{seq:04d}"


def create_sale(session: Session, data) -> SaleRead:
    customer = session.get(Customer, data.customer_id)
    if not customer:
        raise NotFoundError("客户不存在")
    if not customer.is_active:
        raise BadRequestError("客户已停用，不能开单")

    buyer = session.get(CustomerContact, data.buyer_id)
    if not buyer or buyer.customer_id != data.customer_id:
        raise BadRequestError("拿货人不存在")

    if not data.items:
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

    sale_date = data.sale_date or utc_now()

    sale = Sale(
        sale_no=_generate_sale_no(session, sale_date),
        customer_id=data.customer_id,
        buyer_id=data.buyer_id,
        contact_id=data.buyer_id,
        contact_name_snapshot=buyer.name,
        project=data.project,
        project_name=data.project,
        sale_date=sale_date,
        note=data.note,
        total_amount=0,
        paid_amount=0,
        ar_amount=0,
        payment_status="unpaid",
    )
    session.add(sale)
    session.flush()

    total = 0.0
    for it in data.items:
        qty = float(it.qty)
        price = float(it.unit_price)
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
            unit_price=price,
            sold_price=price,
            line_total=line_total,
            remark=it.note,
        )
        session.add(si)

    sale.total_amount = round(total, 2)
    sale.ar_amount = round(total, 2)
    sale.payment_status = _compute_payment_status(sale.total_amount, sale.paid_amount)
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
            sale_no=s.sale_no,
            customer_id=s.customer_id,
            customer_name=c.name,
            buyer_name=s.contact_name_snapshot,
            project=s.project,
            sale_date=s.sale_date,
            note=s.note,
            total_amount=s.total_amount,
            paid_amount=s.paid_amount,
            ar_amount=s.ar_amount,
            payment_status=s.payment_status,
        )
        for (s, c) in rows
    ]
    return items, total, page, page_size


def get_sale(session: Session, sale_id: int) -> SaleRead:
    row = session.exec(select(Sale, Customer).join(Customer, Customer.id == Sale.customer_id).where(Sale.id == sale_id)).first()
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
            unit_price=si.unit_price or si.sold_price,
            line_total=si.line_total,
            note=si.remark,
        )
        for (si, p) in item_rows
    ]

    return SaleRead(
        id=sale.id,
        sale_no=sale.sale_no,
        customer_id=sale.customer_id,
        customer_name=customer.name,
        buyer_id=sale.buyer_id,
        buyer_name=sale.contact_name_snapshot,
        project=sale.project,
        sale_date=sale.sale_date,
        note=sale.note,
        total_amount=sale.total_amount,
        paid_amount=sale.paid_amount,
        ar_amount=sale.ar_amount,
        payment_status=sale.payment_status,
        created_at=sale.created_at,
        items=items,
    )


def recompute_sale_payment(session: Session, sale: Sale):
    paid = 0.0
    for p in sale.payments:
        paid += float(p.amount)
    sale.paid_amount = round(paid, 2)
    sale.ar_amount = round(float(sale.total_amount) - sale.paid_amount, 2)
    sale.payment_status = _compute_payment_status(float(sale.total_amount), float(sale.paid_amount))
    session.add(sale)
