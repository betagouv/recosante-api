"""Ajout vigilance à newsletter

Revision ID: c9d8fcacabf0
Revises: 017e76d92cfb
Create Date: 2022-01-19 17:35:41.001599

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c9d8fcacabf0'
down_revision = '017e76d92cfb'
branch_labels = None
depends_on = None

phenomenes_sib = {1: 'vent', 2: 'pluie', 3: 'orages', 4: 'crues', 5: 'neige', 6: 'canicule', 7: 'froid', 8: 'avalanches', 9: 'vagues'}

def upgrade():
    for phenomene in phenomenes_sib.values():
        op.add_column('newsletter', sa.Column(f'vigilance_{phenomene}_id', sa.Integer(), nullable=True))
        op.add_column('newsletter', sa.Column(f'vigilance_{phenomene}_recommandation_id', sa.Integer(), nullable=True))
        op.create_foreign_key(f'newsletter_fk_vigilance_{phenomene}_id', 'newsletter', 'recommandation', [f'vigilance_{phenomene}_recommandation_id'], ['id'])
        op.create_foreign_key(f'newsletter_fk_vigilance_{phenomene}_recommandation_id', 'newsletter', 'vigilance_meteo', [f'vigilance_{phenomene}_id'], ['id'], referent_schema='indice_schema')


def downgrade():
    for phenomene in phenomenes_sib.values():
        op.drop_constraint(f'newsletter_fk_vigilance_{phenomene}_id', 'newsletter', type_='foreignkey')
        op.drop_constraint(f'newsletter_fk_vigilance_{phenomene}_recommandation_id', 'newsletter', type_='foreignkey')
        op.drop_column('newsletter', f'vigilance_{phenomene}_recommandation_id')
        op.drop_column('newsletter', f'vigilance_{phenomene}_id')