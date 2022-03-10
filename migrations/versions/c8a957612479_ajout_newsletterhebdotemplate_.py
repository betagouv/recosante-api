"""Ajout newsletterhebdotemplate.indicateurs_exclus

Revision ID: c8a957612479
Revises: 6603bd49a22b
Create Date: 2022-03-10 17:49:56.873891

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c8a957612479'
down_revision = '6603bd49a22b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter_hebdo_template', sa.Column('indicateurs_exclus', postgresql.ARRAY(sa.String()), nullable=True))


def downgrade():
    op.drop_column('newsletter_hebdo_template', 'indicateurs_exclus')