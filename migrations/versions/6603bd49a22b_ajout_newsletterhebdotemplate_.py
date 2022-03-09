"""Ajout NewsletterHebdoTemplate.indicateurs

Revision ID: 6603bd49a22b
Revises: edee20e469b1
Create Date: 2022-03-09 12:26:30.217781

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '6603bd49a22b'
down_revision = 'edee20e469b1'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter_hebdo_template', sa.Column('indicateurs', postgresql.ARRAY(sa.String()), nullable=True))


def downgrade():
    op.drop_column('newsletter_hebdo_template', 'indicateurs')