"""lower activites

Revision ID: bcb4dc0e73e2
Revises: 25116bbd585c
Create Date: 2020-10-06 11:34:47.860748

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = 'bcb4dc0e73e2'
down_revision = '25116bbd585c'
branch_labels = None
depends_on = None


def upgrade():
    #op.drop_column('inscription', 'frequence_old')
    #op.drop_column('inscription', 'diffusion_old')

    conn = op.get_bind()
    conn.execute(
        text(
            """
            UPDATE inscription SET activites=(SELECT array(SELECT lower(unnest(activites))));
            """
        )
    )



def downgrade():
    pass