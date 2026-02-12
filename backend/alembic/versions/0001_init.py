"""init tables

Revision ID: 0001_init
Revises:
Create Date: 2026-02-04

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_customer_name", "customer", ["name"])
    op.create_index("ix_customer_is_active", "customer", ["is_active"])

    op.create_table(
        "product",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("sku", sa.String(length=80), nullable=True),
        sa.Column("unit", sa.String(length=20), nullable=True),
        sa.Column("standard_price", sa.Float(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_product_name", "product", ["name"])
    op.create_index("ix_product_sku", "product", ["sku"])
    op.create_index("ix_product_is_active", "product", ["is_active"])

    op.create_table(
        "sale",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), nullable=False),
        sa.Column("sale_date", sa.DateTime(), nullable=False),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("total_amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["customer_id"], ["customer.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_sale_customer_id", "sale", ["customer_id"])
    op.create_index("ix_sale_sale_date", "sale", ["sale_date"])
    # 关键索引：customer_id + sale_date desc
    op.create_index(
        "ix_sale_customer_saledate_desc",
        "sale",
        ["customer_id", sa.text("sale_date DESC")],
    )

    op.create_table(
        "sale_item",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("sale_id", sa.Integer(), nullable=False),
        sa.Column("product_id", sa.Integer(), nullable=False),
        sa.Column("qty", sa.Float(), nullable=False),
        sa.Column("sold_price", sa.Float(), nullable=False),
        sa.Column("line_total", sa.Float(), nullable=False, server_default="0"),
        sa.Column("remark", sa.String(length=200), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["sale_id"], ["sale.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["product_id"], ["product.id"], ondelete="RESTRICT"),
    )
    op.create_index("ix_sale_item_sale_id", "sale_item", ["sale_id"])
    op.create_index("ix_sale_item_product_id", "sale_item", ["product_id"])


def downgrade() -> None:
    op.drop_index("ix_sale_item_product_id", table_name="sale_item")
    op.drop_index("ix_sale_item_sale_id", table_name="sale_item")
    op.drop_table("sale_item")

    op.drop_index("ix_sale_customer_saledate_desc", table_name="sale")
    op.drop_index("ix_sale_sale_date", table_name="sale")
    op.drop_index("ix_sale_customer_id", table_name="sale")
    op.drop_table("sale")

    op.drop_index("ix_product_is_active", table_name="product")
    op.drop_index("ix_product_sku", table_name="product")
    op.drop_index("ix_product_name", table_name="product")
    op.drop_table("product")

    op.drop_index("ix_customer_is_active", table_name="customer")
    op.drop_index("ix_customer_name", table_name="customer")
    op.drop_table("customer")
