"""fix name webpush_subscription_id in Newsletter

Revision ID: f643006c45b9
Revises: e3dd9b69b9c7
Create Date: 2021-10-11 17:04:32.535093

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f643006c45b9'
down_revision = 'e3dd9b69b9c7'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column("newsletter", "webpush_subcription_info_id", new_column_name='webpush_subscription_info_id')
    
def downgrade():
    op.alter_column("newsletter", "webpush_subscription_info_id", new_column_name='webpush_subcription_info_id')
