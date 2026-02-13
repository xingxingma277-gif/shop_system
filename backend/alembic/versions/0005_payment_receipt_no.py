"""add payment receipt no

Revision ID: 0005_payment_receipt_no
Revises: 0004_sale_no_and_statement_filters
Create Date: 2026-02-13
"""

from alembic import op
import sqlalchemy as sa

revision = "0005_payment_receipt_no"
down_revision = "0004_sale_no_and_statement_filters"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("payment") as batch_op:
        batch_op.add_column(sa.Column("receipt_no", sa.String(length=40), nullable=True))
        batch_op.create_index("ix_payment_receipt_no", ["receipt_no"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("payment") as batch_op:
        batch_op.drop_index("ix_payment_receipt_no")
        batch_op.drop_column("receipt_no")
