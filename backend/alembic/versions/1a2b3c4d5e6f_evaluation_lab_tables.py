"""
Create evaluation tables: runs, items, judgments, aggregates

Revision ID: 1a2b3c4d5e6f
Revises: 
Create Date: 2025-10-30
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '1a2b3c4d5e6f'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'evaluation_runs',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False),
        sa.Column('config', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='QUEUED'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('summary', sa.JSON(), nullable=True),
    )
    op.create_index('ix_evaluation_runs_user_id', 'evaluation_runs', ['user_id'])

    op.create_table(
        'evaluation_items',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('run_id', sa.String(length=36), sa.ForeignKey('evaluation_runs.id'), nullable=False),
        sa.Column('item_id', sa.String(length=128), nullable=False),
        sa.Column('sentence', sa.Text(), nullable=False),
        sa.Column('gold_label', sa.String(length=64), nullable=False),
        sa.Column('predicted_label', sa.String(length=64), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
    )
    op.create_index('ix_evaluation_items_run_id', 'evaluation_items', ['run_id'])
    op.create_index('ix_evaluation_items_item_id', 'evaluation_items', ['item_id'])

    op.create_table(
        'evaluation_judgments',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('run_id', sa.String(length=36), sa.ForeignKey('evaluation_runs.id'), nullable=False),
        sa.Column('item_pk', sa.Integer(), sa.ForeignKey('evaluation_items.id'), nullable=False),
        sa.Column('judge_model', sa.String(length=64), nullable=False),
        sa.Column('verdict', sa.JSON(), nullable=False),
        sa.Column('latency_ms', sa.Float(), nullable=False),
        sa.Column('raw', sa.JSON(), nullable=False),
    )
    op.create_index('ix_evaluation_judgments_run_id', 'evaluation_judgments', ['run_id'])
    op.create_index('ix_evaluation_judgments_item_pk', 'evaluation_judgments', ['item_pk'])

    op.create_table(
        'evaluation_aggregates',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('run_id', sa.String(length=36), sa.ForeignKey('evaluation_runs.id'), nullable=False),
        sa.Column('item_pk', sa.Integer(), sa.ForeignKey('evaluation_items.id'), nullable=False),
        sa.Column('yesno', sa.JSON(), nullable=False),
        sa.Column('confidence', sa.JSON(), nullable=False),
        sa.Column('notes', sa.JSON(), nullable=False),
        sa.Column('judge_votes', sa.JSON(), nullable=False),
        sa.Column('time_ms', sa.Float(), nullable=False, server_default='0'),
    )
    op.create_index('ix_evaluation_aggregates_run_id', 'evaluation_aggregates', ['run_id'])
    op.create_index('ix_evaluation_aggregates_item_pk', 'evaluation_aggregates', ['item_pk'])


def downgrade() -> None:
    op.drop_index('ix_evaluation_aggregates_item_pk', table_name='evaluation_aggregates')
    op.drop_index('ix_evaluation_aggregates_run_id', table_name='evaluation_aggregates')
    op.drop_table('evaluation_aggregates')

    op.drop_index('ix_evaluation_judgments_item_pk', table_name='evaluation_judgments')
    op.drop_index('ix_evaluation_judgments_run_id', table_name='evaluation_judgments')
    op.drop_table('evaluation_judgments')

    op.drop_index('ix_evaluation_items_item_id', table_name='evaluation_items')
    op.drop_index('ix_evaluation_items_run_id', table_name='evaluation_items')
    op.drop_table('evaluation_items')

    op.drop_index('ix_evaluation_runs_user_id', table_name='evaluation_runs')
    op.drop_table('evaluation_runs')