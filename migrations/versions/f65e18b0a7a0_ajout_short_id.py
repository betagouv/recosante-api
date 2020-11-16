"""Ajout short_id

Revision ID: f65e18b0a7a0
Revises: ec7ca2436d87
Create Date: 2020-11-13 10:39:19.018845

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f65e18b0a7a0'
down_revision = 'ec7ca2436d87'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'newsletter',
        sa.Column('short_id',
            sa.String(),
            nullable=True,
            server_default=sa.text("generate_random_id('public', 'newsletter', 'short_id', 8)")
        )
    )
    op.execute("UPDATE newsletter SET short_id=generate_random_id('public', 'newsletter', 'short_id', 9)")
    op.alter_column('newsletter', 'short_id', nullable=False)


def downgrade():
    op.drop_column('newsletter', 'short_id')