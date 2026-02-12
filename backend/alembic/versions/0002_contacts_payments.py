"""contacts & payments

Revision ID: 0002_contacts_payments
Revises: 0001_init
Create Date: 2026-02-10
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_contacts_payments"
down_revision = "0001_init"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "customer_contact",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customer.id"), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("role", sa.String(length=20), nullable=False, server_default="维修工"),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_customer_contact_customer_id", "customer_contact", ["customer_id"], unique=False)
    op.create_index("ix_customer_contact_name", "customer_contact", ["name"], unique=False)
    op.create_index("ix_customer_contact_role", "customer_contact", ["role"], unique=False)
    op.create_index("ix_customer_contact_is_active", "customer_contact", ["is_active"], unique=False)

    # SQLite alter table needs batch mode for adding FK
    with op.batch_alter_table("sale") as batch_op:
        batch_op.add_column(sa.Column("contact_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("contact_name_snapshot", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("project_name", sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column("signed_by", sa.String(length=100), nullable=True))

        batch_op.create_index("ix_sale_contact_id", ["contact_id"], unique=False)
        batch_op.create_foreign_key(
            "fk_sale_contact_id_customer_contact",
            "customer_contact",
            ["contact_id"],
            ["id"],
        )

    op.create_table(
        "payment",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("customer_id", sa.Integer(), sa.ForeignKey("customer.id"), nullable=False),
        sa.Column("sale_id", sa.Integer(), sa.ForeignKey("sale.id"), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("method", sa.String(length=20), nullable=False, server_default="转账"),
        sa.Column("paid_at", sa.DateTime(), nullable=False),
        sa.Column("note", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_payment_customer_id", "payment", ["customer_id"], unique=False)
    op.create_index("ix_payment_sale_id", "payment", ["sale_id"], unique=False)
    op.create_index("ix_payment_paid_at", "payment", ["paid_at"], unique=False)
    op.create_index("ix_payment_method", "payment", ["method"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_payment_method", table_name="payment")
    op.drop_index("ix_payment_paid_at", table_name="payment")
    op.drop_index("ix_payment_sale_id", table_name="payment")
    op.drop_index("ix_payment_customer_id", table_name="payment")
    op.drop_table("payment")

    with op.batch_alter_table("sale") as batch_op:
        batch_op.drop_constraint("fk_sale_contact_id_customer_contact", type_="foreignkey")
        batch_op.drop_index("ix_sale_contact_id")
        batch_op.drop_column("signed_by")
        batch_op.drop_column("project_name")
        batch_op.drop_column("contact_name_snapshot")
        batch_op.drop_column("contact_id")

    op.drop_index("ix_customer_contact_is_active", table_name="customer_contact")
    op.drop_index("ix_customer_contact_role", table_name="customer_contact")
    op.drop_index("ix_customer_contact_name", table_name="customer_contact")
    op.drop_index("ix_customer_contact_customer_id", table_name="customer_contact")
    op.drop_table("customer_contact")
