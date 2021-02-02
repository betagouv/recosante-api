"""ajout raep

Revision ID: 9e5d9dcf1a4a
Revises: 3853692e5a9f
Create Date: 2021-02-02 16:29:53.833256

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9e5d9dcf1a4a'
down_revision = '3853692e5a9f'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter', sa.Column('raep', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('newsletter', 'raep')
