"""Changement nom Recommandations.vigilance_*_id

Revision ID: f9d644374ef4
Revises: 110acb48f900
Create Date: 2021-12-16 14:22:47.726438

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'f9d644374ef4'
down_revision = '110acb48f900'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('recommandation', 'vigilance_couleur_id', new_column_name='vigilance_couleur_ids')
    op.alter_column('recommandation', 'vigilance_phenomene_id', new_column_name='vigilance_phenomene_ids')


def downgrade():
    op.alter_column('recommandation', 'vigilance_couleur_ids', new_column_name='vigilance_couleur_id')
    op.alter_column('recommandation', 'vigilance_phenomene_ids', new_column_name='vigilance_phenomene_id')
