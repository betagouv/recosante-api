"""Ajout NLDB.show_{qa,vigilance}

Revision ID: ad12ab0c9e74
Revises: 08bb5d4e3455
Create Date: 2022-06-09 11:38:04.905718

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ad12ab0c9e74'
down_revision = '08bb5d4e3455'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter', sa.Column('show_qa', sa.Boolean(), nullable=True))
    op.add_column('newsletter', sa.Column('show_vigilance', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('newsletter', 'show_vigilance')
    op.drop_column('newsletter', 'show_qa')
