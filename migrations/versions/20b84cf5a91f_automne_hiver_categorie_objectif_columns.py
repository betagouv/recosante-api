"""automne, hiver, categorie, objectif columns

Revision ID: 20b84cf5a91f
Revises: e6fde44bb7d3
Create Date: 2020-11-12 17:03:20.579726

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20b84cf5a91f'
down_revision = 'e6fde44bb7d3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('automne', sa.BOOLEAN(), nullable=True))
    op.add_column('recommandation', sa.Column('hiver', sa.BOOLEAN(), nullable=True))


def downgrade():
    op.drop_column('recommandation', 'hiver')
    op.drop_column('recommandation', 'automne')