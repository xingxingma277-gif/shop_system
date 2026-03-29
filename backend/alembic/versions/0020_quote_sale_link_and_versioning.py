"""quote sale link and versioning

Revision ID: 0020_quote_sale_link_and_versioning
Revises: 0019_seed_core_permissions
Create Date: 2026-03-29
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


revision = '0020_quote_sale_link_and_versioning'
down_revision = '0019_seed_core_permissions'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    sale_columns = {col['name'] for col in inspector.get_columns('sale')}
    sale_indexes = {idx['name'] for idx in inspector.get_indexes('sale')}
    sale_fks = inspector.get_foreign_keys('sale')
    has_source_quote_fk = any(fk.get('referred_table') == 'sale' and fk.get('constrained_columns') == ['source_quote_id'] for fk in sale_fks)

    if 'source_quote_id' not in sale_columns:
        op.add_column('sale', sa.Column('source_quote_id', sa.Integer(), nullable=True))
    if 'quote_status' not in sale_columns:
        op.add_column('sale', sa.Column('quote_status', sa.String(length=20), nullable=True))
    if 'updated_at' not in sale_columns:
        op.add_column('sale', sa.Column('updated_at', sa.DateTime(), nullable=True))

    if 'ix_sale_source_quote_id' not in sale_indexes:
        op.create_index('ix_sale_source_quote_id', 'sale', ['source_quote_id'], unique=False)
    if 'ix_sale_quote_status' not in sale_indexes:
        op.create_index('ix_sale_quote_status', 'sale', ['quote_status'], unique=False)

    if conn.dialect.name != 'sqlite' and not has_source_quote_fk:
        op.create_foreign_key('fk_sale_source_quote_id_sale', 'sale', 'sale', ['source_quote_id'], ['id'])

    op.execute("UPDATE sale SET quote_status='SUBMITTED' WHERE order_stage='QUOTE' AND (quote_status IS NULL OR quote_status='')")
    op.execute("UPDATE sale SET updated_at=created_at WHERE updated_at IS NULL")


def downgrade():
    conn = op.get_bind()
    inspector = inspect(conn)
    sale_indexes = {idx['name'] for idx in inspector.get_indexes('sale')}
    sale_columns = {col['name'] for col in inspector.get_columns('sale')}
    sale_fks = {fk.get('name') for fk in inspector.get_foreign_keys('sale') if fk.get('name')}

    if conn.dialect.name != 'sqlite' and 'fk_sale_source_quote_id_sale' in sale_fks:
        op.drop_constraint('fk_sale_source_quote_id_sale', 'sale', type_='foreignkey')
    if 'ix_sale_quote_status' in sale_indexes:
        op.drop_index('ix_sale_quote_status', table_name='sale')
    if 'ix_sale_source_quote_id' in sale_indexes:
        op.drop_index('ix_sale_source_quote_id', table_name='sale')

    if 'updated_at' in sale_columns:
        op.drop_column('sale', 'updated_at')
    if 'quote_status' in sale_columns:
        op.drop_column('sale', 'quote_status')
    if 'source_quote_id' in sale_columns:
        op.drop_column('sale', 'source_quote_id')
