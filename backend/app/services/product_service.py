from sqlmodel import Session, select, col
from sqlalchemy import or_

from app.core.errors import NotFoundError, BadRequestError
from app.models import Product
from app.services.pagination import paginate
from app.services.utils import to_update_dict


def list_products(
    session: Session,
    page: int,
    page_size: int,
    q: str | None = None,
    active_only: bool = True,
):
    stmt = select(Product)
    if active_only:
        stmt = stmt.where(Product.is_active == True)  # noqa: E712

    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(
                col(Product.name).ilike(like),
                col(Product.sku).ilike(like),
            )
        )

    stmt = stmt.order_by(Product.created_at.desc(), Product.id.desc())
    return paginate(session, stmt, page, page_size)


def create_product(session: Session, data) -> Product:
    if data.standard_price is not None and data.standard_price < 0:
        raise BadRequestError("标准价不能为负数")

    product = Product(
        name=data.name.strip(),
        sku=(data.sku.strip() if data.sku else None),
        unit=(data.unit.strip() if data.unit else None),
        standard_price=float(data.standard_price or 0),
        is_active=bool(data.is_active),
    )
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def update_product(session: Session, product_id: int, data) -> Product:
    product = session.get(Product, product_id)
    if not product:
        raise NotFoundError("商品不存在")

    updates = to_update_dict(data)
    if "name" in updates and updates["name"] is not None:
        updates["name"] = updates["name"].strip()
    if "sku" in updates and updates["sku"] is not None:
        updates["sku"] = updates["sku"].strip()
    if "unit" in updates and updates["unit"] is not None:
        updates["unit"] = updates["unit"].strip()

    if "standard_price" in updates and updates["standard_price"] is not None:
        if updates["standard_price"] < 0:
            raise BadRequestError("标准价不能为负数")

    for k, v in updates.items():
        setattr(product, k, v)

    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def toggle_product_active(session: Session, product_id: int) -> Product:
    product = session.get(Product, product_id)
    if not product:
        raise NotFoundError("商品不存在")
    product.is_active = not bool(product.is_active)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


def get_product_or_404(session: Session, product_id: int) -> Product:
    product = session.get(Product, product_id)
    if not product:
        raise NotFoundError("商品不存在")
    return product
