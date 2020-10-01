"""Ajout recommandations

Revision ID: 07e6a2b58cb7
Revises: 50ec124dbbfc
Create Date: 2020-09-30 15:30:25.389947

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '07e6a2b58cb7'
down_revision = '50ec124dbbfc'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('recommandation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('recommandabilite', sa.String(), nullable=True),
    sa.Column('recommandation', sa.String(), nullable=True),
    sa.Column('precisions', sa.String(), nullable=True),
    sa.Column('recommandation_format_SMS', sa.String(), nullable=True),
    sa.Column('qa_mauvaise', sa.Boolean(), nullable=True),
    sa.Column('menage', sa.Boolean(), nullable=True),
    sa.Column('bricolage', sa.Boolean(), nullable=True),
    sa.Column('chauffage_a_bois', sa.Boolean(), nullable=True),
    sa.Column('jardinage', sa.Boolean(), nullable=True),
    sa.Column('balcon_terasse', sa.Boolean(), nullable=True),
    sa.Column('velo_trott_skate', sa.Boolean(), nullable=True),
    sa.Column('transport_en_commun', sa.Boolean(), nullable=True),
    sa.Column('voiture', sa.Boolean(), nullable=True),
    sa.Column('activite_physique', sa.Boolean(), nullable=True),
    sa.Column('allergies', sa.Boolean(), nullable=True),
    sa.Column('enfants', sa.Boolean(), nullable=True),
    sa.Column('personnes_sensibles', sa.Boolean(), nullable=True),
    sa.Column('niveau_difficulte', sa.String(), nullable=True),
    sa.Column('autres_conditions', sa.String(), nullable=True),
    sa.Column('sources', sa.String(), nullable=True),
    sa.Column('categorie', sa.String(), nullable=True),
    sa.Column('objectif', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('recommandation')
