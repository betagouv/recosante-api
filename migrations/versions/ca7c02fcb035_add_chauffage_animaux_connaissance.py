"""Add chauffage, animaux, connaissance

Revision ID: ca7c02fcb035
Revises: 723f9ab27edf
Create Date: 2021-03-10 15:05:29.180649

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'ca7c02fcb035'
down_revision = '723f9ab27edf'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('inscription', sa.Column('animaux_domestiques', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('inscription', sa.Column('chauffage', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('inscription', sa.Column('connaissance_produit', postgresql.ARRAY(sa.String()), nullable=True))


def downgrade():
    op.drop_column('inscription', 'connaissance_produit')
    op.drop_column('inscription', 'chauffage')
    op.drop_column('inscription', 'animaux_domestiques')
