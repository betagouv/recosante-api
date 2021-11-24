"""Recommandation.typeindice_atmo vers generale

Revision ID: 1d82053b1e7a
Revises: aade4a2ca414
Create Date: 2021-11-24 15:30:11.165282

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1d82053b1e7a'
down_revision = 'aade4a2ca414'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute("UPDATE recommandation SET type = 'indice_atmo' WHERE type = 'generale'")


def downgrade():
    conn = op.get_bind()
    conn.execute("UPDATE recommandation SET type = 'generale' WHERE type = 'indice_atmo'")
