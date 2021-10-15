"""Ajout mail_list_id dans newsletter

Revision ID: 28ca23dcd7a4
Revises: 56a71fa504ec
Create Date: 2021-10-15 11:35:49.245323

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '28ca23dcd7a4'
down_revision = '56a71fa504ec'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter', sa.Column('mail_list_id', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('newsletter', 'mail_list_id')