from datetime import datetime

from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased
from sqlmodel import Session, select

from app.core.errors import BadRequestError, NotFoundError
from app.core.time import utc_now
from app.models import Customer, CustomerContact, Payment, PaymentAllocation, Product, Sale, SaleItem
from app.schemas.sale import SaleItemRead, SaleRead, SaleSummary
from app.services.inventory_service import post_txn
from app.services.pagination import paginate

_ALLOWED_SETTLEMENT = {"UNPAID", "PARTIAL", "PAID"}
_ALLOWED_METHODS = {"cash", "wechat", "alipay", "bank_transfer", "other"}
_METHOD_ALIASES = {"现金": "cash", "微信": "wechat", "支付宝": "alipay", "转账": "bank_transfer", "bank": "bank_transfer", "transfer": "bank_transfer", "其他": "other"}


def _compute_payment_status(total_amount: float, paid_amount: float) -> str:
    if paid_amount <= 0:
        return "unpaid"
    if paid_amount + 1e-6 >= total_amount:
        return "paid"
    return "partial"


def _to_settlement_status(payment_status: str) -> str:
    return {"unpaid": "UNPAID", "partial": "PARTIAL", "paid": "PAID"}.get(payment_status, "UNPAID")


def _normalize_method(method: str | None) -> str | None:
    if not method:
        return None
    value = _METHOD_ALIASES.get(method, method)
    if value not in _ALLOWED_METHODS:
        raise BadRequestError("付款方式不合法")
    return value


def _generate_sale_no(session: Session, sale_date: datetime, *, doc_type: str = "sale") -> str:
    day = sale_date.strftime("%Y%m%d")
    prefix_map = {"sale": "SO", "quote": "QT", "delivery": "DN"}
    prefix = f"{prefix_map.get(doc_type, 'SO')}{day}-"
    last_no = session.exec(select(Sale.sale_no).where(Sale.sale_no.like(f"{prefix}%")).order_by(Sale.sale_no.desc()).limit(1)).first()
    seq = 1
    if last_no and "-" in last_no:
        try:
            seq = int(last_no.split("-")[-1]) + 1
        except Exception:
            seq = 1
    return f"{prefix}{seq:04d}"


def next_sale_no(session: Session) -> str:
    return _generate_sale_no(session, utc_now(), doc_type="sale")


def _resolve_buyer_for_customer(session: Session, customer: Customer, buyer_id: int | None):
    if customer.type == "personal":
        if buyer_id:
            buyer = session.get(CustomerContact, buyer_id)
            if buyer and buyer.customer_id == customer.id:
                return buyer
        buyer = session.exec(select(CustomerContact).where(CustomerContact.customer_id == customer.id).order_by(CustomerContact.id.asc())).first()
        if buyer:
            return buyer
        buyer = CustomerContact(customer_id=customer.id, name=customer.name, phone=customer.phone, role="本人", is_active=True)
        session.add(buyer)
        session.flush()
        return buyer

    if not buyer_id:
        raise BadRequestError("公司客户必须选择拿货人")
    buyer = session.get(CustomerContact, buyer_id)
    if not buyer or buyer.customer_id != customer.id:
        raise BadRequestError("拿货人不存在")
    return buyer


def _validate_items_and_products(session: Session, items):
    if not items:
        raise BadRequestError("至少需要 1 行商品明细")
    product_ids = [i.product_id for i in items]
    if len(product_ids) != len(set(product_ids)):
        raise BadRequestError("同一订单中不允许重复添加相同商品，请直接修改原商品行数量")
    products = session.exec(select(Product).where(Product.id.in_(product_ids))).all()
    prod_map = {p.id: p for p in products}
    missing = [pid for pid in product_ids if pid not in prod_map]
    if missing:
        raise BadRequestError(f"商品不存在：{missing}")
    inactive = [p.name for p in products if not p.is_active]
    if inactive:
        raise BadRequestError(f"以下商品已停用：{', '.join(inactive)}")
    return prod_map


