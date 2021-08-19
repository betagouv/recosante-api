"""Ajout recommandations, notifications à inscription

Revision ID: ed7fe5215ef4
Revises: 6693ab247cb9
Create Date: 2021-08-19 12:47:40.027362

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ed7fe5215ef4'
down_revision = '6693ab247cb9'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('inscription', sa.Column('notifications', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('inscription', sa.Column('recommandations', postgresql.ARRAY(sa.String()), nullable=True))


def downgrade():
    op.drop_column('inscription', 'recommandations')
    op.drop_column('inscription', 'notifications')
