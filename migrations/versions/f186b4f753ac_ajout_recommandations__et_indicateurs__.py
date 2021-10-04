"""Ajout recommandations_* et indicateurs_* dans inscription

Revision ID: f186b4f753ac
Revises: c9dbc97d160a
Create Date: 2021-09-22 17:30:56.151251

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f186b4f753ac'
down_revision = 'c9dbc97d160a'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('inscription', sa.Column('indicateurs', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('inscription', sa.Column('indicateurs_frequence', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('inscription', sa.Column('indicateurs_media', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('inscription', sa.Column('recommandations_actives', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('inscription', sa.Column('recommandations_frequence', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('inscription', sa.Column('recommandations_media', postgresql.ARRAY(sa.String()), nullable=True))


def downgrade():
    op.drop_column('inscription', 'recommandations_media')
    op.drop_column('inscription', 'recommandations_frequence')
    op.drop_column('inscription', 'recommandations_actives')
    op.drop_column('inscription', 'indicateurs_media')
    op.drop_column('inscription', 'indicateurs_frequence')
    op.drop_column('inscription', 'indicateurs')