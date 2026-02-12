from typing import Generic, List, TypeVar
from pydantic import BaseModel
from sqlmodel import SQLModel

T = TypeVar("T")


class PageMeta(SQLModel):
    page: int
    page_size: int
    total: int
    pages: int


class PageParams(SQLModel):
    page: int = 1
    page_size: int = 20


class Page(BaseModel, Generic[T]):
    items: List[T]
    meta: PageMeta
