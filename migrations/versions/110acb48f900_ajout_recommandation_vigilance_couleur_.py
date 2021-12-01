"""Ajout Recommandation.vigilance_couleur_id&vigilance_phenomene_id

Revision ID: 110acb48f900
Revises: 539529db24ef
Create Date: 2021-12-01 11:46:22.540788

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '110acb48f900'
down_revision = '539529db24ef'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('vigilance_couleur_id', postgresql.ARRAY(sa.Integer()), nullable=True))
    op.add_column('recommandation', sa.Column('vigilance_phenomene_id', postgresql.ARRAY(sa.Integer()), nullable=True))


def downgrade():
    op.drop_column('recommandation', 'vigilance_phenomene_id')
    op.drop_column('recommandation', 'vigilance_couleur_id')

