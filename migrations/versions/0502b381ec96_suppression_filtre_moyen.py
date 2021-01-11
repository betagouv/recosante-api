"""Suppression filtre moyen

Revision ID: 0502b381ec96
Revises: 3dfc4940599e
Create Date: 2021-01-11 17:11:53.532843

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0502b381ec96'
down_revision = '3dfc4940599e'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('recommandation', 'qa_moyenne')


def downgrade():
    op.add_column('recommandation', sa.Column('qa_moyenne', sa.BOOLEAN(), autoincrement=False, nullable=True))
