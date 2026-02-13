"""add sale settlement fields

Revision ID: 0007_sale_settlement_fields
Revises: 0006_payment_allocations
Create Date: 2026-02-13
"""

from alembic import op
import sqlalchemy as sa

revision = "0007_sale_settlement_fields"
down_revision = "0006_payment_allocations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("sale") as batch_op:
        batch_op.add_column(sa.Column("settlement_status", sa.String(length=20), nullable=False, server_default="UNPAID"))
        batch_op.add_column(sa.Column("payment_method", sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column("payment_note", sa.String(length=255), nullable=True))
        batch_op.create_index("ix_sale_settlement_status", ["settlement_status"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("sale") as batch_op:
        batch_op.drop_index("ix_sale_settlement_status")
        batch_op.drop_column("payment_note")
        batch_op.drop_column("payment_method")
        batch_op.drop_column("settlement_status")
