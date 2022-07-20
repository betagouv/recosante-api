"""Ajout évenement dans Recommandation

Revision ID: 7739c55cf576
Revises: ad12ab0c9e74
Create Date: 2022-07-20 17:35:02.482039

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7739c55cf576'
down_revision = 'ad12ab0c9e74'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('qa_evenement', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('recommandation', 'qa_evenement')
