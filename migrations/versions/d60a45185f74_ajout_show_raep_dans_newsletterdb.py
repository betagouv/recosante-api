"""Ajout show_raep dans newsletterdb

Revision ID: d60a45185f74
Revises: 104f38f05d5b
Create Date: 2021-06-23 17:26:45.619277

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd60a45185f74'
down_revision = '104f38f05d5b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter', sa.Column('show_raep', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('newsletter', 'show_raep')
