from typing import Optional

from sqlmodel import Field, SQLModel


class RolePermission(SQLModel, table=True):
    __tablename__ = 'role_permission'

    id: Optional[int] = Field(default=None, primary_key=True)
    role_id: int = Field(foreign_key='role.id', index=True)
    permission_id: int = Field(foreign_key='permission.id', index=True)
