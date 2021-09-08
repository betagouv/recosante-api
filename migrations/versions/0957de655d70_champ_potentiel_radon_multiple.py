"""Champ potentiel radon multiple

Revision ID: 0957de655d70
Revises: bc9b27265a3b
Create Date: 2021-09-08 17:40:27.916833

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0957de655d70'
down_revision = 'bc9b27265a3b'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
    ALTER TABLE recommandation
    ALTER potentiel_radon TYPE integer[]
    USING
    CASE
    WHEN potentiel_radon IS NULL THEN
    ARRAY[]::integer[]
    ELSE
    ARRAY[potentiel_radon]
    END
    """)


def downgrade():
    pass
    
