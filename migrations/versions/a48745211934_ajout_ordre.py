"""Ajout ordre

Revision ID: a48745211934
Revises: c95d1281836f
Create Date: 2021-04-21 16:23:55.011610

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a48745211934'
down_revision = 'c95d1281836f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('ordre', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('recommandation', 'ordre')
