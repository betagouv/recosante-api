"""Add newsletter history

Revision ID: 0e4285fb2929
Revises: 28165a6ada0d
Create Date: 2020-11-03 12:01:49.481652

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0e4285fb2929'
down_revision = '28165a6ada0d'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('newsletter',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('inscription_id', sa.Integer(), nullable=True),
        sa.Column('recommandation_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['inscription_id'], ['inscription.id'], ),
        sa.ForeignKeyConstraint(['recommandation_id'], ['recommandation.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade():
    op.drop_table('newsletter')
