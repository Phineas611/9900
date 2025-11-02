from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1c7d89dd359'
down_revision = '04622b31c520'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('eval_lab_records', sa.Column('contract_id', sa.String(length=128), nullable=True))
    op.add_column('eval_lab_records', sa.Column('sentence_id', sa.String(length=128), nullable=True))
    op.add_column('eval_lab_records', sa.Column('model_id', sa.String(length=64), nullable=True))
    op.create_index(op.f('ix_eval_lab_records_contract_id'), 'eval_lab_records', ['contract_id'], unique=False)
    op.create_index(op.f('ix_eval_lab_records_sentence_id'), 'eval_lab_records', ['sentence_id'], unique=False)


def downgrade():
    op.drop_index(op.f('ix_eval_lab_records_sentence_id'), table_name='eval_lab_records')
    op.drop_index(op.f('ix_eval_lab_records_contract_id'), table_name='eval_lab_records')
    op.drop_column('eval_lab_records', 'sentence_id')
    op.drop_column('eval_lab_records', 'contract_id')
    op.drop_column('eval_lab_records', 'model_id')