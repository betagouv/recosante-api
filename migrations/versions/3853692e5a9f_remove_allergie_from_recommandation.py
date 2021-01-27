"""remove allergie from recommandation

Revision ID: 3853692e5a9f
Revises: 582406afd280
Create Date: 2021-01-27 16:35:59.807795

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3853692e5a9f'
down_revision = '582406afd280'
branch_labels = None
depends_on = None


def upgrade():
    op.drop_column('recommandation', 'allergies')


def downgrade():
    op.add_column('recommandation', sa.Column('allergies', sa.BOOLEAN(), autoincrement=False, nullable=True))
