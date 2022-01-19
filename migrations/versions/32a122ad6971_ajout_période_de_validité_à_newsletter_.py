"""Ajout période de validité à newsletter hebdo

Revision ID: 32a122ad6971
Revises: f9d644374ef4
Create Date: 2022-01-12 11:15:41.823702

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '32a122ad6971'
down_revision = 'f9d644374ef4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter_hebdo_template', sa.Column('periode_validite', postgresql.DATERANGE(), nullable=True))
    op.execute("UPDATE newsletter_hebdo_template SET periode_validite = daterange('2022-01-01', '2022-12-31', '[]')")
    op.alter_column('newsletter_hebdo_template', 'periode_validite', nullable=False)


def downgrade():
    op.drop_column('newsletter_hebdo_template', 'periode_validite')