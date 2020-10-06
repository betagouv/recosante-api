"""Ajout avis

Revision ID: 930a6874fe56
Revises: b6a88566b4cf
Create Date: 2020-10-06 18:58:19.075753

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '930a6874fe56'
down_revision = 'b6a88566b4cf'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('avis',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('mail', sa.String(), nullable=True),
    sa.Column('decouverte', postgresql.ARRAY(sa.String()), nullable=True),
    sa.Column('satisfaction_nombre_recommandation', sa.Boolean(), nullable=True),
    sa.Column('satisfaction_frequence', sa.String(), nullable=True),
    sa.Column('recommandabilite', sa.Integer(), nullable=True),
    sa.Column('encore', sa.Boolean(), nullable=True),
    sa.Column('autres_thematiques', sa.String(), nullable=True),
    sa.Column('date', sa.Date(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('avis')
