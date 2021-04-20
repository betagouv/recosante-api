"""Ajout allergenes dans la nl

Revision ID: a34653793342
Revises: 8b4768bb1336
Create Date: 2021-04-20 15:08:07.500751

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a34653793342'
down_revision = '8b4768bb1336'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter', sa.Column('allergenes', postgresql.ARRAY(sa.String()), nullable=True))
    op.drop_column('newsletter', 'qai')


def downgrade():
    op.add_column('newsletter', sa.Column('qai', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('newsletter', 'allergenes')
