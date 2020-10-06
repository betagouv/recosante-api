"""sanitize deplacement

Revision ID: b6a88566b4cf
Revises: bcb4dc0e73e2
Create Date: 2020-10-06 17:11:34.309473

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = 'b6a88566b4cf'
down_revision = 'bcb4dc0e73e2'
branch_labels = None
depends_on = None


def upgrade():

    conn = op.get_bind()
    conn.execute(
        text(
            """
            UPDATE inscription SET deplacement=(SELECT array(SELECT lower(unnest(deplacement))));
            UPDATE inscription SET deplacement=array_append(deplacement, 'tec') WHERE 'transports en commun' = ANY(deplacement);
            UPDATE inscription SET deplacement=array_append(deplacement, 'velo') WHERE 'vélo' = ANY(deplacement);
            UPDATE inscription SET deplacement=array_remove(deplacement, 'transports en commun');
            UPDATE inscription SET deplacement=array_remove(deplacement, 'vélo');
            UPDATE inscription
            SET    deplacement = ARRAY (
                 SELECT d
                 FROM   unnest(deplacement) WITH ORDINALITY t(d,ord)
                 GROUP  BY 1
                 ORDER  BY min(ord)
                )
            WHERE  cardinality(deplacement) > 1
            AND    deplacement <> ARRAY (
                 SELECT d
                 FROM   unnest(deplacement) WITH ORDINALITY t(d, ord)
                 GROUP  BY 1
                 ORDER  BY min(ord)
                );
            """
        )
    )

def downgrade():
    pass
