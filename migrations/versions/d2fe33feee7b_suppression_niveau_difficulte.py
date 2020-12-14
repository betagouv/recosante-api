"""Suppression niveau_difficulte

Revision ID: d2fe33feee7b
Revises: 5a0aaae91354
Create Date: 2020-12-14 11:15:42.393328

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd2fe33feee7b'
down_revision = '5a0aaae91354'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('recommandation', 'niveau_difficulte')


def downgrade():
    op.add_column('recommandation', sa.Column('niveau_difficulte', sa.VARCHAR(), autoincrement=False, nullable=True))
