"""inventory adjustments module

Revision ID: 0014_inventory_adjustment
Revises: 0013_supplier_payment_ap_allocation
Create Date: 2026-03-17
"""

from alembic import op
import sqlalchemy as sa

revision = '0014_inventory_adjustment'
down_revision = '0013_supplier_payment_ap_allocation'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'inventory_adjustment',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('adj_no', sa.String(length=40), nullable=False),
        sa.Column('warehouse_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('adj_type', sa.String(length=20), nullable=False),
        sa.Column('qty', sa.Float(), nullable=False),
        sa.Column('reason', sa.String(length=255), nullable=True),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouse.id']),
        sa.ForeignKeyConstraint(['product_id'], ['product.id']),
    )
    op.create_index('ix_inventory_adjustment_adj_no', 'inventory_adjustment', ['adj_no'], unique=True)
    op.create_index('ix_inventory_adjustment_warehouse_id', 'inventory_adjustment', ['warehouse_id'], unique=False)
    op.create_index('ix_inventory_adjustment_product_id', 'inventory_adjustment', ['product_id'], unique=False)
    op.create_index('ix_inventory_adjustment_adj_type', 'inventory_adjustment', ['adj_type'], unique=False)
    op.create_index('ix_inventory_adjustment_created_at', 'inventory_adjustment', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_inventory_adjustment_created_at', table_name='inventory_adjustment')
    op.drop_index('ix_inventory_adjustment_adj_type', table_name='inventory_adjustment')
    op.drop_index('ix_inventory_adjustment_product_id', table_name='inventory_adjustment')
    op.drop_index('ix_inventory_adjustment_warehouse_id', table_name='inventory_adjustment')
    op.drop_index('ix_inventory_adjustment_adj_no', table_name='inventory_adjustment')
    op.drop_table('inventory_adjustment')
