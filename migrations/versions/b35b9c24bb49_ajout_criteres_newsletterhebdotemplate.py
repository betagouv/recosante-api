"""Ajout criteres NewsletterHebdoTemplate

Revision ID: b35b9c24bb49
Revises: 32a122ad6971
Create Date: 2022-01-13 16:38:40.240406

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'b35b9c24bb49'
down_revision = '32a122ad6971'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('newsletter_hebdo_template', sa.Column('deplacement', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('newsletter_hebdo_template', sa.Column('activites', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('newsletter_hebdo_template', sa.Column('enfants', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('newsletter_hebdo_template', sa.Column('chauffage', postgresql.ARRAY(sa.String()), nullable=True))
    op.add_column('newsletter_hebdo_template', sa.Column('animaux_domestiques', postgresql.ARRAY(sa.String()), nullable=True))


def downgrade():
    op.drop_column('newsletter_hebdo_template', 'animaux_domestiques')
    op.drop_column('newsletter_hebdo_template', 'chauffage')
    op.drop_column('newsletter_hebdo_template', 'enfants')
    op.drop_column('newsletter_hebdo_template', 'activites')
    op.drop_column('newsletter_hebdo_template', 'deplacement')
