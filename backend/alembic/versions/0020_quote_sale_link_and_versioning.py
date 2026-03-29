"""quote sale link and versioning

Revision ID: 0020_quote_sale_link_and_versioning
Revises: 0019_seed_core_permissions
Create Date: 2026-03-29
"""

from alembic import op
import sqlalchemy as sa


revision = '0020_quote_sale_link_and_versioning'
down_revision = '0019_seed_core_permissions'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('sale', sa.Column('source_quote_id', sa.Integer(), nullable=True))
    op.add_column('sale', sa.Column('quote_status', sa.String(length=20), nullable=True))
    op.add_column('sale', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.create_index('ix_sale_source_quote_id', 'sale', ['source_quote_id'], unique=False)
    op.create_index('ix_sale_quote_status', 'sale', ['quote_status'], unique=False)
    op.create_foreign_key('fk_sale_source_quote_id_sale', 'sale', 'sale', ['source_quote_id'], ['id'])
    op.execute("UPDATE sale SET quote_status='SUBMITTED' WHERE order_stage='QUOTE' AND quote_status IS NULL")
    op.execute("UPDATE sale SET updated_at=created_at WHERE updated_at IS NULL")


def downgrade():
    op.drop_constraint('fk_sale_source_quote_id_sale', 'sale', type_='foreignkey')
    op.drop_index('ix_sale_quote_status', table_name='sale')
    op.drop_index('ix_sale_source_quote_id', table_name='sale')
    op.drop_column('sale', 'updated_at')
    op.drop_column('sale', 'quote_status')
    op.drop_column('sale', 'source_quote_id')
