"""Ajout radon dans la newsletter

Revision ID: 1c7b2c3e05c5
Revises: d60a45185f74
Create Date: 2021-06-23 17:39:02.845005

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1c7b2c3e05c5'
down_revision = 'd60a45185f74'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter', sa.Column('radon', sa.Integer(), nullable=True))
    op.add_column('newsletter', sa.Column('show_radon', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('newsletter', 'show_radon')
    op.drop_column('newsletter', 'radon')
