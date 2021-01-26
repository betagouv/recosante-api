"""add polluants

Revision ID: 582406afd280
Revises: c39fd985fdc0
Create Date: 2021-01-26 17:05:34.009640

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '582406afd280'
down_revision = 'c39fd985fdc0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter', sa.Column('polluants', postgresql.ARRAY(sa.String()), nullable=True))


def downgrade():
    op.drop_column('newsletter', 'polluants')
