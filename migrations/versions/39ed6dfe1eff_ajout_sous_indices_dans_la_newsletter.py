"""Ajout sous_indices dans la newsletter

Revision ID: 39ed6dfe1eff
Revises: 1c7b2c3e05c5
Create Date: 2021-06-28 17:11:02.652549

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '39ed6dfe1eff'
down_revision = '1c7b2c3e05c5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter', sa.Column('sous_indices', postgresql.JSONB(astext_type=sa.Text()), nullable=True))


def downgrade():
    op.drop_column('newsletter', 'sous_indices')