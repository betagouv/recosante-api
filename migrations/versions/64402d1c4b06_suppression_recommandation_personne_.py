"""Suppression Recommandation.personne_allergique

Revision ID: 64402d1c4b06
Revises: 8faff7cb2f6c
Create Date: 2021-11-24 16:12:22.563248

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '64402d1c4b06'
down_revision = '8faff7cb2f6c'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('recommandation', 'personne_allergique')


def downgrade():
    op.add_column('recommandation', sa.Column('personne_allergique', sa.BOOLEAN(), autoincrement=False, nullable=True))