def create_sale(session: Session, data) -> SaleRead:
    customer = session.get(Customer, data.customer_id)
    if not customer:
        raise NotFoundError("客户不存在")
    if not customer.is_active:
        raise BadRequestError("客户已停用，不能开单")
    buyer = _resolve_buyer_for_customer(session, customer, data.buyer_id)
    prod_map = _validate_items_and_products(session, data.items)

    sale_date = data.sale_date or utc_now()
    preferred_sale_no = (data.sale_no or "").strip()
    order_stage = getattr(data, "order_stage", "SALE_CONFIRMED") or "SALE_CONFIRMED"
    if order_stage not in {"QUOTE", "SALE_CONFIRMED"}:
        raise BadRequestError("订单阶段不合法")
    order_type = getattr(data, "order_type", None) or ("quote" if order_stage == "QUOTE" else "sale_direct")
    if order_type not in {"quote", "sale_direct", "sale_from_quote"}:
        raise BadRequestError("order_type 不合法")

    doc_type = "quote" if order_stage == "QUOTE" else "sale"
    inventory_effected = order_stage == "SALE_CONFIRMED"

    for _ in range(3):
        sale_no = preferred_sale_no or _generate_sale_no(session, sale_date, doc_type=doc_type)
        sale = Sale(
            sale_no=sale_no,
            customer_id=data.customer_id,
            buyer_id=buyer.id,
            contact_id=buyer.id,
            contact_name_snapshot=buyer.name,
            project=data.project or None,
            project_name=data.project or None,
            order_type=order_type,
            order_stage=order_stage,
            inventory_effected=inventory_effected,
            needs_delivery=bool(getattr(data, "needs_delivery", False)),
            delivery_status="PENDING" if getattr(data, "needs_delivery", False) else "NONE",
            receiver_name=getattr(data, "receiver_name", None),
            receiver_phone=getattr(data, "receiver_phone", None),
            receiver_address=getattr(data, "receiver_address", None),
            delivery_note=getattr(data, "delivery_note", None),
            source_quote_id=getattr(data, "source_quote_id", None),
            quote_status="SUBMITTED" if order_stage == "QUOTE" else None,
            sale_date=sale_date,
            note=data.note,
            total_amount=0,
            paid_amount=0,
            ar_amount=0,
            payment_status="unpaid",
            settlement_status="UNPAID",
            payment_method=None,
            payment_note=None,
            created_at=utc_now(),
            updated_at=utc_now(),
        )
        session.add(sale)
        try:
            session.flush()
        except IntegrityError:
            session.rollback()
            preferred_sale_no = ""
            continue

        total = 0.0
        for it in data.items:
            qty = float(it.qty)
            price = float(it.unit_price)
            if qty <= 0:
                raise BadRequestError("数量必须大于 0")
            if price < 0:
                raise BadRequestError("成交价不能为负数")
            p = prod_map[it.product_id]
            if inventory_effected and float(p.stock_quantity or 0) < qty:
                raise BadRequestError(f"商品【{p.name}】当前库存 {float(p.stock_quantity or 0)}，不足 {qty}，库存不足，请改为报价单")
            if inventory_effected:
                post_txn(session, product_id=p.id, warehouse_id=None, change_qty=round(-qty, 2), biz_type="sale", biz_id=sale.id, sale_id=sale.id, note=f"销售单{sale.sale_no}扣减")
            line_total = round(qty * price, 2)
            total += line_total
            session.add(SaleItem(sale_id=sale.id, product_id=it.product_id, qty=qty, unit_price=price, sold_price=price, line_total=line_total, remark=it.note))

        sale.total_amount = round(total, 2)
        sale.ar_amount = round(total, 2)
        if order_stage == "SALE_CONFIRMED":
            sale.sale_confirmed_at = utc_now()

        settlement_status = getattr(data, "settlement_status", None)
        if order_stage == "SALE_CONFIRMED" and settlement_status in _ALLOWED_SETTLEMENT:
            method = _normalize_method(getattr(data, "payment_method", None))
            paid_amount = float(getattr(data, "paid_amount", 0) or 0)
            if settlement_status == "UNPAID":
                sale.paid_amount = 0
                sale.payment_status = "unpaid"
                sale.settlement_status = "UNPAID"
                sale.payment_method = None
            else:
                if not method:
                    raise BadRequestError("请选择付款方式")
                if settlement_status == "PAID":
                    paid_amount = float(total)
                if paid_amount < 0 or paid_amount > float(total):
                    raise BadRequestError("已付金额不合法")
                sale.paid_amount = round(paid_amount, 2)
                sale.ar_amount = round(max(float(total) - sale.paid_amount, 0), 2)
                sale.payment_status = _compute_payment_status(float(total), sale.paid_amount)
                sale.settlement_status = settlement_status
                sale.payment_method = method
            sale.payment_note = getattr(data, "payment_note", None)

        if sale.source_quote_id:
            source = session.get(Sale, sale.source_quote_id)
            if source and source.order_stage == "QUOTE":
                source.quote_status = "CONVERTED"
                source.updated_at = utc_now()
                session.add(source)

        sale.updated_at = utc_now()
        session.add(sale)
        session.commit()
        return get_sale(session, sale.id)

    raise BadRequestError("生成单号失败，请重试")


