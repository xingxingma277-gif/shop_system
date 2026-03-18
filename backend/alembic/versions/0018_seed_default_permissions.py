"""seed default permissions

Revision ID: 0018_seed_default_permissions
Revises: 0017_auth_token_sessions
Create Date: 2026-03-18
"""

from datetime import datetime

from alembic import op
import sqlalchemy as sa

revision = '0018_seed_default_permissions'
down_revision = '0017_auth_token_sessions'
branch_labels = None
depends_on = None


PERMISSIONS = [
    ('admin.user.manage', '用户管理', 'admin', 'user_manage'),
    ('admin.role.manage', '角色管理', 'admin', 'role_manage'),
    ('admin.permission.manage', '权限管理', 'admin', 'permission_manage'),
    ('audit.view', '审计查看', 'audit', 'view'),
    ('supplier.manage', '供应商管理', 'supplier', 'manage'),
    ('warehouse.manage', '仓库管理', 'warehouse', 'manage'),
    ('purchase.view', '采购查看', 'purchase', 'view'),
    ('purchase.manage', '采购管理', 'purchase', 'manage'),
    ('inventory.view', '库存查看', 'inventory', 'view'),
    ('inventory.manage', '库存管理', 'inventory', 'manage'),
    ('report.view', '报表查看', 'report', 'view'),
    ('ap.manage', '应付管理', 'ap', 'manage'),
]


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.utcnow()
    for code, name, resource, action in PERMISSIONS:
        exists = conn.execute(sa.text("SELECT 1 FROM permission WHERE code = :code"), {'code': code}).fetchone()
        if not exists:
            conn.execute(
                sa.text("""
                    INSERT INTO permission (code, name, resource, action, created_at)
                    VALUES (:code, :name, :resource, :action, :created_at)
                """),
                {'code': code, 'name': name, 'resource': resource, 'action': action, 'created_at': now},
            )


def downgrade() -> None:
    conn = op.get_bind()
    for code, *_ in PERMISSIONS:
        conn.execute(sa.text("DELETE FROM permission WHERE code = :code"), {'code': code})
