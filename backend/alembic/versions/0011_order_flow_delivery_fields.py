"""order flow delivery fields and order type

Revision ID: 0011_order_flow_delivery_fields
Revises: 0010_order_stages_payment_scenes
Create Date: 2026-03-17
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0011_order_flow_delivery_fields"
down_revision = "0010_order_stages_payment_scenes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    sale_columns = [col['name'] for col in inspector.get_columns('sale')]

    if 'order_type' not in sale_columns:
        op.add_column('sale', sa.Column('order_type', sa.String(length=20), nullable=False, server_default='sale_direct'))
        op.create_index('ix_sale_order_type', 'sale', ['order_type'], unique=False)

    if 'needs_delivery' not in sale_columns:
        op.add_column('sale', sa.Column('needs_delivery', sa.Boolean(), nullable=False, server_default=sa.text('0')))

    if 'receiver_name' not in sale_columns:
        op.add_column('sale', sa.Column('receiver_name', sa.String(length=100), nullable=True))
    if 'receiver_phone' not in sale_columns:
        op.add_column('sale', sa.Column('receiver_phone', sa.String(length=50), nullable=True))
    if 'receiver_address' not in sale_columns:
        op.add_column('sale', sa.Column('receiver_address', sa.String(length=255), nullable=True))
    if 'delivery_note' not in sale_columns:
        op.add_column('sale', sa.Column('delivery_note', sa.String(length=255), nullable=True))
    if 'sale_confirmed_at' not in sale_columns:
        op.add_column('sale', sa.Column('sale_confirmed_at', sa.DateTime(), nullable=True))
    if 'delivered_at' not in sale_columns:
        op.add_column('sale', sa.Column('delivered_at', sa.DateTime(), nullable=True))

    op.execute("UPDATE sale SET order_type='quote' WHERE order_stage='QUOTE'")
    op.execute("UPDATE sale SET needs_delivery=1 WHERE delivery_status IN ('PENDING','GENERATED','SHIPPED','SIGNED')")


def downgrade() -> None:
    with op.batch_alter_table('sale') as batch_op:
        batch_op.drop_column('delivered_at')
        batch_op.drop_column('sale_confirmed_at')
        batch_op.drop_column('delivery_note')
        batch_op.drop_column('receiver_address')
        batch_op.drop_column('receiver_phone')
        batch_op.drop_column('receiver_name')
        batch_op.drop_column('needs_delivery')
        batch_op.drop_index('ix_sale_order_type')
        batch_op.drop_column('order_type')
