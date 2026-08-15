"""Add multi-department support for agents

Revision ID: 008_add_multi_department_support
Revises: 007_add_context_intelligence
Create Date: 2025-11-26

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '008_add_multi_department_support'
down_revision = '007_add_context_intelligence'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    Add support for agents to belong to multiple departments.

    Changes:
    1. Add 'departments' JSONB column to agents table (array of department strings)
    2. Keep 'department' column for backwards compatibility
    3. Migrate existing single department to departments array
    """

    # Add new departments column
    op.add_column(
        'agents',
        sa.Column('departments', JSONB, nullable=True)
    )

    # Migrate existing department data to departments array
    # This SQL will convert the single department string to a JSON array
    op.execute("""
        UPDATE agents
        SET departments = jsonb_build_array(department)
        WHERE department IS NOT NULL
    """)

    # Make departments column non-nullable now that data is migrated
    op.alter_column('agents', 'departments', nullable=False, server_default='["unknown"]')

    # Add comment to clarify the schema
    op.execute("""
        COMMENT ON COLUMN agents.departments IS
        'Array of department names this agent belongs to. First department is considered primary.';
    """)

    op.execute("""
        COMMENT ON COLUMN agents.department IS
        'Legacy single department field. Kept for backwards compatibility. Use departments array instead.';
    """)


def downgrade() -> None:
    """
    Remove multi-department support and revert to single department.

    WARNING: If an agent belongs to multiple departments, only the first
    department will be preserved during downgrade.
    """

    # Remove the departments column
    op.drop_column('agents', 'departments')
