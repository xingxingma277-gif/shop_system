"""sales checkout buyers

Revision ID: 0003_sales_checkout_buyers
Revises: 0002_contacts_payments
Create Date: 2026-02-13
"""

from alembic import op
import sqlalchemy as sa

revision = "0003_sales_checkout_buyers"
down_revision = "0002_contacts_payments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("customer") as batch_op:
        batch_op.add_column(sa.Column("type", sa.String(length=20), nullable=False, server_default="company"))
        batch_op.add_column(sa.Column("contact_name", sa.String(length=100), nullable=False, server_default=""))
        batch_op.alter_column("phone", existing_type=sa.String(length=50), nullable=False, server_default="")
        batch_op.alter_column("address", existing_type=sa.String(length=255), nullable=False, server_default="")
        batch_op.create_index("ix_customer_type", ["type"], unique=False)

    op.execute("UPDATE customer SET contact_name = COALESCE(NULLIF(name,''), '未填写') WHERE contact_name = ''")

    with op.batch_alter_table("sale") as batch_op:
        batch_op.add_column(sa.Column("buyer_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("project", sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column("paid_amount", sa.Float(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("ar_amount", sa.Float(), nullable=False, server_default="0"))
        batch_op.add_column(sa.Column("payment_status", sa.String(length=20), nullable=False, server_default="unpaid"))
        batch_op.create_index("ix_sale_buyer_id", ["buyer_id"], unique=False)
        batch_op.create_index("ix_sale_payment_status", ["payment_status"], unique=False)
        batch_op.create_foreign_key("fk_sale_buyer_id_customer_contact", "customer_contact", ["buyer_id"], ["id"])

    op.execute("UPDATE sale SET project = project_name WHERE project IS NULL")
    op.execute("UPDATE sale SET buyer_id = contact_id WHERE buyer_id IS NULL")
    op.execute("UPDATE sale SET paid_amount = 0 WHERE paid_amount IS NULL")
    op.execute("UPDATE sale SET ar_amount = total_amount - paid_amount WHERE ar_amount IS NULL OR ar_amount = 0")

    with op.batch_alter_table("sale_item") as batch_op:
        batch_op.add_column(sa.Column("unit_price", sa.Float(), nullable=False, server_default="0"))
    op.execute("UPDATE sale_item SET unit_price = sold_price WHERE unit_price = 0")

    with op.batch_alter_table("payment") as batch_op:
        batch_op.add_column(sa.Column("pay_type", sa.String(length=20), nullable=False, server_default="partial"))
        batch_op.create_index("ix_payment_pay_type", ["pay_type"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("payment") as batch_op:
        batch_op.drop_index("ix_payment_pay_type")
        batch_op.drop_column("pay_type")

    with op.batch_alter_table("sale_item") as batch_op:
        batch_op.drop_column("unit_price")

    with op.batch_alter_table("sale") as batch_op:
        batch_op.drop_constraint("fk_sale_buyer_id_customer_contact", type_="foreignkey")
        batch_op.drop_index("ix_sale_payment_status")
        batch_op.drop_index("ix_sale_buyer_id")
        batch_op.drop_column("payment_status")
        batch_op.drop_column("ar_amount")
        batch_op.drop_column("paid_amount")
        batch_op.drop_column("project")
        batch_op.drop_column("buyer_id")

    with op.batch_alter_table("customer") as batch_op:
        batch_op.drop_index("ix_customer_type")
        batch_op.alter_column("address", existing_type=sa.String(length=255), nullable=True, server_default=None)
        batch_op.alter_column("phone", existing_type=sa.String(length=50), nullable=True, server_default=None)
        batch_op.drop_column("contact_name")
        batch_op.drop_column("type")
