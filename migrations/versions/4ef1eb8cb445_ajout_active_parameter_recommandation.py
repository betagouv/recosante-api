"""Ajout active parameter recommandation

Revision ID: 4ef1eb8cb445
Revises: 0502b381ec96
Create Date: 2021-01-11 17:46:03.077471

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import expression


# revision identifiers, used by Alembic.
revision = '4ef1eb8cb445'
down_revision = '0502b381ec96'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('is_active', sa.Boolean(), server_default=expression.true(), nullable=False))


def downgrade():
    op.drop_column('recommandation', 'is_active')
