"""Ajout commune_id

Revision ID: 732e132637c5
Revises: 63dbbff719ac
Create Date: 2021-10-06 12:23:17.146405

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '732e132637c5'
down_revision = '63dbbff719ac'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute("""
    UPDATE inscription
    SET commune_id = subquery.id
    FROM (
        SELECT id, insee
        FROM indice_schema.commune
    ) AS subquery
    WHERE inscription.ville_insee = subquery.insee
    """)


def downgrade():
    pass
