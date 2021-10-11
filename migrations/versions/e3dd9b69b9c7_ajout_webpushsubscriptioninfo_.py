"""Ajout WebpushSubscriptionInfo relationship

Revision ID: e3dd9b69b9c7
Revises: 732e132637c5
Create Date: 2021-10-07 17:07:29.831008

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'e3dd9b69b9c7'
down_revision = '732e132637c5'
branch_labels = None
depends_on = None

rel_name = 'newsletter_webpush_subscription_info'

def upgrade():
    op.create_table('webpush_subscription_info',
    sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.Column('inscription_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['inscription_id'], ['inscription.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_webpush_subscription_info_inscription_id'), 'webpush_subscription_info', ['inscription_id'], unique=False)
    op.drop_column('inscription', 'webpush_subscriptions_info')
    op.add_column('newsletter', sa.Column('webpush_subcription_info_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_newsletter_webpush_subcription_info_id'), 'newsletter', ['webpush_subcription_info_id'], unique=False)
    op.create_foreign_key(rel_name, 'newsletter', 'webpush_subscription_info', ['webpush_subcription_info_id'], ['id'])


def downgrade():
    op.drop_constraint(rel_name, 'newsletter', type_='foreignkey')
    op.drop_index(op.f('ix_newsletter_webpush_subcription_info_id'), table_name='newsletter')
    op.drop_column('newsletter', 'webpush_subcription_info_id')
    op.add_column('inscription', sa.Column('webpush_subscriptions_info', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_index(op.f('ix_webpush_subscription_info_inscription_id'), table_name='webpush_subscription_info')
    op.drop_table('webpush_subscription_info')
