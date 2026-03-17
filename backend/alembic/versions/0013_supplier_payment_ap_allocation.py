"""supplier payments and AP allocation

Revision ID: 0013_supplier_payment_ap_allocation
Revises: 0012_purchase_supplier_warehouse_p0
Create Date: 2026-03-17
"""

from alembic import op
import sqlalchemy as sa

revision = '0013_supplier_payment_ap_allocation'
down_revision = '0012_purchase_supplier_warehouse_p0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'supplier_payment',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('receipt_no', sa.String(length=40), nullable=False),
        sa.Column('supplier_id', sa.Integer(), nullable=False),
        sa.Column('purchase_id', sa.Integer(), nullable=True),
        sa.Column('scene', sa.String(length=30), nullable=False, server_default='AP_PAYMENT'),
        sa.Column('method', sa.String(length=20), nullable=False, server_default='bank_transfer'),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('paid_at', sa.DateTime(), nullable=False),
        sa.Column('note', sa.String(length=255), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['supplier_id'], ['supplier.id']),
        sa.ForeignKeyConstraint(['purchase_id'], ['purchase.id']),
    )
    op.create_index('ix_supplier_payment_receipt_no', 'supplier_payment', ['receipt_no'], unique=True)
    op.create_index('ix_supplier_payment_supplier_id', 'supplier_payment', ['supplier_id'], unique=False)
    op.create_index('ix_supplier_payment_purchase_id', 'supplier_payment', ['purchase_id'], unique=False)
    op.create_index('ix_supplier_payment_scene', 'supplier_payment', ['scene'], unique=False)
    op.create_index('ix_supplier_payment_method', 'supplier_payment', ['method'], unique=False)
    op.create_index('ix_supplier_payment_paid_at', 'supplier_payment', ['paid_at'], unique=False)

    op.create_table(
        'ap_allocation',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('payment_id', sa.Integer(), nullable=False),
        sa.Column('purchase_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.ForeignKeyConstraint(['payment_id'], ['supplier_payment.id']),
        sa.ForeignKeyConstraint(['purchase_id'], ['purchase.id']),
    )
    op.create_index('ix_ap_allocation_payment_id', 'ap_allocation', ['payment_id'], unique=False)
    op.create_index('ix_ap_allocation_purchase_id', 'ap_allocation', ['purchase_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_ap_allocation_purchase_id', table_name='ap_allocation')
    op.drop_index('ix_ap_allocation_payment_id', table_name='ap_allocation')
    op.drop_table('ap_allocation')

    op.drop_index('ix_supplier_payment_paid_at', table_name='supplier_payment')
    op.drop_index('ix_supplier_payment_method', table_name='supplier_payment')
    op.drop_index('ix_supplier_payment_scene', table_name='supplier_payment')
    op.drop_index('ix_supplier_payment_purchase_id', table_name='supplier_payment')
    op.drop_index('ix_supplier_payment_supplier_id', table_name='supplier_payment')
    op.drop_index('ix_supplier_payment_receipt_no', table_name='supplier_payment')
    op.drop_table('supplier_payment')
