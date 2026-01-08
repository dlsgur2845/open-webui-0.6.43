"""add token_jti to auth

Revision ID: a1b2c3d4e5f6
Revises: d31026856c01
Create Date: 2026-01-08 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = 'c440947495f3'
branch_labels = None
depends_on = None

def upgrade():
    # Attempt to add the column.
    # Note: If running on SQLite, this works for simple columns.
    # Open WebUI supports SQLite and PostgreSQL.
    # 'auth' table name is lowercase in models/auths.py (__tablename__ = "auth")
    op.add_column('auth', sa.Column('token_jti', sa.String(), nullable=True))

def downgrade():
    op.drop_column('auth', 'token_jti')
