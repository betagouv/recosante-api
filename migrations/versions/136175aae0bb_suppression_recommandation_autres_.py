"""Suppression Recommandation.autres_conditions

Revision ID: 136175aae0bb
Revises: 64402d1c4b06
Create Date: 2021-11-24 16:15:44.496785

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '136175aae0bb'
down_revision = '64402d1c4b06'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('recommandation', 'autres_conditions')


def downgrade():
    op.add_column('recommandation', sa.Column('autres_conditions', sa.VARCHAR(), autoincrement=False, nullable=True))