def update_quote(session: Session, sale_id: int, payload) -> SaleRead:
    sale = session.get(Sale, sale_id)
    if not sale:
        raise NotFoundError("单据不存在")
    if sale.order_stage != "QUOTE":
        raise BadRequestError("仅报价单可编辑")
    if sale.quote_status in {"CONVERTED", "VOIDED", "EXPIRED"}:
        raise BadRequestError("当前报价单状态不允许编辑")
    if payload.quote_updated_at != sale.updated_at:
        raise BadRequestError("报价单已被其他人修改，请刷新后重试")

    customer = session.get(Customer, payload.customer_id)
    if not customer:
        raise NotFoundError("客户不存在")
    buyer = _resolve_buyer_for_customer(session, customer, payload.buyer_id)
    prod_map = _validate_items_and_products(session, payload.items)

    sale.customer_id = payload.customer_id
    sale.buyer_id = buyer.id
    sale.contact_id = buyer.id
    sale.contact_name_snapshot = buyer.name
    sale.project = payload.project or None
    sale.note = payload.note or None

    items = session.exec(select(SaleItem).where(SaleItem.sale_id == sale.id)).all()
    for i in items:
        session.delete(i)

    total = 0.0
    for it in payload.items:
        qty = float(it.qty)
        price = float(it.unit_price)
        if qty <= 0:
            raise BadRequestError("数量必须大于 0")
        if price < 0:
            raise BadRequestError("成交价不能为负数")
        p = prod_map[it.product_id]
        line_total = round(qty * price, 2)
        total += line_total
        session.add(SaleItem(sale_id=sale.id, product_id=p.id, qty=qty, unit_price=price, sold_price=price, line_total=line_total, remark=it.note))

    sale.total_amount = round(total, 2)
    sale.ar_amount = round(total, 2)
    sale.updated_at = utc_now()
    session.add(sale)
    session.commit()
    return get_sale(session, sale.id)


