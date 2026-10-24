"""Durable source schedules and notification outbox."""
from alembic import op
import sqlalchemy as sa

revision = 'd91e5f7c201a'
down_revision = 'c28a01b92f10'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('source_refresh_jobs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), unique=True, nullable=False),
        sa.Column('source_id', sa.String(100), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=False),
        sa.Column('interval_seconds', sa.Integer(), nullable=False),
        sa.Column('expected_revision', sa.String(100)),
        sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('lease_token', sa.String(64)), sa.Column('lease_until', sa.DateTime(timezone=True)),
        sa.Column('status', sa.String(32), nullable=False),
        sa.Column('last_run_at', sa.DateTime(timezone=True)), sa.Column('last_error', sa.String(300)),
        sa.Column('last_source_hash', sa.String(64)), sa.Column('failures', sa.Integer(), nullable=False))
    op.create_table('notification_outbox',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_key', sa.String(100), nullable=False), sa.Column('destination_id', sa.String(100), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False), sa.Column('status', sa.String(32), nullable=False),
        sa.Column('attempts', sa.Integer(), nullable=False), sa.Column('next_attempt_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('lease_token', sa.String(64)), sa.Column('lease_until', sa.DateTime(timezone=True)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False), sa.Column('accepted_at', sa.DateTime(timezone=True)),
        sa.Column('last_error', sa.String(300)),
        sa.UniqueConstraint('company_id', 'event_key', 'destination_id', name='uq_notification_event_destination'))
    op.create_index('ix_notification_outbox_company_id', 'notification_outbox', ['company_id'])


def downgrade():
    op.drop_index('ix_notification_outbox_company_id', table_name='notification_outbox')
    op.drop_table('notification_outbox')
    op.drop_table('source_refresh_jobs')
