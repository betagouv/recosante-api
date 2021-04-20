"""Ajout couleur et label dans la nl

Revision ID: c95d1281836f
Revises: 9abe090e50ce
Create Date: 2021-04-20 16:16:37.557218

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c95d1281836f'
down_revision = '9abe090e50ce'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter', sa.Column('couleur', sa.String(), nullable=True))
    op.add_column('newsletter', sa.Column('label', sa.String(), nullable=True))


def downgrade():
    op.drop_column('newsletter', 'label')
    op.drop_column('newsletter', 'couleur')
