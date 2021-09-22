"""Ajout commune à inscription

Revision ID: c9dbc97d160a
Revises: 0957de655d70
Create Date: 2021-09-15 12:51:45.022843

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c9dbc97d160a'
down_revision = '0957de655d70'
branch_labels = None
depends_on = None

foreign_key_name = 'inscription_commune_fk'

def upgrade():
    op.add_column('inscription', sa.Column('commune_id', sa.Integer(), nullable=True))
    op.create_foreign_key(foreign_key_name, 'inscription', 'commune', ['commune_id'], ['id'], referent_schema='indice_schema')


def downgrade():
    op.drop_constraint(foreign_key_name, 'inscription', type_='foreignkey')
    op.drop_column('inscription', 'commune_id')
