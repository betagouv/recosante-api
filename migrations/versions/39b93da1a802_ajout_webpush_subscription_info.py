"""Ajout webpush_subscription_info

Revision ID: 39b93da1a802
Revises: f186b4f753ac
Create Date: 2021-09-23 18:06:28.826280

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '39b93da1a802'
down_revision = 'f186b4f753ac'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('inscription', sa.Column('webpush_subscription_info', sa.String(), nullable=True))


def downgrade():
    op.drop_column('inscription', 'webpush_subscription_info')