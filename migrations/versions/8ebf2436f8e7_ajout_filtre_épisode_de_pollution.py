"""Ajout filtre épisode de pollution

Revision ID: 8ebf2436f8e7
Revises: b80f126e89b2
Create Date: 2020-12-14 12:21:13.194232

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8ebf2436f8e7'
down_revision = 'b80f126e89b2'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('episode_pollution', sa.BOOLEAN(), nullable=True))


def downgrade():
    op.drop_column('recommandation', 'episode_pollution')
