"""Ajouts types

Revision ID: 2d010b0aa766
Revises: eb571ade8f34
Create Date: 2021-02-23 13:59:37.818970

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2d010b0aa766'
down_revision = 'eb571ade8f34'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("UPDATE recommandation SET type = 'pollens' WHERE min_raep > 0")
    op.execute("UPDATE recommandation SET type = 'episode_pollution' WHERE episode_pollution = true")
    op.execute("UPDATE recommandation SET type = 'generale' WHERE type = null or type = '' or type is null")


def downgrade():
    op.execute("UPDATE recommandation SET type = null")
