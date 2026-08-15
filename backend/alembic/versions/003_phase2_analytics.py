"""Add Phase 2 analytics and learning system support.

This migration adds support for advanced analytics, agent learning, and
audit logging to enable performance tracking and optimization.

Changes:
- Add task_templates table
- Add agent_performance_metrics table
- Add agent_skill_progression table
- Add project_metrics table
- Add audit_logs table
- Add workflow_instances table

Revision ID: 004_phase2_analytics
Revises: 003_business_ops
Create Date: 2025-11-23 15:00:00.000000

This migration is NON-BREAKING - all changes are additive with defaults
to preserve existing data and ensure backward compatibility.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_phase2_analytics'
down_revision: Union[str, Sequence[str], None] = '003_business_ops'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema for Phase 2 analytics support."""

    # ===== CREATE NEW TABLES FOR PHASE 2 =====

    # 1. Task templates table
    op.create_table(
        'task_templates',
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('project_type', sa.String(100), nullable=False),
        sa.Column('breakdown_instructions', sa.Text(), nullable=False),
        sa.Column('estimated_duration_hours', sa.Integer(), nullable=True),
        sa.Column('typical_subtasks', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('required_skills', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('created_by', sa.String(100), sa.ForeignKey('agents.agent_id'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('template_id')
    )

    # 2. Agent performance metrics table
    op.create_table(
        'agent_performance_metrics',
        sa.Column('metric_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(100), sa.ForeignKey('agents.agent_id', ondelete='CASCADE'), nullable=False),
        sa.Column('task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tasks.task_id', ondelete='CASCADE'), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.project_id', ondelete='CASCADE'), nullable=True),
        sa.Column('quality_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('speed_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('reliability_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('overall_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('actual_duration_hours', sa.Integer(), nullable=True),
        sa.Column('estimated_duration_hours', sa.Integer(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('recorded_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('metric_id')
    )

    # 3. Agent skill progression table
    op.create_table(
        'agent_skill_progression',
        sa.Column('progression_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(100), sa.ForeignKey('agents.agent_id', ondelete='CASCADE'), nullable=False),
        sa.Column('skill_name', sa.String(100), nullable=False),
        sa.Column('proficiency_level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('tasks_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_used', sa.TIMESTAMP(), nullable=True),
        sa.Column('updated_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('progression_id')
    )

    # 4. Project metrics table
    op.create_table(
        'project_metrics',
        sa.Column('metric_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.project_id', ondelete='CASCADE'), nullable=False),
        sa.Column('planned_completion_date', sa.TIMESTAMP(), nullable=True),
        sa.Column('actual_completion_date', sa.TIMESTAMP(), nullable=True),
        sa.Column('timeline_variance_percent', sa.Integer(), nullable=True),
        sa.Column('total_tasks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_tasks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('blocked_tasks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('failed_tasks', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completion_rate', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('quality_score', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('rework_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('approval_rate', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('total_agent_hours', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_team_utilization', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('last_updated', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('metric_id')
    )

    # 5. Audit logs table
    op.create_table(
        'audit_logs',
        sa.Column('log_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('entity_type', sa.String(100), nullable=False),
        sa.Column('entity_id', sa.String(200), nullable=False),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('actor', sa.String(100), nullable=False),
        sa.Column('old_value', postgresql.JSONB(), nullable=True),
        sa.Column('new_value', postgresql.JSONB(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('details', postgresql.JSONB(), nullable=True),
        sa.Column('timestamp', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('ip_address', sa.String(50), nullable=True),
        sa.PrimaryKeyConstraint('log_id')
    )

    # 6. Workflow instances table
    op.create_table(
        'workflow_instances',
        sa.Column('workflow_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.project_id', ondelete='CASCADE'), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('task_templates.template_id'), nullable=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('parent_task_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('tasks.task_id', ondelete='SET NULL'), nullable=True),
        sa.Column('subtasks', postgresql.JSONB(), nullable=False, server_default='[]'),
        sa.Column('created_by', sa.String(100), sa.ForeignKey('agents.agent_id'), nullable=True),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=False, server_default=sa.func.now()),
        sa.Column('completed_at', sa.TIMESTAMP(), nullable=True),
        sa.PrimaryKeyConstraint('workflow_id')
    )

    # ===== CREATE INDEXES =====

    op.create_index('idx_agent_performance_agent_id', 'agent_performance_metrics', ['agent_id'])
    op.create_index('idx_agent_performance_task_id', 'agent_performance_metrics', ['task_id'])
    op.create_index('idx_agent_performance_project_id', 'agent_performance_metrics', ['project_id'])
    op.create_index('idx_agent_skill_progression_agent_id', 'agent_skill_progression', ['agent_id'])
    op.create_index('idx_project_metrics_project_id', 'project_metrics', ['project_id'])
    op.create_index('idx_audit_logs_entity', 'audit_logs', ['entity_type', 'entity_id'])
    op.create_index('idx_audit_logs_timestamp', 'audit_logs', ['timestamp'])
    op.create_index('idx_workflow_instances_project_id', 'workflow_instances', ['project_id'])
    op.create_index('idx_task_templates_project_type', 'task_templates', ['project_type'])


def downgrade() -> None:
    """Downgrade database schema - remove Phase 2 analytics support."""

    # Drop indexes
    op.drop_index('idx_task_templates_project_type')
    op.drop_index('idx_workflow_instances_project_id')
    op.drop_index('idx_audit_logs_timestamp')
    op.drop_index('idx_audit_logs_entity')
    op.drop_index('idx_project_metrics_project_id')
    op.drop_index('idx_agent_skill_progression_agent_id')
    op.drop_index('idx_agent_performance_project_id')
    op.drop_index('idx_agent_performance_task_id')
    op.drop_index('idx_agent_performance_agent_id')

    # Drop tables
    op.drop_table('workflow_instances')
    op.drop_table('audit_logs')
    op.drop_table('project_metrics')
    op.drop_table('agent_skill_progression')
    op.drop_table('agent_performance_metrics')
    op.drop_table('task_templates')
