"""inventory and product extensions

Revision ID: 0009_inventory_and_product_ext
Revises: 0008_sale_operation_and_status
Create Date: 2026-03-06
"""

from alembic import op
import sqlalchemy as sa

revision = "0009_inventory_and_product_ext"
down_revision = "0008_sale_operation_and_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("product") as batch_op:
        batch_op.add_column(sa.Column("standard_cost", sa.Float(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("stock_quantity", sa.Float(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("stock_warning_threshold", sa.Float(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("category", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("brand", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("barcode", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("spec", sa.String(length=120), nullable=True))
        batch_op.add_column(sa.Column("image", sa.String(length=500), nullable=True))
        batch_op.create_index("ix_product_category", ["category"], unique=False)
        batch_op.create_index("ix_product_brand", ["brand"], unique=False)
        batch_op.create_index("ix_product_barcode", ["barcode"], unique=False)

    op.create_table(
        "inventory_txn",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("product_id", sa.Integer(), sa.ForeignKey("product.id"), nullable=False),
        sa.Column("change_qty", sa.Float(), nullable=False),
        sa.Column("after_qty", sa.Float(), nullable=False),
        sa.Column("biz_type", sa.String(length=30), nullable=False),
        sa.Column("biz_id", sa.Integer(), nullable=True),
        sa.Column("sale_id", sa.Integer(), sa.ForeignKey("sale.id"), nullable=True),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_inventory_txn_product_id", "inventory_txn", ["product_id"], unique=False)
    op.create_index("ix_inventory_txn_biz_type", "inventory_txn", ["biz_type"], unique=False)
    op.create_index("ix_inventory_txn_biz_id", "inventory_txn", ["biz_id"], unique=False)
    op.create_index("ix_inventory_txn_sale_id", "inventory_txn", ["sale_id"], unique=False)
    op.create_index("ix_inventory_txn_created_at", "inventory_txn", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_inventory_txn_created_at", table_name="inventory_txn")
    op.drop_index("ix_inventory_txn_sale_id", table_name="inventory_txn")
    op.drop_index("ix_inventory_txn_biz_id", table_name="inventory_txn")
    op.drop_index("ix_inventory_txn_biz_type", table_name="inventory_txn")
    op.drop_index("ix_inventory_txn_product_id", table_name="inventory_txn")
    op.drop_table("inventory_txn")

    with op.batch_alter_table("product") as batch_op:
        batch_op.drop_index("ix_product_barcode")
        batch_op.drop_index("ix_product_brand")
        batch_op.drop_index("ix_product_category")
        batch_op.drop_column("image")
        batch_op.drop_column("spec")
        batch_op.drop_column("barcode")
        batch_op.drop_column("brand")
        batch_op.drop_column("category")
        batch_op.drop_column("stock_warning_threshold")
        batch_op.drop_column("stock_quantity")
        batch_op.drop_column("standard_cost")
