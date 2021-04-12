"""Montrer dans le widget

Revision ID: 8b4768bb1336
Revises: dc85620e95c3
Create Date: 2021-04-12 17:24:31.906506

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8b4768bb1336'
down_revision = 'dc85620e95c3'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('montrer_dans_le_widget', sa.Boolean(), nullable=True))


def downgrade():
    op.drop_column('recommandation', 'montrer_dans_le_widget')