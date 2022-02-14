"""Ajout vigilance à newsletter

Revision ID: c9d8fcacabf0
Revises: 017e76d92cfb
Create Date: 2022-01-19 17:35:41.001599

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import reflection


# revision identifiers, used by Alembic.
revision = 'c9d8fcacabf0'
down_revision = '37b15063d1c7'
branch_labels = None
depends_on = None

phenomenes_sib = {1: 'vent', 2: 'pluie', 3: 'orages', 4: 'crues', 5: 'neige', 6: 'canicule', 7: 'froid', 8: 'avalanches', 9: 'vagues'}
def _table_has_column(table, column):
    config = op.get_context().config
    engine = sa.engine_from_config(
        config.get_section(config.config_ini_section), prefix='sqlalchemy.')
    insp = reflection.Inspector.from_engine(engine)
    has_column = False
    for col in insp.get_columns(table):
        if column not in col['name']:
            continue
        has_column = True
    return has_column


def upgrade():
    for phenomene in phenomenes_sib.values():
        column_name = f'vigilance_{phenomene}_id'
        op.add_column('newsletter', sa.Column(column_name, sa.Integer(), nullable=True))
        op.create_foreign_key(f'newsletter_fk_{column_name}', 'newsletter', 'vigilance_meteo', [column_name], ['id'], referent_schema='indice_schema')
        column_name = f'vigilance_{phenomene}_recommandation_id'
        op.add_column('newsletter', sa.Column(column_name, sa.Integer(), nullable=True))
        op.create_foreign_key(f'newsletter_fk_{column_name}', 'newsletter', 'recommandation', [column_name], ['id'])


def downgrade():
    for phenomene in phenomenes_sib.values():
        op.drop_constraint(f'newsletter_fk_vigilance_{phenomene}_id', 'newsletter', type_='foreignkey')
        op.drop_constraint(f'newsletter_fk_vigilance_{phenomene}_recommandation_id', 'newsletter', type_='foreignkey')
        op.drop_column('newsletter', f'vigilance_{phenomene}_recommandation_id')
        op.drop_column('newsletter', f'vigilance_{phenomene}_id')
