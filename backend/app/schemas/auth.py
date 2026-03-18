from typing import List

from sqlmodel import Field, SQLModel


class LoginPayload(SQLModel):
    username: str
    password: str = Field(min_length=6)


class CurrentUserRead(SQLModel):
    id: int
    username: str
    display_name: str
    is_superuser: bool
    role_ids: List[int] = []
    role_names: List[str] = []
    permission_codes: List[str] = []
