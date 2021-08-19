"""Suppression lien qa pollen

Revision ID: ebc8551a80f4
Revises: ed7fe5215ef4
Create Date: 2021-08-19 15:27:35.685252

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ebc8551a80f4'
down_revision = 'ed7fe5215ef4'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('recommandation', 'lien_qa_pollen')

def downgrade():
    op.add_column('recommandation', sa.Column('lien_qa_pollen', sa.BOOLEAN(), autoincrement=False, nullable=True))
