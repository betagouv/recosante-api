"""Migrer les utilisateurs avec la nouvelle fréquence

Revision ID: 63dbbff719ac
Revises: 17a61f048f42
Create Date: 2021-10-04 17:13:09.847708

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '63dbbff719ac'
down_revision = '17a61f048f42'
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
    conn.execute(inscription.update().where(
        sa.text("'allergie_pollens' <> ALL(population)"))
        .values({
            "indicateurs": ["indice_atmo"],
            "indicateurs_frequence": ["quotidien"],
            "indicateurs_media": ["mail"],
            "recommandations_actives": ["oui"],
            "recommandations_frequence": ["quotidien"],
            "recommandations_media": ["mail"]
        })
    )
    conn.execute(inscription.update().where(
            sa.text("'allergie_pollens' = ANY(population)"),
        ).values({
            "indicateurs": ["indice_atmo", "raep"],
            "indicateurs_frequence": ["quotidien"],
            "indicateurs_media": ["mail"],
            "recommandations_actives": ["oui"],
            "recommandations_frequence": ["quotidien"],
            "recommandations_media": ["mail"]
        }
    ))


def downgrade():
    pass
