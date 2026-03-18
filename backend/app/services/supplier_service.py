from sqlmodel import Session, select

from app.core.errors import BadRequestError, NotFoundError
from app.models import Supplier


def create_supplier(session: Session, data: dict | object):
    code = (getattr(data, 'code', None) or '').strip().upper()
    name = (getattr(data, 'name', None) or '').strip()
    if not code or not name:
        raise BadRequestError('供应商编码和名称不能为空')
    exists = session.exec(select(Supplier).where(Supplier.code == code)).first()
    if exists:
        raise BadRequestError('供应商编码已存在')
    obj = Supplier(
        code=code,
        name=name,
        contact_name=getattr(data, 'contact_name', None),
        phone=getattr(data, 'phone', None),
        address=getattr(data, 'address', None),
        note=getattr(data, 'note', None),
        status='ACTIVE',
    )
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def list_suppliers(session: Session, q: str | None, status: str | None):
    stmt = select(Supplier)
    if q:
        like = f"%{q.strip()}%"
        stmt = stmt.where((Supplier.name.ilike(like)) | (Supplier.code.ilike(like)))
    if status:
        stmt = stmt.where(Supplier.status == status)
    return session.exec(stmt.order_by(Supplier.id.desc())).all()


def update_supplier(session: Session, supplier_id: int, data: dict | object):
    obj = session.get(Supplier, supplier_id)
    if not obj:
        raise NotFoundError('供应商不存在')
    for key in ['name', 'contact_name', 'phone', 'address', 'note', 'status']:
        val = getattr(data, key, None)
        if val is not None:
            setattr(obj, key, val)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj
