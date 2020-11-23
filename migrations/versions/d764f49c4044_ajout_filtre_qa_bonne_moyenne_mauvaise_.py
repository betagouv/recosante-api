"""Ajout filtre qa_bonne, moyenne, mauvaise et été

Revision ID: d764f49c4044
Revises: de48f61a110c
Create Date: 2020-11-23 15:44:02.638091

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd764f49c4044'
down_revision = 'de48f61a110c'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('ete', sa.BOOLEAN(), nullable=True))
    op.add_column('recommandation', sa.Column('qa_bonne', sa.BOOLEAN(), nullable=True))
    op.add_column('recommandation', sa.Column('qa_moyenne', sa.BOOLEAN(), nullable=True))


def downgrade():
    op.drop_column('recommandation', 'qa_moyenne')
    op.drop_column('recommandation', 'qa_bonne')
    op.drop_column('recommandation', 'ete')
