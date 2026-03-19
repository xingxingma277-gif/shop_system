"""p2 auth and audit foundation

Revision ID: 0016_p2_auth_audit
Revises: 0015_inventory_check_transfer
Create Date: 2026-03-18
"""

from alembic import op
import sqlalchemy as sa

revision = '0016_p2_auth_audit'
down_revision = '0015_inventory_check_transfer'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'user',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('is_superuser', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_user_username', 'user', ['username'], unique=True)
    op.create_index('ix_user_display_name', 'user', ['display_name'], unique=False)
    op.create_index('ix_user_status', 'user', ['status'], unique=False)
    op.create_index('ix_user_is_superuser', 'user', ['is_superuser'], unique=False)
    op.create_index('ix_user_created_at', 'user', ['created_at'], unique=False)

    op.create_table(
        'role',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('code', sa.String(length=50), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_role_code', 'role', ['code'], unique=True)
    op.create_index('ix_role_name', 'role', ['name'], unique=False)
    op.create_index('ix_role_status', 'role', ['status'], unique=False)
    op.create_index('ix_role_created_at', 'role', ['created_at'], unique=False)

    op.create_table(
        'permission',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('code', sa.String(length=80), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('resource', sa.String(length=50), nullable=False),
        sa.Column('action', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_permission_code', 'permission', ['code'], unique=True)
    op.create_index('ix_permission_name', 'permission', ['name'], unique=False)
    op.create_index('ix_permission_resource', 'permission', ['resource'], unique=False)
    op.create_index('ix_permission_action', 'permission', ['action'], unique=False)
    op.create_index('ix_permission_created_at', 'permission', ['created_at'], unique=False)

    op.create_table(
        'user_role',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
        sa.ForeignKeyConstraint(['role_id'], ['role.id']),
    )
    op.create_index('ix_user_role_user_id', 'user_role', ['user_id'], unique=False)
    op.create_index('ix_user_role_role_id', 'user_role', ['role_id'], unique=False)

    op.create_table(
        'role_permission',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.Column('permission_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['role_id'], ['role.id']),
        sa.ForeignKeyConstraint(['permission_id'], ['permission.id']),
    )
    op.create_index('ix_role_permission_role_id', 'role_permission', ['role_id'], unique=False)
    op.create_index('ix_role_permission_permission_id', 'role_permission', ['permission_id'], unique=False)

    op.create_table(
        'audit_log',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('actor_user_id', sa.Integer(), nullable=True),
        sa.Column('actor_name', sa.String(length=100), nullable=False, server_default='system'),
        sa.Column('action', sa.String(length=80), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=False),
        sa.Column('resource_id', sa.Integer(), nullable=True),
        sa.Column('detail', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['actor_user_id'], ['user.id']),
    )
    op.create_index('ix_audit_log_actor_user_id', 'audit_log', ['actor_user_id'], unique=False)
    op.create_index('ix_audit_log_actor_name', 'audit_log', ['actor_name'], unique=False)
    op.create_index('ix_audit_log_action', 'audit_log', ['action'], unique=False)
    op.create_index('ix_audit_log_resource_type', 'audit_log', ['resource_type'], unique=False)
    op.create_index('ix_audit_log_resource_id', 'audit_log', ['resource_id'], unique=False)
    op.create_index('ix_audit_log_created_at', 'audit_log', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_audit_log_created_at', table_name='audit_log')
    op.drop_index('ix_audit_log_resource_id', table_name='audit_log')
    op.drop_index('ix_audit_log_resource_type', table_name='audit_log')
    op.drop_index('ix_audit_log_action', table_name='audit_log')
    op.drop_index('ix_audit_log_actor_name', table_name='audit_log')
    op.drop_index('ix_audit_log_actor_user_id', table_name='audit_log')
    op.drop_table('audit_log')

    op.drop_index('ix_role_permission_permission_id', table_name='role_permission')
    op.drop_index('ix_role_permission_role_id', table_name='role_permission')
    op.drop_table('role_permission')

    op.drop_index('ix_user_role_role_id', table_name='user_role')
    op.drop_index('ix_user_role_user_id', table_name='user_role')
    op.drop_table('user_role')

    op.drop_index('ix_permission_created_at', table_name='permission')
    op.drop_index('ix_permission_action', table_name='permission')
    op.drop_index('ix_permission_resource', table_name='permission')
    op.drop_index('ix_permission_name', table_name='permission')
    op.drop_index('ix_permission_code', table_name='permission')
    op.drop_table('permission')

    op.drop_index('ix_role_created_at', table_name='role')
    op.drop_index('ix_role_status', table_name='role')
    op.drop_index('ix_role_name', table_name='role')
    op.drop_index('ix_role_code', table_name='role')
    op.drop_table('role')

    op.drop_index('ix_user_created_at', table_name='user')
    op.drop_index('ix_user_is_superuser', table_name='user')
    op.drop_index('ix_user_status', table_name='user')
    op.drop_index('ix_user_display_name', table_name='user')
    op.drop_index('ix_user_username', table_name='user')
    op.drop_table('user')
