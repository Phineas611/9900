"""add contract sentence model fields

Revision ID: 5e6f7a8b9c0d
Revises: 4d5e6f7a8b9c
Create Date: 2023-07-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5e6f7a8b9c0d'
down_revision = '4d5e6f7a8b9c'
branch_labels = None
depends_on = None


def upgrade():
    # 添加新字段到eval_lab_records表
    op.add_column('eval_lab_records', sa.Column('contract_id', sa.String(128), nullable=True))
    op.add_column('eval_lab_records', sa.Column('sentence_id', sa.String(128), nullable=True))
    op.add_column('eval_lab_records', sa.Column('model_id', sa.String(64), nullable=True))
    
    # 创建索引以提高查询性能
    op.create_index('ix_eval_lab_records_contract_id', 'eval_lab_records', ['contract_id'])
    op.create_index('ix_eval_lab_records_sentence_id', 'eval_lab_records', ['sentence_id'])


def downgrade():
    # 删除索引
    op.drop_index('ix_eval_lab_records_contract_id', 'eval_lab_records')
    op.drop_index('ix_eval_lab_records_sentence_id', 'eval_lab_records')
    
    # 删除列
    op.drop_column('eval_lab_records', 'contract_id')
    op.drop_column('eval_lab_records', 'sentence_id')
    op.drop_column('eval_lab_records', 'model_id')