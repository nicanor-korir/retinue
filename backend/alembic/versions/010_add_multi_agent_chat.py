"""Add multi-agent chat system

Revision ID: 010_multi_agent_chat
Revises: 009_intelligent_knowledge
Create Date: 2025-01-28 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '010_multi_agent_chat'
down_revision = '009_intelligent_knowledge'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create multi-agent chat tables."""

    # 1. Create agent_invitations table
    op.create_table(
        'agent_invitations',
        sa.Column('invitation_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('invited_by_type', sa.String(20), nullable=False),
        sa.Column('invited_by_id', sa.String(100), nullable=False),
        sa.Column('invited_by_name', sa.String(255), nullable=True),
        sa.Column('invitation_reason', sa.Text, nullable=True),
        sa.Column('context_summary', postgresql.JSONB, server_default='{}'),
        sa.Column('specific_question', sa.Text, nullable=True),
        sa.Column('related_message_ids', postgresql.JSONB, server_default='[]'),
        sa.Column('conversation_context', postgresql.JSONB, server_default='{}'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending'),
        sa.Column('responded_at', sa.TIMESTAMP, nullable=True),
        sa.Column('response_message', sa.Text, nullable=True),
        sa.Column('prediction_score', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('invitation_type', sa.String(50), server_default='manual'),
        sa.Column('urgency', sa.String(20), server_default='normal'),
        sa.Column('priority_score', sa.Integer, server_default='0'),
        sa.Column('auto_accept', sa.Boolean, server_default='false'),
        sa.Column('requires_user_approval', sa.Boolean, server_default='true'),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column('expires_at', sa.TIMESTAMP, nullable=True),
        sa.Column('accepted_at', sa.TIMESTAMP, nullable=True),
        sa.Column('declined_at', sa.TIMESTAMP, nullable=True),
        sa.Column('resulted_in_participation', sa.Boolean, server_default='false'),
        sa.Column('participation_duration_minutes', sa.Integer, nullable=True),
        sa.Column('meta_data', postgresql.JSONB, server_default='{}'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.conversation_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.agent_id'])
    )

    # Create indexes for agent_invitations
    op.create_index('idx_agent_invitations_conversation', 'agent_invitations', ['conversation_id'])
    op.create_index('idx_agent_invitations_agent', 'agent_invitations', ['agent_id'])
    op.create_index('idx_agent_invitations_status', 'agent_invitations', ['status'])
    op.create_index('idx_agent_invitations_created', 'agent_invitations', ['created_at'])

    # 2. Create agent_presence table
    op.create_table(
        'agent_presence',
        sa.Column('presence_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('activity', sa.String(100), nullable=True),
        sa.Column('activity_details', postgresql.JSONB, server_default='{}'),
        sa.Column('joined_at', sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column('last_active_at', sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column('last_message_at', sa.TIMESTAMP, nullable=True),
        sa.Column('last_status_change_at', sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column('response_count', sa.Integer, server_default='0'),
        sa.Column('average_response_time_seconds', sa.DECIMAL(10, 2), nullable=True),
        sa.Column('total_active_time_minutes', sa.Integer, server_default='0'),
        sa.Column('is_online', sa.Boolean, server_default='true'),
        sa.Column('current_turn_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('meta_data', postgresql.JSONB, server_default='{}'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.conversation_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.agent_id']),
        sa.UniqueConstraint('conversation_id', 'agent_id', name='uq_agent_presence_conversation_agent')
    )

    # Create indexes for agent_presence
    op.create_index('idx_agent_presence_conversation', 'agent_presence', ['conversation_id'])
    op.create_index('idx_agent_presence_agent', 'agent_presence', ['agent_id'])
    op.create_index('idx_agent_presence_status', 'agent_presence', ['status'])
    op.create_index('idx_agent_presence_last_active', 'agent_presence', ['last_active_at'])

    # 3. Create conversation_turns table
    op.create_table(
        'conversation_turns',
        sa.Column('turn_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('turn_number', sa.Integer, nullable=False),
        sa.Column('triggered_by_message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('assigned_agents', postgresql.JSONB, server_default='[]'),
        sa.Column('completed_agents', postgresql.JSONB, server_default='[]'),
        sa.Column('pending_agents', postgresql.JSONB, server_default='[]'),
        sa.Column('skipped_agents', postgresql.JSONB, server_default='[]'),
        sa.Column('response_message_ids', postgresql.JSONB, server_default='[]'),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('turn_type', sa.String(50), server_default='parallel'),
        sa.Column('started_at', sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column('expected_completion_at', sa.TIMESTAMP, nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP, nullable=True),
        sa.Column('expired_at', sa.TIMESTAMP, nullable=True),
        sa.Column('coordination_strategy', sa.String(50), server_default='parallel'),
        sa.Column('max_response_time_seconds', sa.Integer, server_default='120'),
        sa.Column('allow_parallel_responses', sa.Boolean, server_default='true'),
        sa.Column('agent_response_order', postgresql.JSONB, server_default='[]'),
        sa.Column('current_agent_index', sa.Integer, server_default='0'),
        sa.Column('turn_context', postgresql.JSONB, server_default='{}'),
        sa.Column('meta_data', postgresql.JSONB, server_default='{}'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.conversation_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['triggered_by_message_id'], ['conversation_messages.message_id'])
    )

    # Create indexes for conversation_turns
    op.create_index('idx_conversation_turns_conversation', 'conversation_turns', ['conversation_id'])
    op.create_index('idx_conversation_turns_turn_number', 'conversation_turns', ['conversation_id', 'turn_number'])
    op.create_index('idx_conversation_turns_status', 'conversation_turns', ['status'])

    # 4. Create agent_collaboration_sessions table
    op.create_table(
        'agent_collaboration_sessions',
        sa.Column('session_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('participating_agents', postgresql.JSONB, server_default='[]'),
        sa.Column('primary_agent_id', sa.String(100), nullable=True),
        sa.Column('supporting_agents', postgresql.JSONB, server_default='[]'),
        sa.Column('session_purpose', sa.String(500), nullable=True),
        sa.Column('expertise_areas_combined', postgresql.JSONB, server_default='[]'),
        sa.Column('collaboration_type', sa.String(50), nullable=True),
        sa.Column('task_completed', sa.Boolean, server_default='false'),
        sa.Column('user_satisfaction', sa.Integer, nullable=True),
        sa.Column('collaboration_quality_score', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('total_messages', sa.Integer, server_default='0'),
        sa.Column('total_duration_minutes', sa.Integer, nullable=True),
        sa.Column('turn_count', sa.Integer, server_default='0'),
        sa.Column('started_at', sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column('ended_at', sa.TIMESTAMP, nullable=True),
        sa.Column('effectiveness_analysis', postgresql.JSONB, server_default='{}'),
        sa.Column('learnings_extracted', postgresql.JSONB, server_default='[]'),
        sa.Column('meta_data', postgresql.JSONB, server_default='{}'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.conversation_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['primary_agent_id'], ['agents.agent_id'])
    )

    # Create indexes for agent_collaboration_sessions
    op.create_index('idx_agent_collaboration_conversation', 'agent_collaboration_sessions', ['conversation_id'])

    # 5. Create agent_expertise_tags table
    op.create_table(
        'agent_expertise_tags',
        sa.Column('tag_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('expertise_area', sa.String(100), nullable=False),
        sa.Column('proficiency_level', sa.Integer, server_default='5'),
        sa.Column('confidence_score', sa.DECIMAL(3, 2), server_default='0.8'),
        sa.Column('demonstrated_count', sa.Integer, server_default='0'),
        sa.Column('success_rate', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('last_used_at', sa.TIMESTAMP, nullable=True),
        sa.Column('related_keywords', postgresql.JSONB, server_default='[]'),
        sa.Column('domain_specific_terms', postgresql.JSONB, server_default='[]'),
        sa.Column('learned_from_knowledge_base', sa.Boolean, server_default='false'),
        sa.Column('manually_assigned', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column('meta_data', postgresql.JSONB, server_default='{}'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.agent_id'])
    )

    # Create indexes for agent_expertise_tags
    op.create_index('idx_agent_expertise_tags_agent', 'agent_expertise_tags', ['agent_id'])
    op.create_index('idx_agent_expertise_tags_area', 'agent_expertise_tags', ['expertise_area'])

    # 6. Create conversation_agent_suggestions table
    op.create_table(
        'conversation_agent_suggestions',
        sa.Column('suggestion_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('relevance_score', sa.DECIMAL(3, 2), nullable=False),
        sa.Column('reasoning', sa.Text, nullable=True),
        sa.Column('expertise_match_score', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('historical_success_score', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('user_preference_score', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('context_fit_score', sa.DECIMAL(3, 2), nullable=True),
        sa.Column('matched_keywords', postgresql.JSONB, server_default='[]'),
        sa.Column('matched_expertise_areas', postgresql.JSONB, server_default='[]'),
        sa.Column('triggering_message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('shown_to_user', sa.Boolean, server_default='false'),
        sa.Column('shown_at', sa.TIMESTAMP, nullable=True),
        sa.Column('user_action', sa.String(50), nullable=True),
        sa.Column('user_action_at', sa.TIMESTAMP, nullable=True),
        sa.Column('resulted_in_invitation', sa.Boolean, server_default='false'),
        sa.Column('invitation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('feedback_collected', sa.Boolean, server_default='false'),
        sa.Column('suggestion_helpful', sa.Boolean, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column('meta_data', postgresql.JSONB, server_default='{}'),
        sa.ForeignKeyConstraint(['conversation_id'], ['conversations.conversation_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.agent_id']),
        sa.ForeignKeyConstraint(['invitation_id'], ['agent_invitations.invitation_id'])
    )

    # Create indexes for conversation_agent_suggestions
    op.create_index('idx_conversation_agent_suggestions_conversation', 'conversation_agent_suggestions', ['conversation_id'])
    op.create_index('idx_conversation_agent_suggestions_agent', 'conversation_agent_suggestions', ['agent_id'])
    op.create_index('idx_conversation_agent_suggestions_created', 'conversation_agent_suggestions', ['created_at'])

    # 7. Enhance existing conversation_participants table
    op.add_column('conversation_participants', sa.Column('invitation_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('conversation_participants', sa.Column('expertise_tags', postgresql.JSONB, server_default='[]'))
    op.add_column('conversation_participants', sa.Column('can_respond', sa.Boolean, server_default='true'))
    op.add_column('conversation_participants', sa.Column('response_priority', sa.Integer, server_default='0'))
    op.add_column('conversation_participants', sa.Column('last_notified_at', sa.TIMESTAMP, nullable=True))
    op.add_column('conversation_participants', sa.Column('notification_preferences', postgresql.JSONB, server_default='{}'))

    # Add foreign key for invitation_id
    op.create_foreign_key(
        'fk_conversation_participants_invitation',
        'conversation_participants',
        'agent_invitations',
        ['invitation_id'],
        ['invitation_id']
    )

    # 8. Enhance existing conversation_messages table
    op.add_column('conversation_messages', sa.Column('turn_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.add_column('conversation_messages', sa.Column('responding_to_agents', postgresql.JSONB, server_default='[]'))
    op.add_column('conversation_messages', sa.Column('agent_collaboration_context', postgresql.JSONB, server_default='{}'))
    op.add_column('conversation_messages', sa.Column('requires_agent_response', sa.Boolean, server_default='false'))
    op.add_column('conversation_messages', sa.Column('requested_agents', postgresql.JSONB, server_default='[]'))

    # Add foreign key for turn_id
    op.create_foreign_key(
        'fk_conversation_messages_turn',
        'conversation_messages',
        'conversation_turns',
        ['turn_id'],
        ['turn_id']
    )


def downgrade() -> None:
    """Remove multi-agent chat tables."""

    # Drop foreign keys from enhanced tables first
    op.drop_constraint('fk_conversation_messages_turn', 'conversation_messages', type_='foreignkey')
    op.drop_constraint('fk_conversation_participants_invitation', 'conversation_participants', type_='foreignkey')

    # Drop added columns from existing tables
    op.drop_column('conversation_messages', 'requested_agents')
    op.drop_column('conversation_messages', 'requires_agent_response')
    op.drop_column('conversation_messages', 'agent_collaboration_context')
    op.drop_column('conversation_messages', 'responding_to_agents')
    op.drop_column('conversation_messages', 'turn_id')

    op.drop_column('conversation_participants', 'notification_preferences')
    op.drop_column('conversation_participants', 'last_notified_at')
    op.drop_column('conversation_participants', 'response_priority')
    op.drop_column('conversation_participants', 'can_respond')
    op.drop_column('conversation_participants', 'expertise_tags')
    op.drop_column('conversation_participants', 'invitation_id')

    # Drop new tables
    op.drop_table('conversation_agent_suggestions')
    op.drop_table('agent_expertise_tags')
    op.drop_table('agent_collaboration_sessions')
    op.drop_table('conversation_turns')
    op.drop_table('agent_presence')
    op.drop_table('agent_invitations')
