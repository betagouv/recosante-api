"""Ajout qualif aux newsletters

Revision ID: 3dfc4940599e
Revises: d3f98d93885d
Create Date: 2021-01-06 15:26:18.437335

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3dfc4940599e'
down_revision = 'd3f98d93885d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter', sa.Column('qualif', sa.String(), nullable=True))


def downgrade():
    op.drop_column('newsletter', 'qualif')
