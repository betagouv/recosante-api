"""Ajout chauffage

Revision ID: dc85620e95c3
Revises: 446defaaf462
Create Date: 2021-04-12 10:49:40.950216

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'dc85620e95c3'
down_revision = '446defaaf462'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('chauffage', postgresql.ARRAY(sa.String()), nullable=True))
    op.execute("UPDATE recommandation SET chauffage='{\"bois\"}' WHERE chauffage_a_bois = true")
    op.drop_column('recommandation', 'chauffage_a_bois')


def downgrade():
    op.add_column('recommandation', sa.Column('chauffage_a_bois', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('recommandation', 'chauffage')
