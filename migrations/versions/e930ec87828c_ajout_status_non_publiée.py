"""Ajout status non publiée

Revision ID: e930ec87828c
Revises: 136175aae0bb
Create Date: 2021-11-24 17:49:48.493773

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e930ec87828c'
down_revision = '136175aae0bb'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute("UPDATE recommandation SET status = 'hidden' WHERE medias = ARRAY[]::varchar[]")


def downgrade():
    pass
