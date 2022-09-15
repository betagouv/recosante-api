"""Ajout fonction generate_random_id

Revision ID: ec7ca2436d87
Revises: 8df6a9a4bab1
Create Date: 2020-11-13 10:35:45.913959

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision = 'ec7ca2436d87'
down_revision = '8df6a9a4bab1'
branch_labels = None
depends_on = None


def upgrade():
    with open("migrations/data/generate-random-short-id.sql") as f:
        query = text(f.read())
        op.execute(query)


def downgrade():
    op.execute("""
    drop function generate_random_id;
    drop function get_random_string;
    """)
