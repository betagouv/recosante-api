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
            UPDATE inscription SET deplacement=array_append(deplacement, 'tec') WHERE 'transports en commun' = ANY(deplacement);
            UPDATE inscription SET deplacement=array_append(deplacement, 'velo') WHERE 'vélo' = ANY(deplacement);
            UPDATE inscription SET deplacement=array_remove(deplacement, 'transports en commun');
            UPDATE inscription SET deplacement=array_remove(deplacement, 'vélo');
            WITH cte_distinct AS (SELECT array_agg(DISTINCT lower(d)) as dis FROM inscription, unnest(deplacement) d) UPDATE inscription SET deplacement=cte_distinct.dis FROM cte_distinct;
            """
        )
    )



def downgrade():
    pass