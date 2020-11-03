"""Add date to newsletter

Revision ID: e6fde44bb7d3
Revises: 0e4285fb2929
Create Date: 2020-11-03 14:45:23.252191

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e6fde44bb7d3'
down_revision = '0e4285fb2929'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter', sa.Column('date', sa.Date(), nullable=True))


def downgrade():
    op.drop_column('newsletter', 'date')