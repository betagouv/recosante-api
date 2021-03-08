"""Convert cache_api_commune to JSON

Revision ID: 723f9ab27edf
Revises: 7a95dcbb03a6
Create Date: 2021-03-08 16:21:52.641942

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '723f9ab27edf'
down_revision = '7a95dcbb03a6'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("ALTER TABLE inscription ALTER cache_api_commune TYPE JSONB USING cache_api_commune::JSONB")


def downgrade():
    op.execute("ALTER TABLE inscription ALTER cache_api_commune TYPE VARCHAR USING cache_api_commune::VARCHAR")
