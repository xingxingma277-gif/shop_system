from datetime import datetime
from typing import Optional, List

from sqlalchemy import func
from sqlmodel import Session, select

from app.core.errors import BadRequestError, NotFoundError
from app.core.time import utc_now
from app.models import Customer, Payment, Sale
from app.services.sale_service import get_sale, recompute_sale_payment

_ALLOWED_METHODS = {"cash", "wechat", "alipay", "bank", "transfer", "other", "现金", "微信", "支付宝", "银行卡", "转账", "其他"}
_ALLOWED_PAY_TYPES = {"paid_full", "credit", "partial"}


def _parse_iso_dt(dt_str: Optional[str]) -> datetime:
    if not dt_str:
        return utc_now()
    return datetime.fromisoformat(dt_str.replace("Z", "+00:00"))


def create_payment(session: Session, sale_id: int, amount: float, method: str, paid_at: Optional[str], note: Optional[str]):
    sale = session.get(Sale, sale_id)
    if not sale:
        raise NotFoundError("单据不存在")
    if method not in _ALLOWED_METHODS:
        raise BadRequestError("付款方式不合法")

    if amount <= 0:
        raise BadRequestError("金额必须大于0")
    if amount > float(sale.ar_amount) + 1e-6:
        raise BadRequestError("收款金额不能超过该单未付金额")

    payment = Payment(
        customer_id=sale.customer_id,
        sale_id=sale.id,
        pay_type="partial",
        amount=round(float(amount), 2),
        method=method,
        paid_at=_parse_iso_dt(paid_at),
        note=note,
    )
    session.add(payment)
    session.flush()
    session.refresh(sale)
    recompute_sale_payment(session, sale)
    session.commit()
    session.refresh(payment)
    return payment


def submit_sale_payment(session: Session, sale_id: int, pay_type: str, method: str, amount: Optional[float], note: Optional[str]):
    sale = session.get(Sale, sale_id)
    if not sale:
        raise NotFoundError("单据不存在")
    if pay_type not in _ALLOWED_PAY_TYPES:
        raise BadRequestError("pay_type 不合法")
    if method not in _ALLOWED_METHODS:
        raise BadRequestError("method 不合法")

    pay_amount = 0.0
    if pay_type == "paid_full":
        pay_amount = float(sale.ar_amount)
    elif pay_type == "credit":
        pay_amount = 0.0
    else:
        pay_amount = float(amount or 0)

    created = None
    if pay_amount > 0:
        created = Payment(
            customer_id=sale.customer_id,
            sale_id=sale.id,
            pay_type=pay_type,
            amount=round(pay_amount, 2),
            method=method,
            paid_at=utc_now(),
            note=note,
        )
        session.add(created)
        session.flush()

    session.refresh(sale)
    recompute_sale_payment(session, sale)
    session.commit()
    updated_sale = get_sale(session, sale.id)

    payment_payload = None
    if created:
        session.refresh(created)
        payment_payload = {
            "id": created.id,
            "sale_id": created.sale_id,
            "customer_id": created.customer_id,
            "pay_type": created.pay_type,
            "amount": created.amount,
            "method": created.method,
            "paid_at": created.paid_at.isoformat(),
            "note": created.note,
        }
    else:
        payment_payload = {
            "id": None,
            "sale_id": sale.id,
            "customer_id": sale.customer_id,
            "pay_type": pay_type,
            "amount": 0,
            "method": method,
            "paid_at": utc_now().isoformat(),
            "note": note,
        }
    return updated_sale, payment_payload


def list_payments(session: Session, customer_id: Optional[int], sale_id: Optional[int], page: int, page_size: int):
    conds = []
    if customer_id is not None:
        conds.append(Payment.customer_id == customer_id)
    if sale_id is not None:
        conds.append(Payment.sale_id == sale_id)

    total_stmt = select(func.count()).select_from(Payment)
    for c in conds:
        total_stmt = total_stmt.where(c)
    total = session.exec(total_stmt).one()

    stmt = select(Payment)
    for c in conds:
        stmt = stmt.where(c)

    stmt = stmt.order_by(Payment.paid_at.desc(), Payment.id.desc()).offset((page - 1) * page_size).limit(page_size)
    items = session.exec(stmt).all()
    return items, int(total)


def batch_apply(
    session: Session,
    *,
    customer_id: int,
    sale_ids: List[int],
    total_amount: float,
    method: str,
    paid_at: Optional[str],
    note: Optional[str],
):
    customer = session.get(Customer, customer_id)
    if not customer:
        raise NotFoundError("客户不存在")

    if method not in _ALLOWED_METHODS:
        raise BadRequestError("付款方式不合法")

    sales = session.exec(select(Sale).where(Sale.customer_id == customer_id, Sale.id.in_(sale_ids))).all()
    if not sales:
        raise NotFoundError("未找到可结算单据")

    sale_rows = [(s, float(s.ar_amount)) for s in sales if float(s.ar_amount) > 0.000001]
    if not sale_rows:
        raise BadRequestError("所选单据均已结清")

    sale_rows.sort(key=lambda x: (x[0].sale_date, x[0].id))
    total_balance = sum(b for _, b in sale_rows)
    if total_amount > total_balance + 1e-6:
        raise BadRequestError("收款金额超过所选单据总欠款")

    remaining = round(float(total_amount), 2)
    paid_at_dt = _parse_iso_dt(paid_at)

    allocations = []
    created = 0

    for s, bal in sale_rows:
        if remaining <= 0:
            break
        apply_amt = round(float(min(bal, remaining)), 2)
        if apply_amt <= 0:
            continue

        p = Payment(
            customer_id=customer_id,
            sale_id=s.id,
            pay_type="partial",
            amount=apply_amt,
            method=method,
            paid_at=paid_at_dt,
            note=note,
        )
        session.add(p)
        session.flush()

        session.refresh(s)
        recompute_sale_payment(session, s)

        allocations.append(
            {
                "sale_id": s.id,
                "applied_amount": apply_amt,
                "after_paid_amount": s.paid_amount,
                "after_balance": s.ar_amount,
                "after_status": s.payment_status,
            }
        )
        created += 1
        remaining = round(remaining - apply_amt, 2)

    session.commit()
    return created, allocations
