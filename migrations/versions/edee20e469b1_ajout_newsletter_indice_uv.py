"""Ajout newsletter Indice UV

Revision ID: edee20e469b1
Revises: 86489b0fc49b
Create Date: 2022-02-14 14:05:47.216836

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'edee20e469b1'
down_revision = '86489b0fc49b'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter', sa.Column('recommandation_indice_uv_id', sa.Integer(), nullable=True))
    op.add_column('newsletter', sa.Column('show_indice_uv', sa.Boolean(), nullable=True))
    op.add_column('newsletter', sa.Column('indice_uv_label', sa.String(), nullable=True))
    op.add_column('newsletter', sa.Column('indice_uv_value', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'newsletter', 'recommandation', ['recommandation_indice_uv_id'], ['id'])


def downgrade():
    op.drop_constraint(None, 'newsletter', type_='foreignkey')
    op.drop_column('newsletter', 'indice_uv_value')
    op.drop_column('newsletter', 'indice_uv_label')
    op.drop_column('newsletter', 'show_indice_uv')
    op.drop_column('newsletter', 'recommandation_indice_uv_id')