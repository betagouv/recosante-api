"""translate objectifs

Revision ID: 0605112d05c5
Revises: 7c04d2cbf80f
Create Date: 2021-02-18 11:21:44.359700

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text


# revision identifiers, used by Alembic.
revision = '0605112d05c5'
down_revision = '7c04d2cbf80f'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    conn.execute(text(
        """
        UPDATE recommandation SET objectif = 'Contribuer à réduire la pollution de l’air' WHERE objectif = 'Agir pour la qualité de l''air';
        UPDATE recommandation SET objectif = 'Améliorer l’air intérieur de votre logement' WHERE categorie = 'Air intérieur';
        """
    ))


def downgrade():
    pass
