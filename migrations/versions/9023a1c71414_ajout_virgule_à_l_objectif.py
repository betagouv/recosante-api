"""Ajout virgule à l’objectif

Revision ID: 9023a1c71414
Revises: b64307cd3c69
Create Date: 2021-07-26 12:27:11.224807

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9023a1c71414'
down_revision = 'b64307cd3c69'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    UPDATE recommandation
    SET objectif = overlay(objectif placing 'Aujourd’hui, ' from 1 for 12)
    WHERE objectif != ''
    """)


def downgrade():
    pass
