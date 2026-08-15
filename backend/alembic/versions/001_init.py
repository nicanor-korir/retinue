"""Initial schema creation.

Revision ID: 001
Revises:
Create Date: 2025-11-02 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create all tables from models."""
    # Create ENUM types
    agents_enum = sa.Enum('available', 'busy', 'blocked', 'offline', name='availability')
    agents_enum.create(op.get_bind(), checkfirst=True)

    projectstatus_enum = sa.Enum('PLANNING', 'IN_PROGRESS', 'REVIEW', 'COMPLETED', 'CANCELLED', 'ON_HOLD', 'FAILED', name='projectstatus')
    projectstatus_enum.create(op.get_bind(), checkfirst=True)

    priority_enum = sa.Enum('low', 'medium', 'high', 'critical', name='priority')
    priority_enum.create(op.get_bind(), checkfirst=True)

    taskstatus_enum = sa.Enum('PENDING', 'IN_PROGRESS', 'BLOCKED', 'REVIEW', 'COMPLETED', 'CANCELLED', 'FAILED', name='taskstatus')
    taskstatus_enum.create(op.get_bind(), checkfirst=True)

    messagetype_enum = sa.Enum('info', 'request', 'approval', 'alert', name='messagetype')
    messagetype_enum.create(op.get_bind(), checkfirst=True)

    taskragstatus_enum = sa.Enum('not_indexed', 'indexing', 'indexed', 'failed', name='taskragstatus')
    taskragstatus_enum.create(op.get_bind(), checkfirst=True)

    notificationtype_enum = sa.Enum('human_intervention_required', 'ceo_feedback', 'project_completed', 'project_failed', 'task_blocked', 'escalation', 'general', name='notificationtype')
    notificationtype_enum.create(op.get_bind(), checkfirst=True)

    # agents table
    op.create_table(
        'agents',
        sa.Column('agent_id', sa.String(100), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('role', sa.String(100), nullable=False),
        sa.Column('department', sa.String(50), nullable=False),
        sa.Column('reports_to', sa.String(100), nullable=True),
        sa.Column('permissions', postgresql.JSONB(), nullable=False),
        sa.Column('status', sa.String(50), server_default='active'),
        sa.Column('llm_model', sa.String(100), server_default='claude-3-5-sonnet-20241022'),
        sa.Column('system_prompt', sa.Text(), nullable=False),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('meta_data', postgresql.JSONB(), server_default='{}'),
        sa.ForeignKeyConstraint(['reports_to'], ['agents.agent_id']),
    )

    # agent_status table
    op.create_table(
        'agent_status',
        sa.Column('agent_id', sa.String(100), primary_key=True),
        sa.Column('current_task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('availability', sa.Enum('available', 'busy', 'blocked', 'offline', name='availability'), nullable=False),
        sa.Column('last_active', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('last_check_time', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('pending_approvals_count', sa.Integer(), server_default='0'),
        sa.Column('current_context', postgresql.JSONB(), server_default='{}'),
        sa.Column('health_status', sa.String(50), server_default='healthy'),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.agent_id'], ondelete='CASCADE'),
    )

    # projects table
    op.create_table(
        'projects',
        sa.Column('project_id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('PLANNING', 'IN_PROGRESS', 'REVIEW', 'COMPLETED', 'CANCELLED', 'ON_HOLD', 'FAILED', name='projectstatus'), nullable=False),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'critical', name='priority'), nullable=False),
        sa.Column('owner_agent_id', sa.String(100), nullable=False),
        sa.Column('requester_agent_id', sa.String(100), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('deadline', sa.TIMESTAMP(), nullable=True),
        sa.Column('completed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('agent_days_elapsed', sa.Integer(), server_default='0'),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('parent_project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('deleted_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('meta_data', postgresql.JSONB(), server_default='{}'),
        sa.Column('embedding_id', sa.String(255), nullable=True),
        sa.Column('rag_status', sa.Enum('not_indexed', 'indexing', 'indexed', 'failed', name='taskragstatus'), server_default='not_indexed'),
        sa.Column('rag_indexed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('rag_similarity_score', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['owner_agent_id'], ['agents.agent_id']),
        sa.ForeignKeyConstraint(['requester_agent_id'], ['agents.agent_id']),
    )

    # tasks table
    op.create_table(
        'tasks',
        sa.Column('task_id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_to_agent_id', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.Enum('PENDING', 'IN_PROGRESS', 'BLOCKED', 'REVIEW', 'COMPLETED', 'CANCELLED', 'FAILED', name='taskstatus'), nullable=False),
        sa.Column('dependencies', postgresql.JSONB(), server_default='[]'),
        sa.Column('approval_required_from', sa.String(100), nullable=True),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('parent_task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('estimated_hours', sa.Integer(), nullable=True),
        sa.Column('actual_hours', sa.Integer(), nullable=True),
        sa.Column('blocking_reason', sa.Text(), nullable=True),
        sa.Column('deleted_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('output', postgresql.JSONB(), nullable=True),
        sa.Column('review_started_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('embedding_id', sa.String(255), nullable=True),
        sa.Column('rag_status', sa.Enum('not_indexed', 'indexing', 'indexed', 'failed', name='taskragstatus'), server_default='not_indexed'),
        sa.Column('rag_indexed_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('rag_similarity_score', sa.Integer(), nullable=True),
        sa.Column('rag_contexts', postgresql.JSONB(), server_default='[]'),
        sa.Column('rag_patterns', postgresql.JSONB(), server_default='[]'),
        sa.Column('rag_last_context_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('is_paused', sa.Boolean(), server_default='false'),
        sa.Column('pause_reason', sa.Text(), nullable=True),
        sa.Column('paused_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('user_context', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['assigned_to_agent_id'], ['agents.agent_id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE'),
    )

    # Update agent_status with task foreignkey
    op.create_foreign_key(None, 'agent_status', 'tasks', ['current_task_id'], ['task_id'])

    # messages table
    op.create_table(
        'messages',
        sa.Column('message_id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
        sa.Column('from_agent_id', sa.String(100), nullable=False),
        sa.Column('to_agent_id', sa.String(100), nullable=True),
        sa.Column('channel', sa.String(100), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('message_type', sa.Enum('info', 'request', 'approval', 'alert', name='messagetype'), nullable=True),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'critical', name='priority'), server_default='medium'),
        sa.Column('read_status', sa.Boolean(), server_default='false'),
        sa.Column('related_task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('timestamp', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('meta_data', postgresql.JSONB(), server_default='{}'),
        sa.ForeignKeyConstraint(['from_agent_id'], ['agents.agent_id']),
        sa.ForeignKeyConstraint(['to_agent_id'], ['agents.agent_id']),
        sa.ForeignKeyConstraint(['related_task_id'], ['tasks.task_id']),
        sa.ForeignKeyConstraint(['related_project_id'], ['projects.project_id']),
    )

    # decisions table
    op.create_table(
        'decisions',
        sa.Column('decision_id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('made_by_agent_id', sa.String(100), nullable=False),
        sa.Column('decision_type', sa.String(50), nullable=False),
        sa.Column('decision_category', sa.String(50), nullable=True),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('rationale', sa.Text(), nullable=False),
        sa.Column('decision', sa.Text(), nullable=False),
        sa.Column('approved', sa.Boolean(), nullable=True),
        sa.Column('approved_by', sa.String(100), nullable=True),
        sa.Column('timestamp', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('meta_data', postgresql.JSONB(), server_default='{}'),
        sa.Column('embedding_id', sa.String(255), nullable=True),
        sa.Column('rag_indexed_at', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['made_by_agent_id'], ['agents.agent_id']),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id']),
        sa.ForeignKeyConstraint(['task_id'], ['tasks.task_id']),
    )

    # knowledge_base table
    op.create_table(
        'knowledge_base',
        sa.Column('document_id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
        sa.Column('category', sa.String(100), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_by_agent_id', sa.String(100), nullable=False),
        sa.Column('access_level', sa.String(50), server_default='public'),
        sa.Column('version', sa.Integer(), server_default='1'),
        sa.Column('tags', postgresql.JSONB(), server_default='[]'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('last_updated', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('meta_data', postgresql.JSONB(), server_default='{}'),
        sa.ForeignKeyConstraint(['created_by_agent_id'], ['agents.agent_id']),
    )

    # escalations table
    op.create_table(
        'escalations',
        sa.Column('escalation_id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
        sa.Column('issue_type', sa.String(50), nullable=False),
        sa.Column('severity', sa.Enum('low', 'medium', 'high', 'critical', name='priority'), nullable=False),
        sa.Column('escalated_by_agent_id', sa.String(100), nullable=False),
        sa.Column('escalated_to_agent_id', sa.String(100), nullable=False),
        sa.Column('related_task_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('related_project_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('resolution', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), server_default='open'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('resolved_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('meta_data', postgresql.JSONB(), server_default='{}'),
        sa.Column('embedding_id', sa.String(255), nullable=True),
        sa.Column('rag_indexed_at', sa.TIMESTAMP(), nullable=True),
        sa.ForeignKeyConstraint(['escalated_by_agent_id'], ['agents.agent_id']),
        sa.ForeignKeyConstraint(['escalated_to_agent_id'], ['agents.agent_id']),
        sa.ForeignKeyConstraint(['related_task_id'], ['tasks.task_id']),
        sa.ForeignKeyConstraint(['related_project_id'], ['projects.project_id']),
    )

    # audit_log table
    op.create_table(
        'audit_log',
        sa.Column('log_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('agent_id', sa.String(100), nullable=True),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(50), nullable=True),
        sa.Column('entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('old_value', postgresql.JSONB(), nullable=True),
        sa.Column('new_value', postgresql.JSONB(), nullable=True),
        sa.Column('timestamp', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('meta_data', postgresql.JSONB(), server_default='{}'),
    )

    # human_interactions table
    op.create_table(
        'human_interactions',
        sa.Column('interaction_id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
        sa.Column('initiated_by_agent_id', sa.String(100), nullable=False),
        sa.Column('interaction_type', sa.String(50), nullable=False),
        sa.Column('related_entity_type', sa.String(50), nullable=True),
        sa.Column('related_entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('request', sa.Text(), nullable=False),
        sa.Column('human_response', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('responded_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('meta_data', postgresql.JSONB(), server_default='{}'),
        sa.ForeignKeyConstraint(['initiated_by_agent_id'], ['agents.agent_id']),
    )

    # notifications table
    op.create_table(
        'notifications',
        sa.Column('notification_id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
        sa.Column('type', sa.Enum('human_intervention_required', 'ceo_feedback', 'project_completed', 'project_failed', 'task_blocked', 'escalation', 'general', name='notificationtype'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('message', sa.Text(), nullable=False),
        sa.Column('related_entity_type', sa.String(50), nullable=True),
        sa.Column('related_entity_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('agent_id', sa.String(100), nullable=True),
        sa.Column('priority', sa.Enum('low', 'medium', 'high', 'critical', name='priority'), server_default='medium'),
        sa.Column('read', sa.Boolean(), server_default='false'),
        sa.Column('read_at', sa.TIMESTAMP(), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('meta_data', postgresql.JSONB(), server_default='{}'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.agent_id']),
    )

    # system_settings table
    op.create_table(
        'system_settings',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('default_llm_model', sa.String(100), server_default='claude-3-5-sonnet-20241022'),
        sa.Column('llm_temperature', sa.Integer(), server_default='70'),
        sa.Column('llm_max_tokens', sa.Integer(), server_default='4096'),
        sa.Column('show_thinking_process', sa.Boolean(), server_default='true'),
        sa.Column('context_strategy', sa.String(50), server_default='full_history'),
        sa.Column('default_communication_style', sa.String(50), server_default='professional'),
        sa.Column('escalation_time_threshold', sa.Integer(), server_default='60'),
        sa.Column('auto_retry_attempts', sa.Integer(), server_default='3'),
        sa.Column('agent_autonomy_level', sa.String(50), server_default='medium'),
        sa.Column('request_caching_enabled', sa.Boolean(), server_default='true'),
        sa.Column('concurrent_agent_limit', sa.Integer(), server_default='10'),
        sa.Column('auto_scaling_enabled', sa.Boolean(), server_default='false'),
        sa.Column('log_level', sa.String(20), server_default='INFO'),
        sa.Column('debug_mode', sa.Boolean(), server_default='false'),
        sa.Column('auto_backup_enabled', sa.Boolean(), server_default='true'),
        sa.Column('backup_frequency', sa.String(20), server_default='daily'),
        sa.Column('advanced_settings', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('updated_by', sa.String(100), nullable=True),
    )

    # user_profiles table
    op.create_table(
        'user_profiles',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.func.gen_random_uuid()),
        sa.Column('full_name', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(100), nullable=True),
        sa.Column('email', sa.String(255), unique=True, nullable=False),
        sa.Column('phone', sa.String(50), nullable=True),
        sa.Column('job_title', sa.String(100), nullable=True),
        sa.Column('department', sa.String(100), nullable=True),
        sa.Column('location', sa.String(255), nullable=True),
        sa.Column('bio', sa.Text(), nullable=True),
        sa.Column('avatar_url', sa.String(500), nullable=True),
        sa.Column('pronouns', sa.String(50), nullable=True),
        sa.Column('timezone', sa.String(100), server_default='UTC'),
        sa.Column('theme', sa.String(20), server_default='dark'),
        sa.Column('display_density', sa.String(20), server_default='comfortable'),
        sa.Column('font_size', sa.Integer(), server_default='14'),
        sa.Column('language', sa.String(10), server_default='en'),
        sa.Column('animations_enabled', sa.Boolean(), server_default='true'),
        sa.Column('sidebar_collapsed', sa.Boolean(), server_default='false'),
        sa.Column('default_landing_page', sa.String(50), server_default='dashboard'),
        sa.Column('email_notifications', sa.String(20), server_default='realtime'),
        sa.Column('desktop_notifications', sa.Boolean(), server_default='true'),
        sa.Column('notification_sounds', sa.Boolean(), server_default='true'),
        sa.Column('notification_preferences', postgresql.JSONB(), server_default='{}'),
        sa.Column('show_online_status', sa.Boolean(), server_default='true'),
        sa.Column('show_last_active', sa.Boolean(), server_default='true'),
        sa.Column('show_email_in_directory', sa.Boolean(), server_default='false'),
        sa.Column('activity_broadcasting', sa.Boolean(), server_default='true'),
        sa.Column('work_start_time', sa.String(10), server_default='09:00'),
        sa.Column('work_end_time', sa.String(10), server_default='17:00'),
        sa.Column('default_task_view', sa.String(20), server_default='list'),
        sa.Column('availability_status', sa.String(20), server_default='available'),
        sa.Column('connected_accounts', postgresql.JSONB(), server_default='{}'),
        sa.Column('role', sa.String(50), server_default='member'),
        sa.Column('is_admin', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('last_login', sa.TIMESTAMP(), nullable=True),
        sa.Column('meta_data', postgresql.JSONB(), server_default='{}'),
    )

    # settings_audit_log table
    op.create_table(
        'settings_audit_log',
        sa.Column('log_id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('entity_type', sa.String(50), nullable=False),
        sa.Column('entity_id', sa.String(100), nullable=True),
        sa.Column('changed_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('changed_by_admin', sa.Boolean(), server_default='false'),
        sa.Column('field_name', sa.String(100), nullable=False),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('change_reason', sa.Text(), nullable=True),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('timestamp', sa.TIMESTAMP(), server_default=sa.func.now()),
        sa.Column('meta_data', postgresql.JSONB(), server_default='{}'),
    )

    # Create indexes for performance
    op.create_index('ix_projects_status', 'projects', ['status'])
    op.create_index('ix_projects_owner_agent_id', 'projects', ['owner_agent_id'])
    op.create_index('ix_tasks_project_id', 'tasks', ['project_id'])
    op.create_index('ix_tasks_assigned_to_agent_id', 'tasks', ['assigned_to_agent_id'])
    op.create_index('ix_tasks_status', 'tasks', ['status'])
    op.create_index('ix_messages_from_agent_id', 'messages', ['from_agent_id'])
    op.create_index('ix_messages_to_agent_id', 'messages', ['to_agent_id'])
    op.create_index('ix_decisions_made_by_agent_id', 'decisions', ['made_by_agent_id'])
    op.create_index('ix_decisions_project_id', 'decisions', ['project_id'])
    op.create_index('ix_audit_log_agent_id', 'audit_log', ['agent_id'])
    op.create_index('ix_audit_log_timestamp', 'audit_log', ['timestamp'])
    op.create_index('ix_notifications_agent_id', 'notifications', ['agent_id'])
    op.create_index('ix_user_profiles_email', 'user_profiles', ['email'], unique=True)


def downgrade() -> None:
    """Drop all tables and enum types."""
    # Drop indexes
    op.drop_index('ix_user_profiles_email', table_name='user_profiles')
    op.drop_index('ix_notifications_agent_id', table_name='notifications')
    op.drop_index('ix_audit_log_timestamp', table_name='audit_log')
    op.drop_index('ix_audit_log_agent_id', table_name='audit_log')
    op.drop_index('ix_decisions_project_id', table_name='decisions')
    op.drop_index('ix_decisions_made_by_agent_id', table_name='decisions')
    op.drop_index('ix_messages_to_agent_id', table_name='messages')
    op.drop_index('ix_messages_from_agent_id', table_name='messages')
    op.drop_index('ix_tasks_status', table_name='tasks')
    op.drop_index('ix_tasks_assigned_to_agent_id', table_name='tasks')
    op.drop_index('ix_tasks_project_id', table_name='tasks')
    op.drop_index('ix_projects_owner_agent_id', table_name='projects')
    op.drop_index('ix_projects_status', table_name='projects')

    # Drop tables in reverse order
    op.drop_table('settings_audit_log')
    op.drop_table('user_profiles')
    op.drop_table('system_settings')
    op.drop_table('notifications')
    op.drop_table('human_interactions')
    op.drop_table('audit_log')
    op.drop_table('escalations')
    op.drop_table('knowledge_base')
    op.drop_table('decisions')
    op.drop_table('messages')
    op.drop_table('tasks')
    op.drop_table('agent_status')
    op.drop_table('projects')
    op.drop_table('agents')

    # Drop enum types
    sa.Enum('availability').drop(op.get_bind(), checkfirst=True)
    sa.Enum('projectstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum('priority').drop(op.get_bind(), checkfirst=True)
    sa.Enum('taskstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum('messagetype').drop(op.get_bind(), checkfirst=True)
    sa.Enum('taskragstatus').drop(op.get_bind(), checkfirst=True)
    sa.Enum('notificationtype').drop(op.get_bind(), checkfirst=True)
