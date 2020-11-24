"""Ajout filtres ozone et particules fines

Revision ID: 5a0aaae91354
Revises: d764f49c4044
Create Date: 2020-11-24 15:06:38.395841

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5a0aaae91354'
down_revision = 'd764f49c4044'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('ozone', sa.BOOLEAN(), nullable=True))
    op.add_column('recommandation', sa.Column('particules_fines', sa.BOOLEAN(), nullable=True))


def downgrade():
    op.drop_column('recommandation', 'particules_fines')
    op.drop_column('recommandation', 'ozone')
