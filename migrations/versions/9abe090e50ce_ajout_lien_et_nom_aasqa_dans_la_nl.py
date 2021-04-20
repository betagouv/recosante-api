"""Ajout lien et nom AASQA dans la nl

Revision ID: 9abe090e50ce
Revises: a34653793342
Create Date: 2021-04-20 15:54:34.701588

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9abe090e50ce'
down_revision = 'a34653793342'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter', sa.Column('lien_aasqa', sa.String(), nullable=True))
    op.add_column('newsletter', sa.Column('nom_aasqa', sa.String(), nullable=True))


def downgrade():
    op.drop_column('newsletter', 'nom_aasqa')
    op.drop_column('newsletter', 'lien_aasqa')