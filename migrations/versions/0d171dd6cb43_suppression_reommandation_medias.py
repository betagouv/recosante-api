"""Suppression Reommandation.medias

Revision ID: 0d171dd6cb43
Revises: e930ec87828c
Create Date: 2021-11-24 17:58:21.988026

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0d171dd6cb43'
down_revision = 'e930ec87828c'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('recommandation', 'medias')


def downgrade():
    op.add_column('recommandation', sa.Column('medias', postgresql.ARRAY(sa.VARCHAR()), autoincrement=False, nullable=True))
