"""Changement type enfants

Revision ID: 89da260fc688
Revises: e741811f9af0
Create Date: 2021-03-12 15:58:42.348545

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '89da260fc688'
down_revision = 'e741811f9af0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('inscription', sa.Column('_enfants', sa.String(), nullable=True))
    op.execute("UPDATE inscription SET _enfants='oui' WHERE enfants = true;")
    op.execute("UPDATE inscription SET _enfants='non' WHERE enfants = false;")
    op.drop_column('inscription', 'enfants')
    op.alter_column('inscription', '_enfants', new_column_name='enfants')


def downgrade():
    op.add_column('inscription', sa.Column('_enfants', sa.Boolean(), nullable=True))
    op.execute("UPDATE inscription SET _enfants=true WHERE enfants = 'oui';")
    op.execute("UPDATE inscription SET _enfants=false WHERE enfants = 'non';")
    op.drop_column('inscription', 'enfants')
    op.alter_column('inscription', '_enfants', new_column_name='enfants')
