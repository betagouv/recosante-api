"""Allergenes devient json

Revision ID: c313885f2bee
Revises: a48745211934
Create Date: 2021-05-05 11:00:12.372392

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c313885f2bee'
down_revision = 'a48745211934'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    ALTER TABLE newsletter
        ALTER COLUMN allergenes type jsonb using to_jsonb(allergenes);
    """)


def downgrade():
    pass
