"""Ajout vigilance globale à newsletter

Revision ID: 86489b0fc49b
Revises: c9d8fcacabf0
Create Date: 2022-01-26 11:16:52.464294

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '86489b0fc49b'
down_revision = 'c9d8fcacabf0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter', sa.Column('vigilance_globale_id', sa.Integer(), nullable=True))
    op.add_column('newsletter', sa.Column('vigilance_globale_recommandation_id', sa.Integer(), nullable=True))
    op.create_foreign_key('newsletter_vigilance_meteo_globale_id_fk', 'newsletter', 'vigilance_meteo', ['vigilance_globale_id'], ['id'], referent_schema='indice_schema')
    op.create_foreign_key('newsletter_vigilance_meteo_globale_recommandation_id_fk', 'newsletter', 'recommandation', ['vigilance_globale_recommandation_id'], ['id'])


def downgrade():
    op.drop_constraint('newsletter_vigilance_meteo_globale_id_fk', 'newsletter', type_='foreignkey')
    op.drop_constraint('newsletter_vigilance_meteo_globale_recommandation_id_fk', 'newsletter', type_='foreignkey')
    op.drop_column('newsletter', 'vigilance_globale_recommandation_id')
    op.drop_column('newsletter', 'vigilance_globale_id')
