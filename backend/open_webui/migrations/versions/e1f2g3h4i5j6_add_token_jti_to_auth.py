"""add token_jti to auth

Revision ID: e1f2g3h4i5j6
Revises: d31026856c01
Create Date: 2026-01-11 22:15:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1f2g3h4i5j6'
down_revision = 'c440947495f3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('auth', sa.Column('token_jti', sa.String(), nullable=True))


def downgrade():
    op.drop_column('auth', 'token_jti')
