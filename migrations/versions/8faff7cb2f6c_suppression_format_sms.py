"""Suppression format SMS

Revision ID: 8faff7cb2f6c
Revises: 1d82053b1e7a
Create Date: 2021-11-24 16:02:10.089488

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8faff7cb2f6c'
down_revision = '1d82053b1e7a'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('recommandation', 'recommandation_format_SMS')


def downgrade():
    op.add_column('recommandation', sa.Column('recommandation_format_SMS', sa.VARCHAR(), autoincrement=False, nullable=True))
