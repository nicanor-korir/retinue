"""Add context intelligence tables and columns

Revision ID: 007_add_context_intelligence
Revises: 006_enhance_message_status
Create Date: 2025-11-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB, TIMESTAMP


# revision identifiers, used by Alembic.
revision = '007_add_context_intelligence'
down_revision = '006_enhance_message_status'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create conversation_context table
    op.create_table(
        'conversation_context',
        sa.Column('context_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('conversation_id', UUID(as_uuid=True), sa.ForeignKey('conversations.conversation_id', ondelete='CASCADE'), nullable=False),
        sa.Column('entities', JSONB, server_default='{}'),
        sa.Column('context_summary', JSONB, server_default='{}'),
        sa.Column('dominant_intent', sa.String(50)),
        sa.Column('active_entities', JSONB, server_default='[]'),
        sa.Column('indexed_message_count', sa.Integer, server_default='0'),
        sa.Column('last_indexed_at', TIMESTAMP),
        sa.Column('created_at', TIMESTAMP, server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now())
    )
    op.create_index('idx_conversation_context_conversation_id', 'conversation_context', ['conversation_id'])

    # Create user_activity_log table
    op.create_table(
        'user_activity_log',
        sa.Column('activity_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('user_id', sa.String(100), nullable=False),
        sa.Column('activity_type', sa.String(50), nullable=False),
        sa.Column('context', JSONB, server_default='{}'),
        sa.Column('timestamp', TIMESTAMP, server_default=sa.func.now()),
        sa.Column('session_id', sa.String(100)),
        sa.Column('ip_address', sa.String(50))
    )
    op.create_index('idx_user_activity_log_user_id', 'user_activity_log', ['user_id'])
    op.create_index('idx_user_activity_log_timestamp', 'user_activity_log', ['timestamp'])
    op.create_index('idx_user_activity_log_type', 'user_activity_log', ['activity_type'])

    # Create business_knowledge table
    op.create_table(
        'business_knowledge',
        sa.Column('document_id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('subcategory', sa.String(100)),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('summary', sa.Text),
        sa.Column('tags', JSONB, server_default='[]'),
        sa.Column('version', sa.Integer, server_default='1'),
        sa.Column('is_active', sa.Boolean, server_default='true'),
        sa.Column('embedding_id', sa.String(100)),
        sa.Column('rag_indexed_at', TIMESTAMP),
        sa.Column('created_at', TIMESTAMP, server_default=sa.func.now()),
        sa.Column('updated_at', TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('created_by_agent_id', sa.String(100), sa.ForeignKey('agents.agent_id'))
    )
    op.create_index('idx_business_knowledge_category', 'business_knowledge', ['category'])
    op.create_index('idx_business_knowledge_active', 'business_knowledge', ['is_active'])

    # Add columns to conversation_messages
    op.add_column('conversation_messages', sa.Column('extracted_entities', JSONB, server_default='{}'))
    op.add_column('conversation_messages', sa.Column('intent_classification', sa.String(50)))
    op.add_column('conversation_messages', sa.Column('semantic_summary', sa.Text))

    # Add columns to conversations
    op.add_column('conversations', sa.Column('context_summary', JSONB, server_default='{}'))
    op.add_column('conversations', sa.Column('active_entities', JSONB, server_default='{}'))


def downgrade() -> None:
    # Remove columns from conversations
    op.drop_column('conversations', 'active_entities')
    op.drop_column('conversations', 'context_summary')

    # Remove columns from conversation_messages
    op.drop_column('conversation_messages', 'semantic_summary')
    op.drop_column('conversation_messages', 'intent_classification')
    op.drop_column('conversation_messages', 'extracted_entities')

    # Drop business_knowledge table
    op.drop_index('idx_business_knowledge_active', 'business_knowledge')
    op.drop_index('idx_business_knowledge_category', 'business_knowledge')
    op.drop_table('business_knowledge')

    # Drop user_activity_log table
    op.drop_index('idx_user_activity_log_type', 'user_activity_log')
    op.drop_index('idx_user_activity_log_timestamp', 'user_activity_log')
    op.drop_index('idx_user_activity_log_user_id', 'user_activity_log')
    op.drop_table('user_activity_log')

    # Drop conversation_context table
    op.drop_index('idx_conversation_context_conversation_id', 'conversation_context')
    op.drop_table('conversation_context')
