"""Add uid to inscription

Revision ID: 7a95dcbb03a6
Revises: 2d010b0aa766
Create Date: 2021-03-02 18:42:40.281497

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7a95dcbb03a6'
down_revision = '2d010b0aa766'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('inscription', sa.Column('uid', sa.String(), server_default=sa.text("generate_random_id('public', 'inscription', 'uid', 8)"), nullable=True))


def downgrade():
    op.drop_column('inscription', 'uid')
