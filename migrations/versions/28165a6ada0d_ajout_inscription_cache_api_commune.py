"""Ajout inscription.cache_api_commune

Revision ID: 28165a6ada0d
Revises: 930a6874fe56
Create Date: 2020-10-07 15:05:00.035176

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '28165a6ada0d'
down_revision = '930a6874fe56'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('inscription', sa.Column('cache_api_commune', sa.String(), nullable=True))

def downgrade():
    op.drop_column('inscription', 'cache_api_commune')
