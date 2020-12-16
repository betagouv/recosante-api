"""Ajout filtre population_generale

Revision ID: d3f98d93885d
Revises: 8ebf2436f8e7
Create Date: 2020-12-16 17:19:22.672638

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd3f98d93885d'
down_revision = '8ebf2436f8e7'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('population_generale', sa.BOOLEAN(), nullable=True))


def downgrade():
    op.drop_column('recommandation', 'population_generale')
