"""Suppression fumeur

Revision ID: 7c04d2cbf80f
Revises: 9e5d9dcf1a4a
Create Date: 2021-02-03 11:58:53.354988

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7c04d2cbf80f'
down_revision = '9e5d9dcf1a4a'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('inscription', 'fumeur')


def downgrade():
    op.add_column('inscription', sa.Column('fumeur', sa.BOOLEAN(), autoincrement=False, nullable=True))