def convert_quote_to_sale(session: Session, sale_id: int, payload=None):
    quote = session.get(Sale, sale_id)
    if not quote:
        raise NotFoundError("单据不存在")
    if quote.order_stage != "QUOTE":
        raise BadRequestError("仅报价单可转为销售清单")
    if quote.quote_status in {"CONVERTED", "VOIDED", "EXPIRED"}:
        raise BadRequestError("该报价单状态不允许转换")

    quote_items = session.exec(select(SaleItem).where(SaleItem.sale_id == quote.id)).all()
    sale_payload = type("SalePayload", (), {
        "sale_no": None,
        "customer_id": quote.customer_id,
        "order_type": "sale_from_quote",
        "buyer_id": quote.buyer_id,
        "project": quote.project,
        "sale_date": utc_now(),
        "note": quote.note,
        "order_stage": "SALE_CONFIRMED",
        "needs_delivery": bool(getattr(payload, "needs_delivery", False)),
        "receiver_name": getattr(payload, "receiver_name", None),
        "receiver_phone": getattr(payload, "receiver_phone", None),
        "receiver_address": getattr(payload, "receiver_address", None),
        "delivery_note": getattr(payload, "delivery_note", None),
        "settlement_status": getattr(payload, "settlement_status", "UNPAID"),
        "payment_method": getattr(payload, "payment_method", None),
        "paid_amount": getattr(payload, "paid_amount", 0),
        "payment_note": getattr(payload, "payment_note", None),
        "source_quote_id": quote.id,
        "items": [type("I", (), {"product_id": i.product_id, "qty": i.qty, "unit_price": i.unit_price or i.sold_price, "note": i.remark}) for i in quote_items],
    })
    created = create_sale(session, sale_payload)
    quote.quote_status = "CONVERTED"
    quote.updated_at = utc_now()
    session.add(quote)
    session.commit()
    return created


def generate_delivery(session: Session, sale_id: int, payload=None):
    sale = session.get(Sale, sale_id)
    if not sale:
        raise NotFoundError("单据不存在")
    if sale.order_stage not in ["SALE_CONFIRMED", "DELIVERY_CREATED"]:
        raise BadRequestError("仅销售清单可生成送货单")
    if sale.biz_status == "VOIDED":
        raise BadRequestError("单据已作废，无法生成")

    sale.needs_delivery = True
    sale.order_stage = "DELIVERY_CREATED"
    if not sale.sale_no.startswith("DN"):
        sale.sale_no = _generate_sale_no(session, utc_now(), doc_type="delivery")
    sale.delivery_status = "GENERATED"
    sale.receiver_name = getattr(payload, "receiver_name", None) or sale.receiver_name
    sale.receiver_phone = getattr(payload, "receiver_phone", None) or sale.receiver_phone
    sale.receiver_address = getattr(payload, "receiver_address", None) or sale.receiver_address
    sale.delivery_note = getattr(payload, "delivery_note", None) or sale.delivery_note
    sale.delivery_created_at = sale.delivery_created_at or utc_now()
    sale.updated_at = utc_now()

    session.add(sale)
    session.commit()
    return get_sale(session, sale.id)


def update_settlement(session: Session, *, sale_id: int, settlement_status: str, paid_amount: float, payment_method: str | None, payment_note: str | None):
    from app.services import settlement_service
    settlement_service.apply_settlement_compat(session, sale_id=sale_id, settlement_status=settlement_status, paid_amount=paid_amount, payment_method=payment_method, payment_note=payment_note)
    return get_sale(session, sale_id)


def _sale_gross_profit(session: Session, sale_id: int) -> float:
    rows = session.exec(select(SaleItem, Product).join(Product, Product.id == SaleItem.product_id).where(SaleItem.sale_id == sale_id)).all()
    gp = 0.0
    for si, p in rows:
        gp += (float(si.unit_price or si.sold_price) - float(p.standard_cost or 0)) * float(si.qty)
    return round(gp, 2)


def list_sales(session: Session, customer_id: int | None, order_stage: str | None, page: int, page_size: int):
    quote_alias = aliased(Sale)
    stmt = select(Sale, Customer, quote_alias.sale_no).join(Customer, Customer.id == Sale.customer_id).outerjoin(quote_alias, quote_alias.id == Sale.source_quote_id)
    if customer_id:
        stmt = stmt.where(Sale.customer_id == customer_id)
    if order_stage:
        stmt = stmt.where(Sale.order_stage == order_stage)
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
            source_quote_id=s.source_quote_id,
            source_quote_no=source_quote_no,
            quote_status=s.quote_status,
            updated_at=s.updated_at,
            order_type=s.order_type,
            order_stage=s.order_stage,
            inventory_effected=s.inventory_effected,
            needs_delivery=s.needs_delivery,
            delivery_status=s.delivery_status,
            receiver_name=s.receiver_name,
            receiver_phone=s.receiver_phone,
            receiver_address=s.receiver_address,
            delivery_note=s.delivery_note,
            sale_date=s.sale_date,
            note=s.note,
            total_amount=s.total_amount,
            paid_amount=s.paid_amount,
            ar_amount=s.ar_amount,
            payment_status=s.payment_status,
            gross_profit=_sale_gross_profit(session, s.id),
            biz_status=s.biz_status,
        )
        for (s, c, source_quote_no) in rows
    ]
    return items, total, page, page_size


