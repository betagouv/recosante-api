"""Ajout potentiel radon dans les recommandations

Revision ID: 20484ad297c7
Revises: 3e3a68617ad0
Create Date: 2021-06-23 16:32:40.331253

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20484ad297c7'
down_revision = '3e3a68617ad0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('potentiel_radon', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('recommandation', 'potentiel_radon')