from sqlmodel import Session, select
from sqlalchemy import func


def normalize_page(page: int, page_size: int) -> tuple[int, int]:
    page = max(int(page or 1), 1)
    page_size = max(int(page_size or 20), 1)
    page_size = min(page_size, 100)
    return page, page_size


def paginate(session: Session, stmt, page: int, page_size: int):
    page, page_size = normalize_page(page, page_size)
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = session.exec(count_stmt).one()
    items = session.exec(
        stmt.offset((page - 1) * page_size).limit(page_size)
    ).all()
    return items, total, page, page_size
