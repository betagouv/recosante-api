"""Séparation Newsletter et NewsletterDB

Revision ID: de48f61a110c
Revises: f65e18b0a7a0
Create Date: 2020-11-16 11:30:04.171166

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'de48f61a110c'
down_revision = 'f65e18b0a7a0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter', sa.Column('qai', sa.Integer(), nullable=True))
    op.alter_column('newsletter', 'short_id',
               existing_type=sa.VARCHAR(),
               nullable=True,
               existing_server_default=sa.text("generate_random_id('public'::text, 'newsletter'::text, 'short_id'::text, 8)")
    )


def downgrade():
    op.alter_column('newsletter', 'short_id',
               existing_type=sa.VARCHAR(),
               nullable=False,
               existing_server_default=sa.text("generate_random_id('public'::text, 'newsletter'::text, 'short_id'::text, 8)"))
    op.drop_column('newsletter', 'qai')