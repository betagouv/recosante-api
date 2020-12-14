"""Ajout filtres dioxyde de souffre et d’azote

Revision ID: b80f126e89b2
Revises: 1a52f7feda78
Create Date: 2020-12-14 11:59:53.283643

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b80f126e89b2'
down_revision = '1a52f7feda78'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('dioxyde_azote', sa.BOOLEAN(), nullable=True))
    op.add_column('recommandation', sa.Column('dioxyde_soufre', sa.BOOLEAN(), nullable=True))


def downgrade():
    op.drop_column('recommandation', 'dioxyde_soufre')
    op.drop_column('recommandation', 'dioxyde_azote')
