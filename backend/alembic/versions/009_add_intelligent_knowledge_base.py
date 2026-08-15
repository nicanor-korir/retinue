"""Add intelligent knowledge base system

Revision ID: 009_intelligent_knowledge
Revises: 008_add_multi_department_support
Create Date: 2025-11-27 12:00:00.000000

This migration adds the comprehensive intelligent knowledge base system including:
- Knowledge entries with vector embeddings (pgvector)
- Knowledge relationships and graph
- User knowledge profiles and preferences
- Extraction candidates for automatic knowledge extraction
- Agent involvement predictions
- Usage logging and feedback tracking
- Conversation tracking for knowledge extraction
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '009_intelligent_knowledge'
down_revision: Union[str, None] = '008_add_multi_department_support'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database with intelligent knowledge base tables."""

    # First, ensure pgvector extension is available
    op.execute('CREATE EXTENSION IF NOT EXISTS vector')

    # ===== KNOWLEDGE CATEGORIES =====
    op.create_table(
        'knowledge_categories',
        sa.Column('category_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False, index=True),
        sa.Column('slug', sa.String(200), unique=True, nullable=False, index=True),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('parent_category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('path', postgresql.ARRAY(sa.String(200)), default=sa.text("'{}'::varchar[]")),
        sa.Column('level', sa.Integer, nullable=False, default=0),
        sa.Column('display_order', sa.Integer, default=0),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('color', sa.String(20), nullable=True),
        sa.Column('entry_count', sa.Integer, default=0),
        sa.Column('meta_data', postgresql.JSONB, default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.TIMESTAMP, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['parent_category_id'], ['knowledge_categories.category_id'])
    )

    # ===== KNOWLEDGE ENTRIES =====
    op.create_table(
        'knowledge_entries',
        sa.Column('entry_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False, index=True),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('content_format', sa.String(20), default='markdown'),
        sa.Column('content_structured', postgresql.JSONB, default=sa.text("'{}'::jsonb")),

        # Classification
        sa.Column('entry_type', sa.String(50), nullable=False, index=True),
        sa.Column('primary_category_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('categories', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=sa.text("'{}'::uuid[]")),
        sa.Column('tags', postgresql.ARRAY(sa.String(100)), default=sa.text("'{}'::varchar[]")),
        sa.Column('keywords', postgresql.ARRAY(sa.String(100)), default=sa.text("'{}'::varchar[]")),
        sa.Column('domain', sa.String(100), nullable=True, index=True),

        # Scoring
        sa.Column('confidence_score', sa.Float, nullable=False, default=0.0),
        sa.Column('novelty_score', sa.Float, nullable=False, default=0.0),
        sa.Column('relevance_score', sa.Float, nullable=False, default=0.0),
        sa.Column('quality_score', sa.Float, nullable=False, default=0.0),

        # Context
        sa.Column('problem_context', sa.Text, nullable=True),
        sa.Column('applicable_scenarios', postgresql.JSONB, default=sa.text("'[]'::jsonb")),
        sa.Column('prerequisites', postgresql.JSONB, default=sa.text("'[]'::jsonb")),
        sa.Column('limitations', postgresql.JSONB, default=sa.text("'[]'::jsonb")),
        sa.Column('related_technologies', postgresql.ARRAY(sa.String(100)), default=sa.text("'{}'::varchar[]")),

        # Validation
        sa.Column('validation_status', sa.String(50), nullable=False, default='unvalidated', index=True),
        sa.Column('validated_by_agent_id', sa.String(100), nullable=True),
        sa.Column('validated_at', sa.TIMESTAMP, nullable=True),
        sa.Column('validation_notes', sa.Text, nullable=True),

        # Provenance
        sa.Column('source_type', sa.String(50), nullable=False),
        sa.Column('source_conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_message_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=sa.text("'{}'::uuid[]")),
        sa.Column('created_by_type', sa.String(20), nullable=False),
        sa.Column('created_by_id', sa.String(100), nullable=False),
        sa.Column('contributors', postgresql.ARRAY(sa.String(100)), default=sa.text("'{}'::varchar[]")),

        # Lifecycle
        sa.Column('status', sa.String(50), nullable=False, default='draft', index=True),
        sa.Column('version', sa.Integer, nullable=False, default=1),
        sa.Column('superseded_by_id', postgresql.UUID(as_uuid=True), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('last_accessed_at', sa.TIMESTAMP, nullable=True, index=True),

        # Usage Metrics
        sa.Column('view_count', sa.Integer, default=0),
        sa.Column('use_count', sa.Integer, default=0),
        sa.Column('helpfulness_up', sa.Integer, default=0),
        sa.Column('helpfulness_down', sa.Integer, default=0),

        # Vector Embeddings (pgvector - 1536 dimensions for OpenAI/similar)
        sa.Column('title_embedding', postgresql.ARRAY(sa.Float), nullable=True),  # Using ARRAY for now
        sa.Column('summary_embedding', postgresql.ARRAY(sa.Float), nullable=True),
        sa.Column('content_embedding', postgresql.ARRAY(sa.Float), nullable=True),
        sa.Column('problem_embedding', postgresql.ARRAY(sa.Float), nullable=True),

        # Metadata
        sa.Column('meta_data', postgresql.JSONB, default=sa.text("'{}'::jsonb")),

        sa.ForeignKeyConstraint(['primary_category_id'], ['knowledge_categories.category_id']),
        sa.ForeignKeyConstraint(['source_project_id'], ['projects.project_id']),
        sa.ForeignKeyConstraint(['source_task_id'], ['tasks.task_id']),
        sa.ForeignKeyConstraint(['validated_by_agent_id'], ['agents.agent_id']),
        sa.ForeignKeyConstraint(['superseded_by_id'], ['knowledge_entries.entry_id']),

        sa.CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='check_confidence_score'),
        sa.CheckConstraint('novelty_score >= 0 AND novelty_score <= 1', name='check_novelty_score'),
        sa.CheckConstraint('relevance_score >= 0 AND relevance_score <= 1', name='check_relevance_score'),
        sa.CheckConstraint('quality_score >= 0 AND quality_score <= 1', name='check_quality_score'),
    )

    # Create indexes for knowledge_entries
    op.create_index('idx_knowledge_entries_tags', 'knowledge_entries', ['tags'], postgresql_using='gin')
    op.create_index('idx_knowledge_entries_keywords', 'knowledge_entries', ['keywords'], postgresql_using='gin')
    op.create_index('idx_knowledge_entries_categories', 'knowledge_entries', ['categories'], postgresql_using='gin')

    # ===== KNOWLEDGE RELATIONSHIPS =====
    op.create_table(
        'knowledge_relationships',
        sa.Column('relationship_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('source_entry_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('target_entry_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('relationship_type', sa.String(50), nullable=False, index=True),
        sa.Column('strength', sa.Float, nullable=False, default=0.5),
        sa.Column('bidirectional', sa.Boolean, default=False),
        sa.Column('auto_generated', sa.Boolean, default=False),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('meta_data', postgresql.JSONB, default=sa.text("'{}'::jsonb")),

        sa.ForeignKeyConstraint(['source_entry_id'], ['knowledge_entries.entry_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_entry_id'], ['knowledge_entries.entry_id'], ondelete='CASCADE'),

        sa.CheckConstraint('strength >= 0 AND strength <= 1', name='check_strength'),
        sa.CheckConstraint('source_entry_id != target_entry_id', name='check_no_self_reference'),
    )

    # ===== KNOWLEDGE VERSIONS =====
    op.create_table(
        'knowledge_versions',
        sa.Column('version_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entry_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('version_number', sa.Integer, nullable=False),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('content', sa.Text, nullable=False),
        sa.Column('change_type', sa.String(50), nullable=False),
        sa.Column('change_summary', sa.Text, nullable=True),
        sa.Column('change_reason', sa.Text, nullable=True),
        sa.Column('changed_by_type', sa.String(20), nullable=False),
        sa.Column('changed_by_id', sa.String(100), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('meta_data', postgresql.JSONB, default=sa.text("'{}'::jsonb")),

        sa.ForeignKeyConstraint(['entry_id'], ['knowledge_entries.entry_id'], ondelete='CASCADE')
    )

    # ===== USER KNOWLEDGE PROFILES =====
    op.create_table(
        'user_knowledge_profiles',
        sa.Column('profile_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), unique=True, nullable=False, index=True),
        sa.Column('preferred_response_length', sa.String(20), default='moderate'),
        sa.Column('preferred_technical_depth', sa.String(20), default='intermediate'),
        sa.Column('preferred_communication_style', sa.String(20), default='professional'),
        sa.Column('formatting_preferences', postgresql.JSONB, default=sa.text("'{}'::jsonb")),
        sa.Column('expertise_areas', postgresql.JSONB, default=sa.text("'{}'::jsonb")),
        sa.Column('learning_goals', postgresql.ARRAY(sa.Text), default=sa.text("'{}'::text[]")),
        sa.Column('technologies_used', postgresql.ARRAY(sa.String(100)), default=sa.text("'{}'::varchar[]")),
        sa.Column('domains_worked_in', postgresql.ARRAY(sa.String(100)), default=sa.text("'{}'::varchar[]")),
        sa.Column('typical_active_hours', postgresql.JSONB, default=sa.text("'{}'::jsonb")),
        sa.Column('response_time_patterns', postgresql.JSONB, default=sa.text("'{}'::jsonb")),
        sa.Column('decision_making_style', sa.String(30), default='deliberate'),
        sa.Column('topics_discussed', postgresql.JSONB, default=sa.text("'{}'::jsonb")),
        sa.Column('preferred_agents', postgresql.JSONB, default=sa.text("'{}'::jsonb")),
        sa.Column('common_requests', postgresql.ARRAY(sa.Text), default=sa.text("'{}'::text[]")),
        sa.Column('inferred_preferences', postgresql.JSONB, default=sa.text("'{}'::jsonb")),
        sa.Column('communication_quirks', postgresql.JSONB, default=sa.text("'{}'::jsonb")),
        sa.Column('known_pet_peeves', postgresql.ARRAY(sa.Text), default=sa.text("'{}'::text[]")),
        sa.Column('profile_confidence', sa.Float, default=0.0),
        sa.Column('profile_completeness', sa.Float, default=0.0),
        sa.Column('last_updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('update_history', postgresql.JSONB, default=sa.text("'[]'::jsonb")),
        sa.Column('interest_embedding', postgresql.ARRAY(sa.Float), nullable=True),

        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.user_id']),

        sa.CheckConstraint('profile_confidence >= 0 AND profile_confidence <= 1', name='check_profile_confidence'),
        sa.CheckConstraint('profile_completeness >= 0 AND profile_completeness <= 1', name='check_profile_completeness'),
    )

    # ===== USER PREFERENCES =====
    op.create_table(
        'user_preferences',
        sa.Column('preference_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('preference_type', sa.String(20), nullable=False),
        sa.Column('category', sa.String(100), nullable=False, index=True),
        sa.Column('key', sa.String(200), nullable=False, index=True),
        sa.Column('value', postgresql.JSONB, nullable=False),
        sa.Column('confidence', sa.Float, nullable=False, default=0.0),
        sa.Column('source_conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('source_message_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=sa.text("'{}'::uuid[]")),
        sa.Column('times_confirmed', sa.Integer, default=0),
        sa.Column('times_contradicted', sa.Integer, default=0),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('valid_until', sa.TIMESTAMP, nullable=True),

        sa.ForeignKeyConstraint(['user_id'], ['user_profiles.user_id']),

        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='check_confidence'),
    )

    op.create_index('idx_user_pref_user_category', 'user_preferences', ['user_id', 'category'])

    # ===== EXTRACTION CANDIDATES =====
    op.create_table(
        'extraction_candidates',
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('message_range_start', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('message_range_end', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('extracted_content', postgresql.JSONB, nullable=False),
        sa.Column('extraction_type', sa.String(50), nullable=False, index=True),
        sa.Column('primary_category_guess', sa.String(200), nullable=True),
        sa.Column('confidence_score', sa.Float, nullable=False, default=0.0),
        sa.Column('novelty_score', sa.Float, nullable=False, default=0.0),
        sa.Column('relevance_score', sa.Float, nullable=False, default=0.0),
        sa.Column('extraction_quality', sa.Float, nullable=False, default=0.0),
        sa.Column('trigger_type', sa.String(50), nullable=False, index=True),
        sa.Column('trigger_details', postgresql.JSONB, default=sa.text("'{}'::jsonb")),
        sa.Column('status', sa.String(50), nullable=False, default='pending', index=True),
        sa.Column('processing_notes', sa.Text, nullable=True),
        sa.Column('reviewed_by_type', sa.String(20), nullable=True),
        sa.Column('reviewed_by_id', sa.String(100), nullable=True),
        sa.Column('review_decision', sa.String(20), nullable=True),
        sa.Column('review_notes', sa.Text, nullable=True),
        sa.Column('reviewed_at', sa.TIMESTAMP, nullable=True),
        sa.Column('converted_to_entry_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('merged_with_entry_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('updated_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), onupdate=sa.func.now()),

        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id']),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.task_id']),
        sa.ForeignKeyConstraint(['converted_to_entry_id'], ['knowledge_entries.entry_id']),
        sa.ForeignKeyConstraint(['merged_with_entry_id'], ['knowledge_entries.entry_id']),

        sa.CheckConstraint('confidence_score >= 0 AND confidence_score <= 1', name='check_extraction_confidence'),
        sa.CheckConstraint('novelty_score >= 0 AND novelty_score <= 1', name='check_extraction_novelty'),
        sa.CheckConstraint('relevance_score >= 0 AND relevance_score <= 1', name='check_extraction_relevance'),
        sa.CheckConstraint('extraction_quality >= 0 AND extraction_quality <= 1', name='check_extraction_quality'),
    )

    # ===== KNOWLEDGE USAGE LOG =====
    op.create_table(
        'knowledge_usage_log',
        sa.Column('log_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entry_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('used_in_conversation_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('used_in_message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('used_by_agent_id', sa.String(100), nullable=False),
        sa.Column('usage_type', sa.String(50), nullable=False, index=True),
        sa.Column('retrieval_query', sa.Text, nullable=True),
        sa.Column('retrieval_rank', sa.Integer, nullable=True),
        sa.Column('was_helpful', sa.Boolean, nullable=True),
        sa.Column('feedback_type', sa.String(50), nullable=True),
        sa.Column('feedback_text', sa.Text, nullable=True),
        sa.Column('led_to_update', sa.Boolean, default=False),
        sa.Column('used_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('conversation_context', postgresql.JSONB, default=sa.text("'{}'::jsonb")),

        sa.ForeignKeyConstraint(['entry_id'], ['knowledge_entries.entry_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['used_by_agent_id'], ['agents.agent_id'])
    )

    op.create_index('idx_usage_entry_time', 'knowledge_usage_log', ['entry_id', sa.text('used_at DESC')])

    # ===== KNOWLEDGE FEEDBACK =====
    op.create_table(
        'knowledge_feedback',
        sa.Column('feedback_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('entry_id', postgresql.UUID(as_uuid=True), nullable=False, index=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', sa.String(100), nullable=True),
        sa.Column('feedback_type', sa.String(50), nullable=False, index=True),
        sa.Column('rating', sa.Integer, nullable=True),
        sa.Column('comment', sa.Text, nullable=True),
        sa.Column('suggested_improvement', sa.Text, nullable=True),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('addressed', sa.Boolean, default=False),
        sa.Column('addressed_at', sa.TIMESTAMP, nullable=True),

        sa.ForeignKeyConstraint(['entry_id'], ['knowledge_entries.entry_id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.agent_id']),

        sa.CheckConstraint('rating >= 1 AND rating <= 5', name='check_feedback_rating'),
    )

    # ===== AGENT INVOLVEMENT PREDICTIONS =====
    op.create_table(
        'agent_involvement_predictions',
        sa.Column('prediction_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('message_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', sa.String(100), nullable=False, index=True),
        sa.Column('involvement_probability', sa.Float, nullable=False),
        sa.Column('confidence', sa.Float, nullable=False),
        sa.Column('predicted_contribution_type', sa.String(50), nullable=False),
        sa.Column('suggested_timing', sa.String(50), nullable=False),
        sa.Column('introduction_approach', sa.String(50), nullable=False),
        sa.Column('trigger_reasons', postgresql.JSONB, default=sa.text("'[]'::jsonb")),
        sa.Column('signal_strength', sa.Float, nullable=False),
        sa.Column('actual_involvement', sa.String(50), nullable=True),
        sa.Column('involvement_timing', sa.TIMESTAMP, nullable=True),
        sa.Column('user_satisfaction', sa.Float, nullable=True),
        sa.Column('contribution_quality', sa.Float, nullable=True),
        sa.Column('predicted_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('resolved_at', sa.TIMESTAMP, nullable=True),

        sa.ForeignKeyConstraint(['agent_id'], ['agents.agent_id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id']),

        sa.CheckConstraint('involvement_probability >= 0 AND involvement_probability <= 1', name='check_involvement_probability'),
        sa.CheckConstraint('confidence >= 0 AND confidence <= 1', name='check_involvement_confidence'),
        sa.CheckConstraint('signal_strength >= 0 AND signal_strength <= 1', name='check_signal_strength'),
    )

    # ===== AGENT INVOLVEMENT OUTCOMES =====
    op.create_table(
        'agent_involvement_outcomes',
        sa.Column('outcome_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', sa.String(100), nullable=False, index=True),
        sa.Column('involvement_type', sa.String(50), nullable=False),
        sa.Column('joined_at', sa.TIMESTAMP, nullable=False),
        sa.Column('left_at', sa.TIMESTAMP, nullable=True),
        sa.Column('messages_sent', sa.Integer, default=0),
        sa.Column('user_satisfaction_rating', sa.Float, nullable=True),
        sa.Column('contribution_helpfulness', sa.Float, nullable=True),
        sa.Column('response_quality_score', sa.Float, nullable=True),
        sa.Column('timing_appropriateness', sa.Float, nullable=True),
        sa.Column('was_predicted', sa.Boolean, default=False),
        sa.Column('prediction_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('prediction_accuracy', sa.Float, nullable=True),
        sa.Column('user_feedback', postgresql.JSONB, default=sa.text("'{}'::jsonb")),
        sa.Column('created_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now()),

        sa.ForeignKeyConstraint(['agent_id'], ['agents.agent_id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id']),
        sa.ForeignKeyConstraint(['prediction_id'], ['agent_involvement_predictions.prediction_id'])
    )

    # ===== CONVERSATIONS =====
    op.create_table(
        'conversations',
        sa.Column('conversation_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(255), nullable=True),
        sa.Column('summary', sa.Text, nullable=True),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_ids', postgresql.ARRAY(sa.String(100)), default=sa.text("'{}'::varchar[]")),
        sa.Column('status', sa.String(50), nullable=False, default='active'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True, index=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('extraction_status', sa.String(50), default='pending'),
        sa.Column('knowledge_entries_count', sa.Integer, default=0),
        sa.Column('started_at', sa.TIMESTAMP, nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('last_message_at', sa.TIMESTAMP, nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP, nullable=True),
        sa.Column('meta_data', postgresql.JSONB, default=sa.text("'{}'::jsonb")),

        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id']),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.task_id'])
    )


def downgrade() -> None:
    """Downgrade database by removing intelligent knowledge base tables."""

    # Drop tables in reverse order (respecting foreign key constraints)
    op.drop_table('conversations')
    op.drop_table('agent_involvement_outcomes')
    op.drop_table('agent_involvement_predictions')
    op.drop_table('knowledge_feedback')
    op.drop_table('knowledge_usage_log')
    op.drop_table('extraction_candidates')
    op.drop_table('user_preferences')
    op.drop_table('user_knowledge_profiles')
    op.drop_table('knowledge_versions')
    op.drop_table('knowledge_relationships')
    op.drop_table('knowledge_entries')
    op.drop_table('knowledge_categories')

    # Note: We don't drop the pgvector extension as it might be used by other tables
    # op.execute('DROP EXTENSION IF EXISTS vector')
