"""Ajout recommandation Indice UV

Revision ID: 37b15063d1c7
Revises: 017e76d92cfb
Create Date: 2022-01-31 11:55:08.835457

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '37b15063d1c7'
down_revision = '017e76d92cfb'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('min_indice_uv', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('recommandation', 'min_indice_uv')