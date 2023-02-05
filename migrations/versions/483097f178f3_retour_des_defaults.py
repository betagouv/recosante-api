"""retour des defaults

Revision ID: 483097f178f3
Revises: f643006c45b9
Create Date: 2021-10-12 18:00:55.013698

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '483097f178f3'
down_revision = 'f643006c45b9'
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
    conn.execute(inscription.update()
        .where(sa.text("'allergie_pollens' <> ALL(population)")
        ).values({
            "indicateurs": ["indice_atmo"],
            "indicateurs_frequence": ["quotidien"],
            "indicateurs_media": ["mail"],
            "recommandations_actives": ["oui"],
            "recommandations_frequence": ["quotidien"],
            "recommandations_media": ["mail"]
        }
    ))
    conn.execute(inscription.update().where(
        sa.text("'allergie_pollens' = ANY(population)")
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
