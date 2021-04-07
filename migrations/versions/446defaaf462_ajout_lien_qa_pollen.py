"""Ajout lien qa pollen

Revision ID: 446defaaf462
Revises: 89da260fc688
Create Date: 2021-04-07 17:10:54.077142

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '446defaaf462'
down_revision = '89da260fc688'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('lien_qa_pollen', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('recommandation', 'lien_qa_pollen')