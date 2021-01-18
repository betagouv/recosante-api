"""Ajout champ raep sur recommandation

Revision ID: ffbca578dd84
Revises: a504dd88a502
Create Date: 2021-01-18 17:24:20.953721

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ffbca578dd84'
down_revision = 'a504dd88a502'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('raep', sa.BOOLEAN(), nullable=True))


def downgrade():
    op.drop_column('recommandation', 'raep')
