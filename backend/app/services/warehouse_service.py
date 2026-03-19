from sqlmodel import Session, select

from app.core.errors import BadRequestError, NotFoundError
from app.models import Warehouse


def create_warehouse(session: Session, data: dict | object):
    code = (getattr(data, 'code', None) or '').strip().upper()
    name = (getattr(data, 'name', None) or '').strip()
    if not code or not name:
        raise BadRequestError('仓库编码和名称不能为空')
    exists = session.exec(select(Warehouse).where(Warehouse.code == code)).first()
    if exists:
        raise BadRequestError('仓库编码已存在')

    is_default = bool(getattr(data, 'is_default', False))
    if is_default:
        for w in session.exec(select(Warehouse).where(Warehouse.is_default == True)).all():
            w.is_default = False
            session.add(w)

    obj = Warehouse(code=code, name=name, address=getattr(data, 'address', None), is_default=is_default)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj


def list_warehouses(session: Session, status: str | None):
    stmt = select(Warehouse)
    if status:
        stmt = stmt.where(Warehouse.status == status)
    return session.exec(stmt.order_by(Warehouse.id.desc())).all()


def update_warehouse(session: Session, warehouse_id: int, data: dict | object):
    obj = session.get(Warehouse, warehouse_id)
    if not obj:
        raise NotFoundError('仓库不存在')

    if getattr(data, 'is_default', None) is True:
        for w in session.exec(select(Warehouse).where(Warehouse.is_default == True)).all():
            w.is_default = False
            session.add(w)
        obj.is_default = True

    for key in ['name', 'address', 'status']:
        val = getattr(data, key, None)
        if val is not None:
            setattr(obj, key, val)
    session.add(obj)
    session.commit()
    session.refresh(obj)
    return obj
