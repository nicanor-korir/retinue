"""Add conversation and chat feature support to Retinue.

This migration adds support for user-agent conversations, chat, brainstorming,
and intelligent project creation from conversations.

Changes:
- Add conversations table
- Add conversation_messages table
- Add conversation_participants table
- Add conversation_topics table
- Add project_creation_intents table
- Add conversation_analytics table
- Update projects table with conversation references

Revision ID: 005_conversations
Revises: 004_phase2_analytics
Create Date: 2025-11-24 21:00:00.000000

This migration is NON-BREAKING - all new tables and columns have appropriate
defaults to ensure backward compatibility.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005_conversations'
down_revision: Union[str, Sequence[str], None] = '004_phase2_analytics'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema for conversation support."""

    # ===== CREATE NEW TABLES =====

    # 1. Conversations table
    op.create_table(
        'conversations',
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('conversation_type', sa.Enum('agent_chat', 'project_discussion', 'brainstorm', name='conversationtype'), nullable=False),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),

        # Context References
        sa.Column('primary_agent_id', sa.String(100), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by_user_id', sa.String(100), nullable=False, server_default='user_1'),

        # Status & Metadata
        sa.Column('status', sa.Enum('active', 'archived', 'converted_to_project', name='conversationstatus'), nullable=False, server_default='active'),
        sa.Column('is_pinned', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('tags', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),

        # RAG Integration
        sa.Column('embedding_id', sa.String(255), nullable=True),
        sa.Column('rag_indexed_at', sa.TIMESTAMP(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('last_message_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('archived_at', sa.TIMESTAMP(), nullable=True),

        # Metadata
        sa.Column('participant_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('message_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('meta_data', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),

        sa.PrimaryKeyConstraint('conversation_id', name='conversations_pkey'),
        sa.ForeignKeyConstraint(['primary_agent_id'], ['agents.agent_id'], name='conversations_primary_agent_id_fkey'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], name='conversations_project_id_fkey'),
        sa.Index('idx_conversations_agent', 'primary_agent_id'),
        sa.Index('idx_conversations_project', 'project_id'),
        sa.Index('idx_conversations_user', 'created_by_user_id'),
        sa.Index('idx_conversations_status', 'status'),
        sa.Index('idx_conversations_created', 'created_at'),
    )

    # 2. Conversation Messages table
    op.create_table(
        'conversation_messages',
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Sender Information
        sa.Column('sender_type', sa.Enum('user', 'agent', 'system', name='sendertype'), nullable=False),
        sa.Column('sender_id', sa.String(100), nullable=False),
        sa.Column('sender_name', sa.String(255), nullable=True),

        # Message Content
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('content_type', sa.Enum('text', 'code', 'markdown', 'structured', name='contenttype'), nullable=False, server_default='text'),
        sa.Column('message_type', sa.Enum('message', 'system', 'project_suggestion', 'question', name='messagetypeconversation'), nullable=False, server_default='message'),

        # Message Context
        sa.Column('reply_to_message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('mentioned_users', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('mentioned_agents', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),

        # Agent-Specific Fields
        sa.Column('agent_thinking', sa.Text(), nullable=True),
        sa.Column('agent_confidence', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('tools_used', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),

        # Structured Data
        sa.Column('attachments', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('message_metadata', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),

        # Project Creation Context
        sa.Column('suggested_project_data', postgresql.JSONB(), nullable=True),

        # RAG Integration
        sa.Column('embedding_id', sa.String(255), nullable=True),
        sa.Column('rag_contexts', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),

        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('edited_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('deleted_at', sa.TIMESTAMP(), nullable=True),

        # Status
        sa.Column('is_edited', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('read_by', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),

        sa.PrimaryKeyConstraint('message_id', name='conversation_messages_pkey'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.conversation_id'], ondelete='CASCADE', name='conversation_messages_conversation_id_fkey'),
        sa.ForeignKeyConstraint(['reply_to_message_id'], ['conversation_messages.message_id'], name='conversation_messages_reply_to_message_id_fkey'),
        sa.Index('idx_conversation_messages_conversation', 'conversation_id'),
        sa.Index('idx_conversation_messages_sender', 'sender_id'),
        sa.Index('idx_conversation_messages_created', 'created_at'),
    )

    # 3. Conversation Participants table
    op.create_table(
        'conversation_participants',
        sa.Column('participant_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Participant Info
        sa.Column('participant_type', sa.Enum('user', 'agent', name='participanttype'), nullable=False),
        sa.Column('participant_id_ref', sa.String(100), nullable=False),
        sa.Column('participant_name', sa.String(255), nullable=True),
        sa.Column('participant_role', sa.Enum('owner', 'participant', 'observer', 'agent', name='participantrole'), nullable=False),

        # Participation Metadata
        sa.Column('joined_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('left_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('last_read_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('unread_count', sa.Integer(), nullable=False, server_default='0'),

        # Preferences
        sa.Column('notifications_enabled', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('is_muted', sa.Boolean(), nullable=False, server_default=sa.text('false')),

        # Status
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('meta_data', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),

        sa.PrimaryKeyConstraint('participant_id', name='conversation_participants_pkey'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.conversation_id'], ondelete='CASCADE', name='conversation_participants_conversation_id_fkey'),
        sa.Index('idx_conversation_participants_conversation', 'conversation_id'),
        sa.Index('idx_conversation_participants_ref', 'participant_id_ref'),
    )

    # 4. Conversation Topics table
    op.create_table(
        'conversation_topics',
        sa.Column('topic_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),

        sa.Column('topic_name', sa.String(255), nullable=False),
        sa.Column('topic_type', sa.String(50), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),

        # Tracking
        sa.Column('message_ids', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('resolved', sa.Boolean(), nullable=False, server_default=sa.text('false')),

        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('resolved_at', sa.TIMESTAMP(), nullable=True),

        sa.PrimaryKeyConstraint('topic_id', name='conversation_topics_pkey'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.conversation_id'], ondelete='CASCADE', name='conversation_topics_conversation_id_fkey'),
        sa.Index('idx_conversation_topics_conversation', 'conversation_id'),
    )

    # 5. Project Creation Intents table
    op.create_table(
        'project_creation_intents',
        sa.Column('intent_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Intent Status
        sa.Column('status', sa.Enum('suggested', 'gathering_details', 'confirmed', 'cancelled', 'created', name='projectintentstatus'), nullable=False, server_default='suggested'),

        # Project Data
        sa.Column('suggested_by_agent_id', sa.String(100), nullable=True),
        sa.Column('project_name', sa.String(255), nullable=True),
        sa.Column('project_description', sa.Text(), nullable=True),
        sa.Column('project_type', sa.String(50), nullable=True),
        sa.Column('deliverable_type', sa.String(50), nullable=True),
        sa.Column('suggested_agents', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('priority', sa.String(50), nullable=True),

        # Extracted Context
        sa.Column('extracted_requirements', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('extracted_constraints', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('key_points', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),

        # User Interaction
        sa.Column('user_response', sa.Enum('interested', 'declined', 'needs_more_info', name='userresponse'), nullable=True),
        sa.Column('user_feedback', sa.Text(), nullable=True),

        # Workflow State
        sa.Column('current_step', sa.String(100), nullable=True),
        sa.Column('workflow_data', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),

        # Outcome
        sa.Column('created_project_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.TIMESTAMP(), nullable=True),

        sa.PrimaryKeyConstraint('intent_id', name='project_creation_intents_pkey'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.conversation_id'], name='project_creation_intents_conversation_id_fkey'),
        sa.ForeignKeyConstraint(['message_id'], ['conversation_messages.message_id'], name='project_creation_intents_message_id_fkey'),
        sa.ForeignKeyConstraint(['suggested_by_agent_id'], ['agents.agent_id'], name='project_creation_intents_agent_id_fkey'),
        sa.ForeignKeyConstraint(['created_project_id'], ['projects.project_id'], name='project_creation_intents_project_id_fkey'),
        sa.Index('idx_project_creation_intents_conversation', 'conversation_id'),
        sa.Index('idx_project_creation_intents_status', 'status'),
    )

    # 6. Conversation Analytics table
    op.create_table(
        'conversation_analytics',
        sa.Column('analytics_id', postgresql.UUID(as_uuid=True), nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),

        # Metrics
        sa.Column('total_messages', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('agent_messages', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('user_messages', sa.Integer(), nullable=False, server_default='0'),

        sa.Column('average_response_time_seconds', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('conversation_duration_minutes', sa.Integer(), nullable=True),

        sa.Column('topics_discussed', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('sentiment_score', sa.DECIMAL(3, 2), nullable=True),

        # Outcomes
        sa.Column('led_to_project_creation', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('user_satisfaction_rating', sa.Integer(), nullable=True),

        # Agent Performance
        sa.Column('agent_accuracy', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('tools_used_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rag_retrievals_count', sa.Integer(), nullable=False, server_default='0'),

        sa.Column('analyzed_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('meta_data', postgresql.JSONB(), nullable=False, server_default=sa.text("'{}'::jsonb")),

        sa.PrimaryKeyConstraint('analytics_id', name='conversation_analytics_pkey'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.conversation_id'], ondelete='CASCADE', name='conversation_analytics_conversation_id_fkey'),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], name='conversation_analytics_project_id_fkey'),
        sa.Index('idx_conversation_analytics_conversation', 'conversation_id'),
    )

    # ===== UPDATE EXISTING TABLES =====

    # Add conversation references to projects table
    op.add_column('projects', sa.Column('source_conversation_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('projects', sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key('projects_source_conversation_id_fkey', 'projects', 'conversations', ['source_conversation_id'], ['conversation_id'])
    op.create_foreign_key('projects_conversation_id_fkey', 'projects', 'conversations', ['conversation_id'], ['conversation_id'])


def downgrade() -> None:
    """Downgrade database schema for conversation support."""

    # Remove conversation references from projects table
    op.drop_constraint('projects_conversation_id_fkey', 'projects', type_='foreignkey')
    op.drop_constraint('projects_source_conversation_id_fkey', 'projects', type_='foreignkey')
    op.drop_column('projects', 'conversation_id')
    op.drop_column('projects', 'source_conversation_id')

    # Drop tables in reverse order
    op.drop_table('conversation_analytics')
    op.drop_table('project_creation_intents')
    op.drop_table('conversation_topics')
    op.drop_table('conversation_participants')
    op.drop_table('conversation_messages')
    op.drop_table('conversations')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS userresponse')
    op.execute('DROP TYPE IF EXISTS projectintentstatus')
    op.execute('DROP TYPE IF EXISTS participantrole')
    op.execute('DROP TYPE IF EXISTS participanttype')
    op.execute('DROP TYPE IF EXISTS messagetypeconversation')
    op.execute('DROP TYPE IF EXISTS contenttype')
    op.execute('DROP TYPE IF EXISTS sendertype')
    op.execute('DROP TYPE IF EXISTS conversationstatus')
    op.execute('DROP TYPE IF EXISTS conversationtype')
