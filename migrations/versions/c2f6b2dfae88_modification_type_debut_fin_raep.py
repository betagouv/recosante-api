"""Modification type debut fin raep

Revision ID: c2f6b2dfae88
Revises: 5dbcf5dbdf16
Create Date: 2021-05-11 10:25:25.772307

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c2f6b2dfae88'
down_revision = '5dbcf5dbdf16'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('newsletter', 'raep_debut_validite', type_=sa.String())
    op.alter_column('newsletter', 'raep_fin_validite', type_=sa.String())


def downgrade():
    op.alter_column('newsletter', 'raep_debut_validite', type_=sa.Date())
    op.alter_column('newsletter', 'raep_fin_validite', type_=sa.Date())
