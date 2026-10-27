"""Persistent tenant-scoped briefs, analysis evidence, discussions and data backups."""
from alembic import op
import sqlalchemy as sa
revision = 'c28a01b92f10'
down_revision = 'b7e21a89c4d2'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('analysis_records',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('company_id', sa.Integer(), sa.ForeignKey('companies.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('kind', sa.String(32), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('dataset_revision', sa.String(100), nullable=True),
        sa.Column('content', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False))
    op.create_index('ix_analysis_records_company_id', 'analysis_records', ['company_id'])


def downgrade():
    op.drop_index('ix_analysis_records_company_id', table_name='analysis_records')
    op.drop_table('analysis_records')
