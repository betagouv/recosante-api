"""Ajout ouvertures

Revision ID: be7f7b04552a
Revises: 9023a1c71414
Create Date: 2021-08-05 12:31:23.705030

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'be7f7b04552a'
down_revision = '9023a1c71414'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('inscription', sa.Column('ouvertures', postgresql.ARRAY(sa.Date()), nullable=True))


def downgrade():
    op.drop_column('inscription', 'ouvertures')
