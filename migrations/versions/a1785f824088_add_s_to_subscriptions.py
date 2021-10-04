"""Add s to subscriptions

Revision ID: a1785f824088
Revises: 39b93da1a802
Create Date: 2021-09-27 11:33:03.259573

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1785f824088'
down_revision = '39b93da1a802'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('inscription', 'webpush_subscription_info', new_column_name='webpush_subscriptions_info')

def downgrade():
    op.alter_column('inscription', 'webpush_subscriptions_info', new_column_name='webpush_subscription_info')