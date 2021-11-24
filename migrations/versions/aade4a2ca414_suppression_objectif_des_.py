"""Suppression objectif des recommandationss

Revision ID: aade4a2ca414
Revises: 1a1ec28e5d13
Create Date: 2021-11-24 14:18:41.934120

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aade4a2ca414'
down_revision = '1a1ec28e5d13'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('recommandation', 'objectif')


def downgrade():
    op.add_column('recommandation', sa.Column('objectif', sa.VARCHAR(), autoincrement=False, nullable=True))
