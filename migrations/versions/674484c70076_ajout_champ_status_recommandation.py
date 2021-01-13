"""Ajout champ status recommandation

Revision ID: 674484c70076
Revises: 4ef1eb8cb445
Create Date: 2021-01-13 16:28:24.005206

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '674484c70076'
down_revision = '4ef1eb8cb445'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('recommandation', sa.Column('status', sa.String(), nullable=True))
    conn = op.get_bind()
    conn.execute(text("UPDATE recommandation SET status='published' WHERE recommandabilite='Utilisable'"))
    conn.execute(text("UPDATE recommandation SET status='draft' WHERE recommandabilite='Non-utilisable'"))
    conn.execute(text("UPDATE recommandation SET status='deleted' WHERE is_active='f'"))
    op.drop_column('recommandation', 'recommandabilite')
    op.drop_column('recommandation', 'is_active')


def downgrade():
    op.add_column('recommandation', sa.Column('is_active', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False))
    op.add_column('recommandation', sa.Column('recommandabilite', sa.VARCHAR(), autoincrement=False, nullable=True))
    conn = op.get_bind()
    conn.execute(text("UPDATE recommandation SET recommandation='Utilisable' WHERE status='published'"))
    conn.execute(text("UPDATE recommandation SET recommandation='Non-utilisable' WHERE status='draft'"))
    conn.execute(text("UPDATE recommandation SET is_active='t'"))
    conn.execute(text("UPDATE recommandation SET is_active='f' WHERE status='deleted'"))

    op.drop_column('recommandation', 'status')
