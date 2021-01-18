"""Ajout champ deactivation_date

Revision ID: a504dd88a502
Revises: c7ffae85f057
Create Date: 2021-01-15 15:48:51.893410

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a504dd88a502'
down_revision = 'c7ffae85f057'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('inscription', sa.Column('deactivation_date', sa.Date(), nullable=True))


def downgrade():
    op.drop_column('inscription', 'deactivation_date')
