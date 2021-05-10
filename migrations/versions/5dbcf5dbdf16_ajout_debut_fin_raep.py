"""Ajout debut fin raep

Revision ID: 5dbcf5dbdf16
Revises: c313885f2bee
Create Date: 2021-05-10 14:47:47.619582

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5dbcf5dbdf16'
down_revision = 'c313885f2bee'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter', sa.Column('raep_debut_validite', sa.Date(), nullable=True))
    op.add_column('newsletter', sa.Column('raep_fin_validite', sa.Date(), nullable=True))


def downgrade():
    op.drop_column('newsletter', 'raep_fin_validite')
    op.drop_column('newsletter', 'raep_debut_validite')