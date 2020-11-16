"""Ajout des colonnes appliquee, avis sur les newsletter

Revision ID: 8df6a9a4bab1
Revises: 20b84cf5a91f
Create Date: 2020-11-13 10:05:56.850759

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '8df6a9a4bab1'
down_revision = '20b84cf5a91f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter', sa.Column('appliquee', sa.Boolean(), nullable=True))
    op.add_column('newsletter', sa.Column('avis', sa.String(), nullable=True))


def downgrade():
    op.drop_column('newsletter', 'avis')
    op.drop_column('newsletter', 'appliquee')