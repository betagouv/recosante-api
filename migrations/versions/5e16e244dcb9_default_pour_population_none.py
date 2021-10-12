"""default pour population none

Revision ID: 5e16e244dcb9
Revises: 483097f178f3
Create Date: 2021-10-12 18:05:36.696540

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5e16e244dcb9'
down_revision = '483097f178f3'
branch_labels = None
depends_on = None


def upgrade():
    inscription = sa.sql.table("inscription",
        sa.column("indicateurs", sa.dialects.postgresql.ARRAY(sa.String)),
        sa.column("indicateurs_frequence", sa.dialects.postgresql.ARRAY(sa.String)),
        sa.column("indicateurs_media", sa.dialects.postgresql.ARRAY(sa.String)),
        sa.column("recommandations_actives", sa.dialects.postgresql.ARRAY(sa.String)),
        sa.column("recommandations_frequence", sa.dialects.postgresql.ARRAY(sa.String)),
        sa.column("recommandations_media", sa.dialects.postgresql.ARRAY(sa.String))
    )
    conn = op.get_bind()
    conn.execute(inscription.update(
        sa.text("population IS NULL OR 'allergie_pollens' <> ANY(population)"),
        values={
            "indicateurs": ["indice_atmo"],
            "indicateurs_frequence": ["quotidien"],
            "indicateurs_media": ["mail"],
            "recommandations_actives": ["oui"],
            "recommandations_frequence": ["quotidien"],
            "recommandations_media": ["mail"]
        }
    ))


def downgrade():
    pass
