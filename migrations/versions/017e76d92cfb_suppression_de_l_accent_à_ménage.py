"""Suppression de l’accent à ménage

Revision ID: 017e76d92cfb
Revises: b35b9c24bb49
Create Date: 2022-01-18 15:59:54.617143

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '017e76d92cfb'
down_revision = 'b35b9c24bb49'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    UPDATE inscription
    SET activites = array_append(array_remove(activites, 'ménage'), 'menage')
    WHERE activites @> '{ménage}'
    """)

def downgrade():
    pass
