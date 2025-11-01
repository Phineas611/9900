"""
Make gold_label nullable in evaluation_items

Revision ID: 2b3c4d5e6f7g
Revises: 1a2b3c4d5e6f
Create Date: 2025-01-30
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2b3c4d5e6f7g'
down_revision = '1a2b3c4d5e6f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite doesn't support ALTER COLUMN, so we need to recreate the table
    # Create new table with nullable gold_label
    op.create_table(
        'evaluation_items_new',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('run_id', sa.String(length=36), sa.ForeignKey('evaluation_runs.id'), nullable=False),
        sa.Column('item_id', sa.String(length=128), nullable=False),
        sa.Column('sentence', sa.Text(), nullable=False),
        sa.Column('gold_label', sa.String(length=64), nullable=True),  # Now nullable
        sa.Column('predicted_label', sa.String(length=64), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
    )
    op.create_index('ix_evaluation_items_new_run_id', 'evaluation_items_new', ['run_id'])
    op.create_index('ix_evaluation_items_new_item_id', 'evaluation_items_new', ['item_id'])
    
    # Copy data from old table to new table
    op.execute("""
        INSERT INTO evaluation_items_new (id, run_id, item_id, sentence, gold_label, predicted_label, rationale)
        SELECT id, run_id, item_id, sentence, gold_label, predicted_label, rationale
        FROM evaluation_items
    """)
    
    # Drop old table and rename new table
    op.drop_table('evaluation_items')
    op.rename_table('evaluation_items_new', 'evaluation_items')


def downgrade() -> None:
    # Recreate table with non-nullable gold_label
    op.create_table(
        'evaluation_items_old',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('run_id', sa.String(length=36), sa.ForeignKey('evaluation_runs.id'), nullable=False),
        sa.Column('item_id', sa.String(length=128), nullable=False),
        sa.Column('sentence', sa.Text(), nullable=False),
        sa.Column('gold_label', sa.String(length=64), nullable=False),  # Back to non-nullable
        sa.Column('predicted_label', sa.String(length=64), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
    )
    op.create_index('ix_evaluation_items_old_run_id', 'evaluation_items_old', ['run_id'])
    op.create_index('ix_evaluation_items_old_item_id', 'evaluation_items_old', ['item_id'])
    
    # Copy data (excluding rows with NULL gold_label)
    op.execute("""
        INSERT INTO evaluation_items_old (id, run_id, item_id, sentence, gold_label, predicted_label, rationale)
        SELECT id, run_id, item_id, sentence, gold_label, predicted_label, rationale
        FROM evaluation_items
        WHERE gold_label IS NOT NULL
    """)
    
    # Drop new table and rename old table
    op.drop_table('evaluation_items')
    op.rename_table('evaluation_items_old', 'evaluation_items')