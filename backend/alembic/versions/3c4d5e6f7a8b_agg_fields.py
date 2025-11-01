"""
Add agg_label, class_agreement, needs_review to evaluation_aggregates

Revision ID: 3c4d5e6f7a8b
Revises: 1a2b3c4d5e6f
Create Date: 2025-10-30
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3c4d5e6f7a8b'
down_revision = '1a2b3c4d5e6f'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite supports ADD COLUMN
    op.add_column('evaluation_aggregates', sa.Column('agg_label', sa.String(length=32), nullable=True))
    op.add_column('evaluation_aggregates', sa.Column('class_agreement', sa.Boolean(), nullable=True))
    op.add_column('evaluation_aggregates', sa.Column('needs_review', sa.Boolean(), nullable=False, server_default=sa.text('0')))


def downgrade() -> None:
    # SQLite before 3.35 doesn't support DROP COLUMN; skipping full downgrade for brevity
    pass