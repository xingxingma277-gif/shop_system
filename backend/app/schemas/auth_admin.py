from datetime import datetime
from typing import List, Optional

from sqlmodel import Field, SQLModel


class UserCreate(SQLModel):
    username: str
    display_name: str
    password: str = Field(min_length=6)
    role_ids: List[int] = []
    is_superuser: bool = False


class UserUpdate(SQLModel):
    display_name: Optional[str] = None
    password: Optional[str] = Field(default=None, min_length=6)
    role_ids: Optional[List[int]] = None
    status: Optional[str] = None
    is_superuser: Optional[bool] = None


class UserRead(SQLModel):
    id: int
    username: str
    display_name: str
    status: str
    is_superuser: bool
    role_ids: List[int] = []
    role_names: List[str] = []
    created_at: datetime


class RoleCreate(SQLModel):
    code: str
    name: str
    permission_ids: List[int] = []


class RoleUpdate(SQLModel):
    name: Optional[str] = None
    status: Optional[str] = None
    permission_ids: Optional[List[int]] = None


class RoleRead(SQLModel):
    id: int
    code: str
    name: str
    status: str
    permission_ids: List[int] = []
    permission_codes: List[str] = []
    created_at: datetime


class PermissionCreate(SQLModel):
    code: str
    name: str
    resource: str
    action: str


class PermissionRead(SQLModel):
    id: int
    code: str
    name: str
    resource: str
    action: str
    created_at: datetime


class AuditLogRead(SQLModel):
    id: int
    actor_user_id: Optional[int] = None
    actor_name: str
    action: str
    resource_type: str
    resource_id: Optional[int] = None
    detail: Optional[str] = None
    created_at: datetime
