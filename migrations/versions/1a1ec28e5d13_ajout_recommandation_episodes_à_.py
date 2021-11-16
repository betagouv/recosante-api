"""Ajout recommandation_episodes à newsletter

Revision ID: 1a1ec28e5d13
Revises: 71dc6f5ea5ae
Create Date: 2021-11-16 10:59:25.288677

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a1ec28e5d13'
down_revision = '71dc6f5ea5ae'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter', sa.Column('recommandation_episode_id', sa.Integer(), nullable=True))
    op.create_foreign_key('recommandation_episode_id_fkey', 'newsletter', 'recommandation', ['recommandation_episode_id'], ['id'])
    op.create_foreign_key('recommandation_episode_fkey', 'newsletter', 'recommandation', ['recommandation_id'], ['id'])


def downgrade():
    op.drop_constraint('recommandation_episode_id_fkey', 'newsletter', type_='foreignkey')
    op.drop_constraint('recommandation_episode_fkey', 'newsletter', type_='foreignkey')
    op.drop_column('newsletter', 'recommandation_episode_id')