def get_sale(session: Session, sale_id: int) -> SaleRead:
    source_quote = aliased(Sale)
    row = session.exec(select(Sale, Customer, source_quote.sale_no).join(Customer, Customer.id == Sale.customer_id).outerjoin(source_quote, source_quote.id == Sale.source_quote_id).where(Sale.id == sale_id)).first()
    if not row:
        raise NotFoundError("单据不存在")

    sale, customer, source_quote_no = row
    item_rows = session.exec(select(SaleItem, Product).join(Product, Product.id == SaleItem.product_id).where(SaleItem.sale_id == sale_id).order_by(SaleItem.id.asc())).all()
    items = [SaleItemRead(id=si.id, product_id=si.product_id, product_name=p.name, sku=p.sku, unit=p.unit, qty=si.qty, unit_price=si.unit_price or si.sold_price, line_total=si.line_total, gross_profit=round((float(si.unit_price or si.sold_price) - float(p.standard_cost or 0)) * float(si.qty), 2), note=si.remark) for (si, p) in item_rows]

    return SaleRead(
        id=sale.id,
        sale_no=sale.sale_no,
        customer_id=sale.customer_id,
        customer_name=customer.name,
        buyer_id=sale.buyer_id,
        buyer_name=sale.contact_name_snapshot,
        project=sale.project,
        source_quote_id=sale.source_quote_id,
        source_quote_no=source_quote_no,
        quote_status=sale.quote_status,
        updated_at=sale.updated_at,
        order_type=sale.order_type,
        order_stage=sale.order_stage,
        inventory_effected=sale.inventory_effected,
        needs_delivery=sale.needs_delivery,
        delivery_status=sale.delivery_status,
        receiver_name=sale.receiver_name,
        receiver_phone=sale.receiver_phone,
        receiver_address=sale.receiver_address,
        delivery_note=sale.delivery_note,
        sale_date=sale.sale_date,
        note=sale.note,
        total_amount=sale.total_amount,
        paid_amount=sale.paid_amount,
        ar_amount=sale.ar_amount,
        payment_status=sale.payment_status,
        settlement_status=sale.settlement_status,
        payment_method=sale.payment_method,
        payment_note=sale.payment_note,
        quote_confirmed_at=sale.quote_confirmed_at,
        sale_confirmed_at=sale.sale_confirmed_at,
        delivery_created_at=sale.delivery_created_at,
        delivered_at=sale.delivered_at,
        gross_profit=_sale_gross_profit(session, sale.id),
        biz_status=sale.biz_status,
        created_at=sale.created_at,
        items=items,
    )


def recompute_sale_payment(session: Session, sale: Sale):
    paid_direct = float(session.exec(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.sale_id == sale.id, Payment.scene != "REVERSAL")).one() or 0)
    paid_alloc = float(session.exec(select(func.coalesce(func.sum(PaymentAllocation.amount), 0)).where(PaymentAllocation.sale_id == sale.id)).one() or 0)
    reversed_amount = float(session.exec(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.sale_id == sale.id, Payment.scene == "REVERSAL")).one() or 0)
    paid = round(paid_direct + paid_alloc + reversed_amount, 2)
    sale.paid_amount = paid
    sale.ar_amount = round(max(float(sale.total_amount) - sale.paid_amount, 0), 2)
    sale.payment_status = _compute_payment_status(float(sale.total_amount), float(sale.paid_amount))
    sale.settlement_status = _to_settlement_status(sale.payment_status)
    if sale.settlement_status == "UNPAID":
        sale.payment_method = None
    session.add(sale)
