"""auth token sessions

Revision ID: 0017_auth_token_sessions
Revises: 0016_p2_auth_audit
Create Date: 2026-03-18
"""

from alembic import op
import sqlalchemy as sa

revision = '0017_auth_token_sessions'
down_revision = '0016_p2_auth_audit'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'auth_token',
        sa.Column('id', sa.Integer(), primary_key=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.String(length=128), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id']),
    )
    op.create_index('ix_auth_token_user_id', 'auth_token', ['user_id'], unique=False)
    op.create_index('ix_auth_token_token', 'auth_token', ['token'], unique=True)
    op.create_index('ix_auth_token_expires_at', 'auth_token', ['expires_at'], unique=False)
    op.create_index('ix_auth_token_created_at', 'auth_token', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_auth_token_created_at', table_name='auth_token')
    op.drop_index('ix_auth_token_expires_at', table_name='auth_token')
    op.drop_index('ix_auth_token_token', table_name='auth_token')
    op.drop_index('ix_auth_token_user_id', table_name='auth_token')
    op.drop_table('auth_token')
