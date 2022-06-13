"""Add index on newsletter.short_id

Revision ID: a06c1edc439f
Revises: 08bb5d4e3455
Create Date: 2022-06-13 14:05:39.704606

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a06c1edc439f'
down_revision = '08bb5d4e3455'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index(op.f('ix_newsletter_short_id'), 'newsletter', ['short_id'], unique=True)



def downgrade():
    op.drop_index(op.f('ix_newsletter_short_id'), table_name='newsletter')
