"""Suppression doute recommandabilite

Revision ID: 1a52f7feda78
Revises: d2fe33feee7b
Create Date: 2020-12-14 11:46:47.447420

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '1a52f7feda78'
down_revision = 'd2fe33feee7b'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(text("UPDATE recommandation SET recommandabilite='Non-utilisable' WHERE recommandabilite='Doute';"))

def downgrade():
    pass
