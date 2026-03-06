"""sale operation audit and biz status

Revision ID: 0008_sale_operation_and_status
Revises: 0007_sale_settlement_fields
Create Date: 2026-03-06
"""

from alembic import op
import sqlalchemy as sa

revision = "0008_sale_operation_and_status"
down_revision = "0007_sale_settlement_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("sale") as batch_op:
        batch_op.add_column(sa.Column("biz_status", sa.String(length=20), nullable=False, server_default="NORMAL"))
        batch_op.create_index("ix_sale_biz_status", ["biz_status"], unique=False)

    op.create_table(
        "sale_operation",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("sale_id", sa.Integer(), sa.ForeignKey("sale.id"), nullable=False),
        sa.Column("op_type", sa.String(length=30), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False, server_default="0"),
        sa.Column("note", sa.String(length=500), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_sale_operation_sale_id", "sale_operation", ["sale_id"], unique=False)
    op.create_index("ix_sale_operation_op_type", "sale_operation", ["op_type"], unique=False)
    op.create_index("ix_sale_operation_created_at", "sale_operation", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_sale_operation_created_at", table_name="sale_operation")
    op.drop_index("ix_sale_operation_op_type", table_name="sale_operation")
    op.drop_index("ix_sale_operation_sale_id", table_name="sale_operation")
    op.drop_table("sale_operation")

    with op.batch_alter_table("sale") as batch_op:
        batch_op.drop_index("ix_sale_biz_status")
        batch_op.drop_column("biz_status")
