"""order stages, payment scenes, inventory check

Revision ID: 0010_order_stages_payment_scenes
Revises: 0009_inventory_and_product_ext
Create Date: 2026-03-15
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0010_order_stages_payment_scenes"
down_revision = "0009_inventory_and_product_ext"
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)

    # 1. Payment 增加 scene (场景) - 检查是否已存在
    payment_columns = [col['name'] for col in inspector.get_columns('payment')]

    if 'scene' not in payment_columns:
        op.add_column("payment",
                      sa.Column("scene", sa.String(length=30), nullable=False, server_default="ORDER_CHECKOUT"))
        op.create_index("ix_payment_scene", "payment", ["scene"], unique=False)

    # 清洗历史数据：将有分配记录的，或者反结算的付款标记为后置还款或调整
    op.execute(
        "UPDATE payment SET scene = 'POST_SALE_REPAYMENT' WHERE id IN (SELECT payment_id FROM payment_allocation)")
    op.execute("UPDATE payment SET scene = 'POST_SALE_REPAYMENT' WHERE pay_type = 'settlement_adjust'")
    op.execute("UPDATE payment SET scene = 'REVERSAL' WHERE pay_type = 'settlement_reverse'")

    # 2. Sale 增加业务生命周期字段 - 检查是否已存在
    sale_columns = [col['name'] for col in inspector.get_columns('sale')]

    if 'order_stage' not in sale_columns:
        op.add_column("sale",
                      sa.Column("order_stage", sa.String(length=30), nullable=False, server_default="SALE_CONFIRMED"))
        op.create_index("ix_sale_order_stage", "sale", ["order_stage"], unique=False)

    if 'inventory_effected' not in sale_columns:
        op.add_column("sale",
                      sa.Column("inventory_effected", sa.Boolean(), nullable=False, server_default=sa.text("1")))

    if 'delivery_status' not in sale_columns:
        op.add_column("sale", sa.Column("delivery_status", sa.String(length=30), nullable=False, server_default="NONE"))

    if 'quote_confirmed_at' not in sale_columns:
        op.add_column("sale", sa.Column("quote_confirmed_at", sa.DateTime(), nullable=True))

    if 'delivery_created_at' not in sale_columns:
        op.add_column("sale", sa.Column("delivery_created_at", sa.DateTime(), nullable=True))


def downgrade() -> None:
    # downgrade 在 SQLite 中直接 drop column 支持不完善，但这里为了保持结构完整给出基于 batch 的回滚
    with op.batch_alter_table("sale") as batch_op:
        batch_op.drop_index("ix_sale_order_stage")
        batch_op.drop_column("delivery_created_at")
        batch_op.drop_column("quote_confirmed_at")
        batch_op.drop_column("delivery_status")
        batch_op.drop_column("inventory_effected")
        batch_op.drop_column("order_stage")

    with op.batch_alter_table("payment") as batch_op:
        batch_op.drop_index("ix_payment_scene")
        batch_op.drop_column("scene")