"""add sale_no and backfill

Revision ID: 0004_sale_no_and_statement_filters
Revises: 0003_sales_checkout_buyers
Create Date: 2026-02-13
"""

from alembic import op
import sqlalchemy as sa

revision = "0004_sale_no_and_statement_filters"
down_revision = "0003_sales_checkout_buyers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("sale") as batch_op:
        batch_op.add_column(sa.Column("sale_no", sa.String(length=30), nullable=True))

    conn = op.get_bind()
    rows = conn.execute(sa.text("SELECT id, sale_date FROM sale ORDER BY sale_date ASC, id ASC")).fetchall()
    seq = {}
    for row in rows:
        d = str(row.sale_date)[:10].replace("-", "") if row.sale_date else "00000000"
        seq[d] = seq.get(d, 0) + 1
        sale_no = f"SO{d}-{seq[d]:04d}"
        conn.execute(sa.text("UPDATE sale SET sale_no = :sale_no WHERE id = :id"), {"sale_no": sale_no, "id": row.id})

    with op.batch_alter_table("sale") as batch_op:
        batch_op.alter_column("sale_no", existing_type=sa.String(length=30), nullable=False, server_default="")
        batch_op.create_index("ix_sale_sale_no", ["sale_no"], unique=True)


def downgrade() -> None:
    with op.batch_alter_table("sale") as batch_op:
        batch_op.drop_index("ix_sale_sale_no")
        batch_op.drop_column("sale_no")
