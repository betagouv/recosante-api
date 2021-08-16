"""Que deux m à recommandation

Revision ID: fd74ffb53677
Revises: be7f7b04552a
Create Date: 2021-08-16 10:30:46.715087

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'fd74ffb53677'
down_revision = 'be7f7b04552a'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE recommandation SET objectif = REPLACE(objectif, 'recommmandation', 'recommandation')")

def downgrade():
    pass
