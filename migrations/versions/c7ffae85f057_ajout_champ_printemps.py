"""Ajout champ printemps

Revision ID: c7ffae85f057
Revises: 674484c70076
Create Date: 2021-01-13 16:54:51.264707

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c7ffae85f057'
down_revision = '674484c70076'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('printemps', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('recommandation', 'printemps')
