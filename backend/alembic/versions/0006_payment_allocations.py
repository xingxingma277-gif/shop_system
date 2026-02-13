"""payment allocations and nullable payment.sale_id

Revision ID: 0006_payment_allocations
Revises: 0005_payment_receipt_no
Create Date: 2026-02-13
"""

from alembic import op
import sqlalchemy as sa

revision = "0006_payment_allocations"
down_revision = "0005_payment_receipt_no"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("payment") as batch_op:
        batch_op.alter_column("sale_id", existing_type=sa.Integer(), nullable=True)

    op.create_table(
        "payment_allocation",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("payment_id", sa.Integer(), sa.ForeignKey("payment.id"), nullable=False),
        sa.Column("sale_id", sa.Integer(), sa.ForeignKey("sale.id"), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
    )
    op.create_index("ix_payment_allocation_payment_id", "payment_allocation", ["payment_id"], unique=False)
    op.create_index("ix_payment_allocation_sale_id", "payment_allocation", ["sale_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_payment_allocation_sale_id", table_name="payment_allocation")
    op.drop_index("ix_payment_allocation_payment_id", table_name="payment_allocation")
    op.drop_table("payment_allocation")

    with op.batch_alter_table("payment") as batch_op:
        batch_op.alter_column("sale_id", existing_type=sa.Integer(), nullable=False)
