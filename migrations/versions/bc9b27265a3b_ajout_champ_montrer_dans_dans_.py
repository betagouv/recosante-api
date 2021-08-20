"""Ajout champ montrer_dans dans recommandation

Revision ID: bc9b27265a3b
Revises: ebc8551a80f4
Create Date: 2021-08-20 10:44:38.136035

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bc9b27265a3b'
down_revision = 'ebc8551a80f4'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('montrer_dans', sa.ARRAY(sa.String()), nullable=True))
    op.execute("""
    UPDATE recommandation
    SET montrer_dans = ARRAY['widget']
    WHERE montrer_dans_le_widget = true
    """)
    op.execute("""
    UPDATE recommandation
    SET montrer_dans = ARRAY['newsletter']
    WHERE montrer_dans_le_widget = false or montrer_dans_le_widget is null
    """)
    op.drop_column('recommandation', 'montrer_dans_le_widget')


def downgrade():
    op.add_column('recommandation', sa.Column('montrer_dans_le_widget', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.execute("""
    UPDATE recommandation
    SET montrer_dans_le_widget = true
    WHERE  'widget' = ANY (montrer_dans)
    """)
    op.execute("""
    UPDATE recommandation
    SET montrer_dans_le_widget = false
    WHERE 'widget' <> ANY (montrer_dans)
    """)
    op.drop_column('recommandation', 'montrer_dans')
