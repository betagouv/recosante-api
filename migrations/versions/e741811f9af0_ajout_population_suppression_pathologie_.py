"""Ajout population suppression pathologie respi et allergie

Revision ID: e741811f9af0
Revises: ca7c02fcb035
Create Date: 2021-03-10 17:45:26.560460

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e741811f9af0'
down_revision = 'ca7c02fcb035'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('inscription', sa.Column('population', postgresql.ARRAY(sa.String()), nullable=True))
    op.execute("UPDATE inscription SET population = ARRAY['allergie_pollens'] WHERE allergie_pollen = true;")
    op.execute("UPDATE inscription SET population = ARRAY['pathologie_respiratoire'] WHERE pathologie_respiratoire = true;")
    op.execute("UPDATE inscription SET population = ARRAY['allergie_pollens', 'pathologie_respiratoire'] WHERE allergie_pollen = true AND pathologie_respiratoire = true;")
    op.drop_column('inscription', 'allergie_pollen')
    op.drop_column('inscription', 'pathologie_respiratoire')


def downgrade():
    op.add_column('inscription', sa.Column('pathologie_respiratoire', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.execute("UPDATE inscription SET pathologie_respiratoire = true WHERE 'pathologie_respiratoire' = ANY(population)")
    op.add_column('inscription', sa.Column('allergie_pollen', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.execute("UPDATE inscription SET allergie_pollen = true WHERE 'allergie_pollens' = ANY(population)")
    op.drop_column('inscription', 'population')
