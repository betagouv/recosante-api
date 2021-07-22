"""Changement objectif

Revision ID: b64307cd3c69
Revises: 39ed6dfe1eff
Create Date: 2021-07-22 14:55:56.245601

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b64307cd3c69'
down_revision = '39ed6dfe1eff'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    UPDATE recommandation
    SET objectif = 'Aujourd’hui votre recommmandation est un conseil pratique pour ' || objectif
    WHERE objectif != '';
    """)

def downgrade():
    pass
