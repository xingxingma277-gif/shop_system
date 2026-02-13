from sqlalchemy import func
from sqlmodel import Session, col, select

from app.core.errors import BadRequestError, NotFoundError
from app.models import Customer, Payment, Sale
from app.schemas.sale import SaleSummary
from app.services.buyer_service import ensure_default_personal_buyer
from app.services.pagination import paginate
from app.services.utils import to_update_dict


_ALLOWED_TYPES = {"company", "personal"}


def list_customers(session: Session, page: int, page_size: int, q: str | None = None, active_only: bool = True):
    stmt = select(Customer)
    if active_only:
        stmt = stmt.where(Customer.is_active == True)  # noqa: E712
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(col(Customer.name).ilike(like))
    stmt = stmt.order_by(Customer.created_at.desc(), Customer.id.desc())
    return paginate(session, stmt, page, page_size)


def create_customer(session: Session, data) -> Customer:
    ctype = (data.type or "company").strip().lower()
    if ctype not in _ALLOWED_TYPES:
        raise BadRequestError("客户类型仅支持 company/personal")
    customer = Customer(
        type=ctype,
        name=data.name.strip(),
        contact_name=(data.contact_name or "").strip(),
        phone=(data.phone or "").strip(),
        address=(data.address or "").strip(),
        is_active=bool(data.is_active),
    )
    if not customer.contact_name or not customer.phone or not customer.address:
        raise BadRequestError("联系人、电话、地址必填")
    session.add(customer)
    session.commit()
    session.refresh(customer)
    if customer.type == "personal":
        ensure_default_personal_buyer(session, customer)
    return customer


def update_customer(session: Session, customer_id: int, data) -> Customer:
    customer = session.get(Customer, customer_id)
    if not customer:
        raise NotFoundError("客户不存在")

    updates = to_update_dict(data)
    if "type" in updates and updates["type"] is not None:
        updates["type"] = updates["type"].strip().lower()
        if updates["type"] not in _ALLOWED_TYPES:
            raise BadRequestError("客户类型仅支持 company/personal")
    for key in ("name", "contact_name", "phone", "address"):
        if key in updates and updates[key] is not None:
            updates[key] = updates[key].strip()

    for k, v in updates.items():
        setattr(customer, k, v)

    session.add(customer)
    session.commit()
    session.refresh(customer)
    if customer.type == "personal":
        ensure_default_personal_buyer(session, customer)
    return customer


def delete_customer(session: Session, customer_id: int) -> None:
    customer = session.get(Customer, customer_id)
    if not customer:
        raise NotFoundError("客户不存在")

    sale_count = int(session.exec(select(func.count()).select_from(Sale).where(Sale.customer_id == customer_id)).one() or 0)
    payment_count = int(session.exec(select(func.count()).select_from(Payment).where(Payment.customer_id == customer_id)).one() or 0)

    if sale_count > 0 or payment_count > 0:
        raise ValueError("customer_has_related_records")

    session.delete(customer)
    session.commit()


def get_customer_or_404(session: Session, customer_id: int) -> Customer:
    customer = session.get(Customer, customer_id)
    if not customer:
        raise NotFoundError("客户不存在")
    return customer


def get_customer_profile(session: Session, customer_id: int, recent_limit: int = 10):
    customer = get_customer_or_404(session, customer_id)

    sales = session.exec(
        select(Sale).where(Sale.customer_id == customer_id).order_by(Sale.sale_date.desc(), Sale.id.desc()).limit(recent_limit)
    ).all()
    summaries = [
        SaleSummary(
            id=s.id,
            customer_id=s.customer_id,
            customer_name=customer.name,
            buyer_name=s.contact_name_snapshot,
            project=s.project,
            sale_date=s.sale_date,
            note=s.note,
            total_amount=s.total_amount,
            paid_amount=s.paid_amount,
            ar_amount=s.ar_amount,
            payment_status=s.payment_status,
        )
        for s in sales
    ]
    return customer, summaries


def get_ar_summary(session: Session, customer_id: int) -> dict:
    get_customer_or_404(session, customer_id)

    total_sales = float(session.exec(select(func.coalesce(func.sum(Sale.total_amount), 0)).where(Sale.customer_id == customer_id)).one() or 0)
    total_received = float(session.exec(select(func.coalesce(func.sum(Payment.amount), 0)).where(Payment.customer_id == customer_id)).one() or 0)

    return {
        "total_sales": round(total_sales, 2),
        "total_received": round(total_received, 2),
        "total_ar": round(total_sales - total_received, 2),
    }
