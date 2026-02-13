from datetime import timedelta
from sqlmodel import Session, select

from app.core.config import APP_ENV
from app.core.time import utc_now
from app.db.session import engine
from app.models import Customer, Product, Sale, SaleItem, CustomerContact, Payment


def upsert_customer(session: Session, name: str, phone: str | None = None, address: str | None = None) -> Customer:
    c = session.exec(select(Customer).where(Customer.name == name)).first()
    if c:
        return c
    c = Customer(type="company", name=name, contact_name=name, phone=phone or "", address=address or "", is_active=True)
    session.add(c)
    session.flush()
    return c


def upsert_product(session: Session, name: str, standard_price: float, sku: str | None = None, unit: str | None = None) -> Product:
    p = session.exec(select(Product).where(Product.name == name)).first()
    if p:
        return p
    p = Product(name=name, sku=sku, unit=unit, standard_price=standard_price, is_active=True)
    session.add(p)
    session.flush()
    return p


def upsert_contact(session: Session, customer_id: int, name: str, role: str, phone: str | None = None) -> CustomerContact:
    c = session.exec(
        select(CustomerContact).where(
            CustomerContact.customer_id == customer_id,
            CustomerContact.name == name,
        )
    ).first()
    if c:
        return c
    c = CustomerContact(customer_id=customer_id, name=name, role=role, phone=phone, is_active=True)
    session.add(c)
    session.flush()
    return c


def run_seed():
    if APP_ENV.lower() != "dev":
        raise SystemExit("seed 只允许在 APP_ENV=dev 下运行")

    with Session(engine) as session:
        # 基础数据
        c1 = upsert_customer(session, "老李维修公司", phone="13800000001", address="城南街道 12 号")
        c2 = upsert_customer(session, "城南五金店", phone="13800000002", address="五金批发市场 A-18")

        p1 = upsert_product(session, "格力35uf启动电容", 15.0, sku="CAP-35UF", unit="个")
        p2 = upsert_product(session, "R22制冷剂(罐装)", 220.0, sku="R22-CAN", unit="罐")
        p3 = upsert_product(session, "美的洗衣机排水泵", 35.0, sku="MD-PUMP", unit="个")

        session.commit()
        session.refresh(c1); session.refresh(c2)
        session.refresh(p1); session.refresh(p2); session.refresh(p3)

        # 联系人（公司多维修工）
        contact_worker1 = upsert_contact(session, c1.id, "小王", "维修工", "13811110001")
        contact_worker2 = upsert_contact(session, c1.id, "小刘", "维修工", "13811110002")
        contact_account = upsert_contact(session, c1.id, "张会计", "会计", "13811119999")

        session.commit()
        session.refresh(contact_worker1); session.refresh(contact_worker2); session.refresh(contact_account)

        def ensure_sale(customer: Customer, when, note: str, contact: CustomerContact | None, items):
            # 若同日期同备注存在则不重复插入
            exists = session.exec(
                select(Sale).where(Sale.customer_id == customer.id, Sale.sale_date == when, Sale.note == note)
            ).first()
            if exists:
                return exists

            sale = Sale(
                customer_id=customer.id,
                sale_date=when,
                note=note,
                total_amount=0,
                contact_id=contact.id if contact else None,
                contact_name_snapshot=contact.name if contact else None,
                project_name="空调维修项目" if customer.id == c1.id else None,
                signed_by=contact.name if contact else None,
            )
            session.add(sale)
            session.flush()

            total = 0.0
            for prod, qty, price, remark in items:
                line_total = round(qty * price, 2)
                total += line_total
                session.add(
                    SaleItem(
                        sale_id=sale.id,
                        product_id=prod.id,
                        qty=qty,
                        unit_price=price,
                        sold_price=price,
                        line_total=line_total,
                        remark=remark,
                    )
                )
            sale.total_amount = round(total, 2)
            session.add(sale)
            session.commit()
            session.refresh(sale)
            return sale

        now = utc_now()
        sale_a = ensure_sale(
            c1,
            now - timedelta(days=20),
            "上次拿货（赊账）",
            contact_worker1,
            [(p1, 10, 12.0, "老客户优惠"), (p2, 1, 210.0, None)],
        )
        sale_b = ensure_sale(
            c1,
            now - timedelta(days=7),
            "补一批货（部分付款）",
            contact_worker2,
            [(p1, 5, 13.0, None), (p3, 2, 34.0, "顺带")],
        )
        sale_c = ensure_sale(
            c2,
            now - timedelta(days=5),
            "首次合作（已付款）",
            None,
            [(p2, 2, 220.0, None), (p3, 1, 35.0, None)],
        )

        # 付款示例：sale_b 部分付款，sale_c 全额付款
        def ensure_payment(sale: Sale, amount: float, method: str, days_ago: int, note: str | None = None):
            exists = session.exec(
                select(Payment).where(Payment.sale_id == sale.id, Payment.amount == amount, Payment.method == method)
            ).first()
            if exists:
                return
            session.add(
                Payment(
                    customer_id=sale.customer_id,
                    sale_id=sale.id,
                    amount=round(amount, 2),
                    method=method,
                    paid_at=now - timedelta(days=days_ago),
                    note=note,
                )
            )
            session.commit()

        # sale_b 付一部分
        ensure_payment(sale_b, amount=50.0, method="微信", days_ago=6, note="维修工先付一部分")
        # sale_c 全额付款
        ensure_payment(sale_c, amount=sale_c.total_amount, method="转账", days_ago=5, note="现结")

        print("seed 完成：已插入客户、联系人、商品、历史单据、付款流水。")


if __name__ == "__main__":
    run_seed()
