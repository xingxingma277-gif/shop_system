"""p0 purchase supplier warehouse and inventory warehouse dimension

Revision ID: 0012_purchase_supplier_warehouse_p0
Revises: 0011_order_flow_delivery_fields
Create Date: 2026-03-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = '0012_purchase_supplier_warehouse_p0'
down_revision = '0011_order_flow_delivery_fields'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'supplier',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('code', sa.String(length=30), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('contact_name', sa.String(length=60), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_supplier_code', 'supplier', ['code'], unique=True)
    op.create_index('ix_supplier_name', 'supplier', ['name'], unique=False)
    op.create_index('ix_supplier_status', 'supplier', ['status'], unique=False)

    op.create_table(
        'warehouse',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('code', sa.String(length=30), nullable=False),
        sa.Column('name', sa.String(length=120), nullable=False),
        sa.Column('address', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='ACTIVE'),
        sa.Column('is_default', sa.Boolean(), nullable=False, server_default=sa.text('0')),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    op.create_index('ix_warehouse_code', 'warehouse', ['code'], unique=True)
    op.create_index('ix_warehouse_name', 'warehouse', ['name'], unique=False)
    op.create_index('ix_warehouse_status', 'warehouse', ['status'], unique=False)
    op.create_index('ix_warehouse_is_default', 'warehouse', ['is_default'], unique=False)

    op.create_table(
        'purchase',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('purchase_no', sa.String(length=30), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('warehouse_id', sa.Integer(), nullable=False),
        sa.Column('purchase_date', sa.DateTime(), nullable=False),
        sa.Column('status', sa.String(length=30), nullable=False, server_default='DRAFT'),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('total_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('paid_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('ap_amount', sa.Float(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['supplier_id'], ['supplier.id']),
        sa.ForeignKeyConstraint(['warehouse_id'], ['warehouse.id']),
    )
    op.create_index('ix_purchase_purchase_no', 'purchase', ['purchase_no'], unique=True)
    op.create_index('ix_purchase_supplier_id', 'purchase', ['supplier_id'], unique=False)
    op.create_index('ix_purchase_warehouse_id', 'purchase', ['warehouse_id'], unique=False)
    op.create_index('ix_purchase_status', 'purchase', ['status'], unique=False)
    op.create_index('ix_purchase_supplier_date_desc', 'purchase', ['supplier_id', sa.text('purchase_date DESC')], unique=False)

    op.create_table(
        'purchase_item',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('purchase_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('qty', sa.Float(), nullable=False),
        sa.Column('received_qty', sa.Float(), nullable=False, server_default='0'),
        sa.Column('unit_cost', sa.Float(), nullable=False),
        sa.Column('line_total', sa.Float(), nullable=False, server_default='0'),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['purchase_id'], ['purchase.id']),
        sa.ForeignKeyConstraint(['product_id'], ['product.id']),
    )
    op.create_index('ix_purchase_item_purchase_id', 'purchase_item', ['purchase_id'], unique=False)
    op.create_index('ix_purchase_item_product_id', 'purchase_item', ['product_id'], unique=False)

    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [c['name'] for c in inspector.get_columns('inventory_txn')]
    if 'warehouse_id' not in columns:
        op.add_column('inventory_txn', sa.Column('warehouse_id', sa.Integer(), nullable=True))
        op.create_foreign_key('fk_inventory_txn_warehouse_id', 'inventory_txn', 'warehouse', ['warehouse_id'], ['id'])
        op.create_index('ix_inventory_txn_warehouse_id', 'inventory_txn', ['warehouse_id'], unique=False)

    op.execute("INSERT INTO warehouse (code, name, address, status, is_default, created_at) VALUES ('MAIN', '默认仓库', NULL, 'ACTIVE', 1, CURRENT_TIMESTAMP)")


def downgrade() -> None:
    with op.batch_alter_table('inventory_txn') as batch_op:
        batch_op.drop_index('ix_inventory_txn_warehouse_id')
        batch_op.drop_constraint('fk_inventory_txn_warehouse_id', type_='foreignkey')
        batch_op.drop_column('warehouse_id')

    op.drop_index('ix_purchase_item_product_id', table_name='purchase_item')
    op.drop_index('ix_purchase_item_purchase_id', table_name='purchase_item')
    op.drop_table('purchase_item')

    op.drop_index('ix_purchase_supplier_date_desc', table_name='purchase')
    op.drop_index('ix_purchase_status', table_name='purchase')
    op.drop_index('ix_purchase_warehouse_id', table_name='purchase')
    op.drop_index('ix_purchase_supplier_id', table_name='purchase')
    op.drop_index('ix_purchase_purchase_no', table_name='purchase')
    op.drop_table('purchase')

    op.drop_index('ix_warehouse_is_default', table_name='warehouse')
    op.drop_index('ix_warehouse_status', table_name='warehouse')
    op.drop_index('ix_warehouse_name', table_name='warehouse')
    op.drop_index('ix_warehouse_code', table_name='warehouse')
    op.drop_table('warehouse')

    op.drop_index('ix_supplier_status', table_name='supplier')
    op.drop_index('ix_supplier_name', table_name='supplier')
    op.drop_index('ix_supplier_code', table_name='supplier')
    op.drop_table('supplier')
