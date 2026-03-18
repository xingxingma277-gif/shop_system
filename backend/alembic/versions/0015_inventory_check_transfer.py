"""inventory checks and transfers

Revision ID: 0015_inventory_check_transfer
Revises: 0014_inventory_adjustment
Create Date: 2026-03-18
"""

from alembic import op
import sqlalchemy as sa

revision = '0015_inventory_check_transfer'
down_revision = '0014_inventory_adjustment'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'inventory_check',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('check_no', sa.String(length=40), nullable=False),
        sa.Column('warehouse_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='DRAFT'),
        sa.Column('book_qty', sa.Float(), nullable=False, server_default='0'),
        sa.Column('actual_qty', sa.Float(), nullable=False, server_default='0'),
        sa.Column('diff_qty', sa.Float(), nullable=False, server_default='0'),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('posted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouse.id']),
        sa.ForeignKeyConstraint(['product_id'], ['product.id']),
    )
    op.create_index('ix_inventory_check_check_no', 'inventory_check', ['check_no'], unique=True)
    op.create_index('ix_inventory_check_warehouse_id', 'inventory_check', ['warehouse_id'], unique=False)
    op.create_index('ix_inventory_check_product_id', 'inventory_check', ['product_id'], unique=False)
    op.create_index('ix_inventory_check_status', 'inventory_check', ['status'], unique=False)
    op.create_index('ix_inventory_check_created_at', 'inventory_check', ['created_at'], unique=False)

    op.create_table(
        'inventory_transfer',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('transfer_no', sa.String(length=40), nullable=False),
        sa.Column('from_warehouse_id', sa.Integer(), nullable=False),
        sa.Column('to_warehouse_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('qty', sa.Float(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='DRAFT'),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('posted_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['from_warehouse_id'], ['warehouse.id']),
        sa.ForeignKeyConstraint(['to_warehouse_id'], ['warehouse.id']),
        sa.ForeignKeyConstraint(['product_id'], ['product.id']),
    )
    op.create_index('ix_inventory_transfer_transfer_no', 'inventory_transfer', ['transfer_no'], unique=True)
    op.create_index('ix_inventory_transfer_from_warehouse_id', 'inventory_transfer', ['from_warehouse_id'], unique=False)
    op.create_index('ix_inventory_transfer_to_warehouse_id', 'inventory_transfer', ['to_warehouse_id'], unique=False)
    op.create_index('ix_inventory_transfer_product_id', 'inventory_transfer', ['product_id'], unique=False)
    op.create_index('ix_inventory_transfer_status', 'inventory_transfer', ['status'], unique=False)
    op.create_index('ix_inventory_transfer_created_at', 'inventory_transfer', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_inventory_transfer_created_at', table_name='inventory_transfer')
    op.drop_index('ix_inventory_transfer_status', table_name='inventory_transfer')
    op.drop_index('ix_inventory_transfer_product_id', table_name='inventory_transfer')
    op.drop_index('ix_inventory_transfer_to_warehouse_id', table_name='inventory_transfer')
    op.drop_index('ix_inventory_transfer_from_warehouse_id', table_name='inventory_transfer')
    op.drop_index('ix_inventory_transfer_transfer_no', table_name='inventory_transfer')
    op.drop_table('inventory_transfer')

    op.drop_index('ix_inventory_check_created_at', table_name='inventory_check')
    op.drop_index('ix_inventory_check_status', table_name='inventory_check')
    op.drop_index('ix_inventory_check_product_id', table_name='inventory_check')
    op.drop_index('ix_inventory_check_warehouse_id', table_name='inventory_check')
    op.drop_index('ix_inventory_check_check_no', table_name='inventory_check')
    op.drop_table('inventory_check')
