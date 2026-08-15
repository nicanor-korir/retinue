"""Add business operations support to AgentGo.

This migration adds support for flexible agent management and diverse
project types, enabling the platform to handle multiple business functions
beyond software development.

Changes:
- Add departments table
- Add deliverable_types table
- Add project_agent_assignments table
- Update agents table with new columns
- Update projects table with new columns
- Update tasks table with new columns
- Populate reference data

Revision ID: 003_business_ops
Revises: eda90ddfb844
Create Date: 2025-11-22 21:30:00.000000

This migration is NON-BREAKING - all changes have defaults to preserve
existing data and ensure backward compatibility.
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '003_business_ops'
down_revision: Union[str, Sequence[str], None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade database schema for business operations support."""

    # ===== CREATE NEW TABLES =====

    # 1. Departments table
    op.create_table(
        'departments',
        sa.Column('department_id', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('icon', sa.String(50), nullable=True),
        sa.Column('color', sa.String(20), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('department_id', name='departments_pkey'),
        sa.Index('idx_department_active', 'is_active'),
    )

    # 2. Deliverable Types table
    op.create_table(
        'deliverable_types',
        sa.Column('type_id', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('typical_agents', postgresql.JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column('output_format', sa.String(50), nullable=True),
        sa.Column('template_path', sa.String(500), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('created_at', sa.TIMESTAMP(), nullable=True, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('type_id', name='deliverable_types_pkey'),
        sa.Index('idx_deliverable_active', 'is_active'),
    )

    # 3. Project Agent Assignments table
    op.create_table(
        'project_agent_assignments',
        sa.Column('assignment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('agent_id', sa.String(100), nullable=False),
        sa.Column('role_in_project', sa.String(100), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('assigned_at', sa.TIMESTAMP(), nullable=True, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.project_id'], ondelete='CASCADE', name='project_agent_assignments_project_id_fkey'),
        sa.ForeignKeyConstraint(['agent_id'], ['agents.agent_id'], ondelete='CASCADE', name='project_agent_assignments_agent_id_fkey'),
        sa.PrimaryKeyConstraint('assignment_id', name='project_agent_assignments_pkey'),
        sa.UniqueConstraint('project_id', 'agent_id', name='uq_project_agent'),
        sa.Index('idx_project_agents', 'project_id'),
        sa.Index('idx_agent_projects', 'agent_id'),
    )

    # ===== ADD COLUMNS TO EXISTING TABLES =====

    # 4. Update agents table
    op.add_column('agents', sa.Column(
        'output_types',
        postgresql.JSONB(),
        nullable=False,
        server_default=sa.text("'[\"text\"]'::jsonb")
    ))
    op.add_column('agents', sa.Column(
        'specializations',
        postgresql.JSONB(),
        nullable=False,
        server_default=sa.text("'[]'::jsonb")
    ))
    op.add_column('agents', sa.Column(
        'required_for_types',
        postgresql.JSONB(),
        nullable=False,
        server_default=sa.text("'[]'::jsonb")
    ))

    # 5. Update projects table
    op.add_column('projects', sa.Column(
        'project_type',
        sa.String(50),
        nullable=False,
        server_default='custom'
    ))
    op.add_column('projects', sa.Column(
        'deliverable_type',
        sa.String(50),
        nullable=True
    ))
    op.add_column('projects', sa.Column(
        'selected_agents',
        postgresql.JSONB(),
        nullable=False,
        server_default=sa.text("'[]'::jsonb")
    ))

    # Add foreign key for deliverable_type
    op.create_foreign_key(
        'projects_deliverable_type_fkey',
        'projects',
        'deliverable_types',
        ['deliverable_type'],
        ['type_id']
    )

    # 6. Update tasks table
    op.add_column('tasks', sa.Column(
        'output_format',
        sa.String(50),
        nullable=False,
        server_default='text'
    ))
    op.add_column('tasks', sa.Column(
        'output_metadata',
        postgresql.JSONB(),
        nullable=False,
        server_default=sa.text("'{}'::jsonb")
    ))

    # ===== POPULATE REFERENCE DATA =====

    # 7. Insert departments
    op.execute("""
    INSERT INTO departments (department_id, name, description, icon, color, is_active) VALUES
    ('executive', 'Executive Leadership', 'C-suite strategic decision making', 'briefcase', '#8B4513', true),
    ('engineering', 'Engineering', 'Software development and technical solutions', 'code', '#2563EB', true),
    ('marketing', 'Marketing & Growth', 'Marketing campaigns and growth strategies', 'megaphone', '#DC2626', true),
    ('sales', 'Sales & Business Development', 'Revenue generation and client acquisition', 'dollar-sign', '#059669', true),
    ('finance', 'Finance & Accounting', 'Financial analysis and planning', 'chart-line', '#7C3AED', true),
    ('hr', 'Human Resources', 'People operations and talent management', 'users', '#EA580C', true),
    ('operations', 'Operations', 'Business operations and efficiency', 'settings', '#64748B', true),
    ('legal', 'Legal & Compliance', 'Legal advice and compliance', 'scale', '#6B7280', true),
    ('research', 'Research & Analytics', 'Data analysis and market research', 'search', '#14B8A6', true);
    """)

    # 8. Insert deliverable types
    op.execute("""
    INSERT INTO deliverable_types (type_id, name, description, typical_agents, output_format, is_active) VALUES
    ('software_mvp', 'Software MVP', 'Full stack application with code',
     '["ceo_001", "cto_001", "pm_001", "backend_001", "frontend_001", "designer_001"]'::jsonb, 'code', true),
    ('marketing_campaign', 'Marketing Campaign', 'Complete marketing campaign with assets',
     '["ceo_001", "cmo_001", "content_001", "designer_001", "social_media_001"]'::jsonb, 'pdf', true),
    ('financial_analysis', 'Financial Analysis Report', 'Financial projections and analysis',
     '["ceo_001", "cfo_001", "financial_analyst_001"]'::jsonb, 'xlsx', true),
    ('business_proposal', 'Business Proposal', 'Professional business proposal',
     '["ceo_001", "sales_manager_001", "designer_001"]'::jsonb, 'pdf', true),
    ('hr_policy', 'HR Policy Document', 'Company policy documentation',
     '["ceo_001", "chro_001", "hr_specialist_001", "legal_001"]'::jsonb, 'docx', true),
    ('market_research', 'Market Research Report', 'Comprehensive market analysis',
     '["ceo_001", "research_001", "data_analyst_001"]'::jsonb, 'pdf', true),
    ('api_development', 'API Development', 'RESTful API with documentation',
     '["ceo_001", "cto_001", "pm_001", "backend_001"]'::jsonb, 'code', true),
    ('brand_strategy', 'Brand Strategy', 'Comprehensive brand positioning',
     '["ceo_001", "cmo_001", "designer_001"]'::jsonb, 'pdf', true),
    ('budget_planning', 'Budget Planning', 'Annual budget and allocation',
     '["ceo_001", "cfo_001"]'::jsonb, 'xlsx', true),
    ('sales_strategy', 'Sales Strategy', 'Sales playbook and strategy',
     '["ceo_001", "sales_manager_001", "cfo_001"]'::jsonb, 'pdf', true);
    """)

    # 9. Update existing projects to have new column values
    # Set existing projects to legacy software MVP project type
    op.execute("""
    UPDATE projects SET
        project_type = 'software_mvp',
        deliverable_type = 'software_mvp',
        selected_agents = '["ceo_001", "cto_001", "pm_001", "hr_monitor_001", "backend_001", "frontend_001", "designer_001"]'::jsonb
    WHERE project_type IS NULL AND deleted_at IS NULL;
    """)

    # ===== CREATE INDEXES FOR PERFORMANCE =====

    # 10. Indexes for project_agent_assignments
    op.create_index('idx_project_agent_assignments_active', 'project_agent_assignments', ['is_active'])
    op.create_index('idx_project_agent_assignments_assigned', 'project_agent_assignments', ['assigned_at'])

    # 11. Indexes for improved query performance
    op.create_index('idx_projects_project_type', 'projects', ['project_type'])
    op.create_index('idx_projects_deliverable_type', 'projects', ['deliverable_type'])
    op.create_index('idx_tasks_output_format', 'tasks', ['output_format'])


def downgrade() -> None:
    """Downgrade database schema - reverse business operations changes."""

    # ===== DROP INDEXES =====
    op.drop_index('idx_project_agent_assignments_assigned', table_name='project_agent_assignments')
    op.drop_index('idx_project_agent_assignments_active', table_name='project_agent_assignments')
    op.drop_index('idx_tasks_output_format', table_name='tasks')
    op.drop_index('idx_projects_deliverable_type', table_name='projects')
    op.drop_index('idx_projects_project_type', table_name='projects')

    # ===== DROP FOREIGN KEYS AND COLUMNS FROM EXISTING TABLES =====

    # Drop foreign key from projects to deliverable_types
    op.drop_constraint('projects_deliverable_type_fkey', 'projects', type_='foreignkey')

    # Drop columns from tasks
    op.drop_column('tasks', 'output_metadata')
    op.drop_column('tasks', 'output_format')

    # Drop columns from projects
    op.drop_column('projects', 'selected_agents')
    op.drop_column('projects', 'deliverable_type')
    op.drop_column('projects', 'project_type')

    # Drop columns from agents
    op.drop_column('agents', 'required_for_types')
    op.drop_column('agents', 'specializations')
    op.drop_column('agents', 'output_types')

    # ===== DROP NEW TABLES =====

    # Drop project_agent_assignments
    op.drop_table('project_agent_assignments')

    # Drop deliverable_types
    op.drop_table('deliverable_types')

    # Drop departments
    op.drop_table('departments')
