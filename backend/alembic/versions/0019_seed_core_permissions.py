"""seed core business permissions

Revision ID: 0019_seed_core_permissions
Revises: 0018_seed_default_permissions
Create Date: 2026-03-18
"""

from datetime import datetime

from alembic import op
import sqlalchemy as sa

revision = '0019_seed_core_permissions'
down_revision = '0018_seed_default_permissions'
branch_labels = None
depends_on = None


PERMISSIONS = [
    ('sale.view', '销售查看', 'sale', 'view'),
    ('sale.manage', '销售管理', 'sale', 'manage'),
    ('product.view', '商品查看', 'product', 'view'),
    ('product.manage', '商品管理', 'product', 'manage'),
    ('customer.view', '客户查看', 'customer', 'view'),
    ('customer.manage', '客户管理', 'customer', 'manage'),
    ('transaction.view', '交易查看', 'transaction', 'view'),
]


def upgrade() -> None:
    conn = op.get_bind()
    now = datetime.utcnow()
    for code, name, resource, action in PERMISSIONS:
        exists = conn.execute(sa.text('SELECT id FROM permission WHERE code = :code'), {'code': code}).fetchone()
        if exists:
            continue
        conn.execute(
            sa.text(
                'INSERT INTO permission (code, name, resource, action, created_at) '
                'VALUES (:code, :name, :resource, :action, :created_at)'
            ),
            {
                'code': code,
                'name': name,
                'resource': resource,
                'action': action,
                'created_at': now,
            },
        )


def downgrade() -> None:
    conn = op.get_bind()
    conn.execute(sa.text('DELETE FROM permission WHERE code IN :codes').bindparams(sa.bindparam('codes', expanding=True)), {'codes': [code for code, *_ in PERMISSIONS]})
