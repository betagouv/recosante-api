"""Ajout index NewsletterDB.mail_list_id

Revision ID: c5b5037a6407
Revises: 6603bd49a22b
Create Date: 2022-03-17 18:35:54.071530

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c5b5037a6407'
down_revision = '6603bd49a22b'
branch_labels = None
depends_on = None


def upgrade():
    op.create_index('newsletter_mail_list_id', 'newsletter', ['mail_list_id'])


def downgrade():
    op.drop_index('newsletter_mail_list_id', 'newsletter')
