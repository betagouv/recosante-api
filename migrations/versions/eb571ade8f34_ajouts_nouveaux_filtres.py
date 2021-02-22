"""Ajouts nouveaux filtres

Revision ID: eb571ade8f34
Revises: 0605112d05c5
Create Date: 2021-02-22 14:55:38.063579

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'eb571ade8f34'
down_revision = '0605112d05c5'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('animal_de_compagnie', sa.Boolean(), nullable=True))
    op.add_column('recommandation', sa.Column('personne_allergique', sa.Boolean(), nullable=True))
    op.add_column('recommandation', sa.Column('type', sa.String(), nullable=True))
    op.add_column('recommandation', sa.Column('min_raep', sa.Integer(), nullable=True))
    op.alter_column('recommandation', 'population_generale', new_column_name='autres')
    op.execute("UPDATE recommandation SET min_raep = 1 WHERE raep = true")
    op.drop_column('recommandation', 'raep')


def downgrade():
    op.drop_column('recommandation', 'type')
    op.drop_column('recommandation', 'personne_allergique')
    op.drop_column('recommandation', 'animal_de_compagnie')
    op.add_column('recommandation', sa.Column('raep', sa.Boolean(), nullable=True))
