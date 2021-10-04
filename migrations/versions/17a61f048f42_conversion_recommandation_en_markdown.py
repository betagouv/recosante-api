"""Conversion recommandation en markdown

Revision ID: 17a61f048f42
Revises: a1785f824088
Create Date: 2021-09-28 10:17:38.598754

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from html2text import html2text
from markdown import markdown as markdown_to_html

# revision identifiers, used by Alembic.
revision = '17a61f048f42'
down_revision = 'a1785f824088'
branch_labels = None
depends_on = None


recommandation = table(
    'recommandation',
    column('id', sa.Integer),
    column('recommandation', sa.String),
    column('precisions', sa.String)
)

def upgrade():
    conn = op.get_bind()
    res = conn.execute(recommandation.select())
    for r in res:
        conn.execute(
            recommandation.update().where(
                recommandation.c.id == r.id
            )
            .values(
                {
                    "recommandation": html2text(r.recommandation),
                    "precisions": html2text(r.precisions)
                }
            )
        )

def downgrade():
    conn = op.get_bind()
    res = conn.execute(recommandation.select())
    for r in res:
        conn.execute(
            recommandation.update().where(
                recommandation.c.id == r.id
            ).values(
                {
                    "recommandation": markdown_to_html(r.recommandation),
                    "precisions": markdown_to_html(r.precisions)
                }
            )
        )
