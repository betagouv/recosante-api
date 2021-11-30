"""Ajout NewsletterHeboTemplate

Revision ID: 539529db24ef
Revises: 0d171dd6cb43
Create Date: 2021-11-30 15:41:24.175058

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '539529db24ef'
down_revision = '0d171dd6cb43'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('newsletter_hebdo_template',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('sib_id', sa.Integer(), nullable=False),
    sa.Column('ordre', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column('newsletter', sa.Column('newsletter_hebdo_template_id', sa.Integer(), nullable=True))
    op.create_foreign_key('newsletter_newsletter_hebdo_template_id_fk', 'newsletter', 'newsletter_hebdo_template', ['newsletter_hebdo_template_id'], ['id'])


def downgrade():
    op.drop_constraint('newsletter_newsletter_hebdo_template_id_fk', 'newsletter', type_='foreignkey')
    op.drop_column('newsletter', 'newsletter_hebdo_template_id')
    op.drop_table('newsletter_hebdo_template')
