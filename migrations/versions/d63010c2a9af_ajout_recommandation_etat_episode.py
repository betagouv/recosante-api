"""Ajout recommandation etat episode

Revision ID: d63010c2a9af
Revises: 7739c55cf576
Create Date: 2022-10-26 10:35:26.660937

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd63010c2a9af'
down_revision = '7739c55cf576'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('etat_episode_pollution', sa.String(), nullable=True))


def downgrade():
    op.drop_column('recommandation', 'etat_episode_pollution')
