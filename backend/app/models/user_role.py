from typing import Optional

from sqlmodel import Field, SQLModel


class UserRole(SQLModel, table=True):
    __tablename__ = 'user_role'

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key='user.id', index=True)
    role_id: int = Field(foreign_key='role.id', index=True)
