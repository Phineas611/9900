"""
Create Eval Lab tables: eval_lab_jobs, eval_lab_records

Revision ID: 4d5e6f7a8b9c
Revises: 3c4d5e6f7a8b
Create Date: 2025-10-31
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '4d5e6f7a8b9c'
down_revision = '3c4d5e6f7a8b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'eval_lab_jobs',
        sa.Column('job_id', sa.String(length=64), primary_key=True),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('columns_map', sa.JSON(), nullable=False),
        sa.Column('judges', sa.JSON(), nullable=False),
        sa.Column('rubrics', sa.JSON(), nullable=False),
        sa.Column('custom_metrics', sa.JSON(), nullable=False),
        sa.Column('total', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('finished', sa.Integer(), nullable=False, server_default=sa.text('0')),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metrics_summary', sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )

    op.create_table(
        'eval_lab_records',
        sa.Column('pk', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('job_id', sa.String(length=64), sa.ForeignKey('eval_lab_jobs.job_id'), nullable=False),
        sa.Column('sid', sa.String(length=128), nullable=False),
        sa.Column('sentence', sa.Text(), nullable=False),
        sa.Column('gold_class', sa.String(length=32), nullable=True),
        sa.Column('pred_class', sa.String(length=32), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('judges_json', sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
        sa.Column('consensus_json', sa.JSON(), nullable=False, server_default=sa.text("'{}'")),
    )

    op.create_index('ix_eval_lab_records_job_id', 'eval_lab_records', ['job_id'])


def downgrade() -> None:
    op.drop_index('ix_eval_lab_records_job_id', table_name='eval_lab_records')
    op.drop_table('eval_lab_records')
    op.drop_table('eval_lab_jobs')