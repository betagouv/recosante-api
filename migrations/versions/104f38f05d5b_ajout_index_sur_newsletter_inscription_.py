"""Ajout index sur newsletter.inscription_id

Revision ID: 104f38f05d5b
Revises: 20484ad297c7
Create Date: 2021-06-23 17:14:57.795955

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '104f38f05d5b'
down_revision = '20484ad297c7'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(op.f('ix_newsletter_inscription_id'), 'newsletter', ['inscription_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_newsletter_inscription_id'), table_name='newsletter')
