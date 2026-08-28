"""add dataset storage blobs table

Revision ID: b7e21a89c4d2
Revises: aceec30e7803
Create Date: 2026-08-28 10:10:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7e21a89c4d2'
down_revision: Union[str, None] = 'aceec30e7803'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'dataset_storage_blobs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('storage_key', sa.String(length=500), nullable=False),
        sa.Column('compressed_data', sa.LargeBinary(), nullable=False),
        sa.Column('content_type', sa.String(length=100), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_dataset_storage_blobs_id'), 'dataset_storage_blobs', ['id'], unique=False)
    op.create_index(op.f('ix_dataset_storage_blobs_company_id'), 'dataset_storage_blobs', ['company_id'], unique=False)
    op.create_index(op.f('ix_dataset_storage_blobs_storage_key'), 'dataset_storage_blobs', ['storage_key'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_dataset_storage_blobs_storage_key'), table_name='dataset_storage_blobs')
    op.drop_index(op.f('ix_dataset_storage_blobs_company_id'), table_name='dataset_storage_blobs')
    op.drop_index(op.f('ix_dataset_storage_blobs_id'), table_name='dataset_storage_blobs')
    op.drop_table('dataset_storage_blobs')
