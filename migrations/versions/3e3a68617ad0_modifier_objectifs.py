"""Modifier objectifs

Revision ID: 3e3a68617ad0
Revises: c2f6b2dfae88
Create Date: 2021-05-19 14:50:44.634085

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3e3a68617ad0'
down_revision = 'c2f6b2dfae88'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE recommandation SET objectif=LOWER(objectif);")
    op.execute("UPDATE recommandation SET objectif='limiter les effets de la pollution de l''air sur votre santé' WHERE type='episode_pollution';")


def downgrade():
    pass