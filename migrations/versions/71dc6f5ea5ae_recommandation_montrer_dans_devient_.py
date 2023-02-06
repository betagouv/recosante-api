"""recommandation.montrer_dans devient medias

Revision ID: 71dc6f5ea5ae
Revises: 28ca23dcd7a4
Create Date: 2021-10-19 12:00:50.572747

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '71dc6f5ea5ae'
down_revision = '28ca23dcd7a4'
branch_labels = None
depends_on = None


def upgrade():
    op.alter_column('recommandation', 'montrer_dans', new_column_name='medias')
    conn = op.get_bind()
    conn.execute(sa.text("""
    UPDATE recommandation
    SET medias = medias || ARRAY['newsletter_quotidienne']::varchar[]
    WHERE medias @> ARRAY['dashboard']::varchar[]
    """))


def downgrade():
    op.alter_column('recommandation', 'medias', new_column_name='montrer_dans')
    conn = op.get_bind()
    conn.execute(sa.text("""
    UPDATE recommandation
    SET medias = ARRAY_REMOVE(medias, 'newsletter_quotidienne')
    WHERE medias @> ARRAY['newsletter_quotidienne']::varchar[]
    """))
