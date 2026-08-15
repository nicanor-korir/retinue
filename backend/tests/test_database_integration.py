"""Integration tests for database operations and Phase 0 models.

Tests for:
- Database schema changes
- New models (Department, DeliverableType, ProjectAgentAssignment)
- Updated models (Agent, Project, Task)
- Data migration compatibility
- Backward compatibility
"""

import pytest
import uuid
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import engine, get_session
from app.db.models import (
    Department, DeliverableType, ProjectAgentAssignment,
    Agent, Project, Task, ProjectStatus, TaskStatus, Priority, Availability, AgentStatus
)
from app.agents.agent_registry import AgentRegistry


@pytest.mark.asyncio
class TestDatabaseModels:
    """Tests for new Phase 0 database models."""

    async def test_department_model_creation(self):
        """Test that Department model can be created and saved."""
        async for session in get_session():
            dept = Department(
                department_id='test_dept',
                name='Test Department',
                description='A test department',
                icon='test-icon',
                color='#FF0000',
                is_active=True
            )
            session.add(dept)
            await session.commit()

            # Verify it was saved
            result = await session.execute(
                select(Department).where(Department.department_id == 'test_dept')
            )
            saved_dept = result.scalar_one()
            assert saved_dept.name == 'Test Department'

            # Cleanup
            await session.delete(saved_dept)
            await session.commit()

    async def test_deliverable_type_model_creation(self):
        """Test that DeliverableType model can be created and saved."""
        async for session in get_session():
            dt = DeliverableType(
                type_id='test_type',
                name='Test Deliverable Type',
                description='A test deliverable type',
                typical_agents=['agent1', 'agent2'],
                output_format='pdf',
                is_active=True
            )
            session.add(dt)
            await session.commit()

            # Verify it was saved
            result = await session.execute(
                select(DeliverableType).where(DeliverableType.type_id == 'test_type')
            )
            saved_dt = result.scalar_one()
            assert saved_dt.name == 'Test Deliverable Type'
            assert saved_dt.output_format == 'pdf'

            # Cleanup
            await session.delete(saved_dt)
            await session.commit()

    async def test_project_agent_assignment_model_creation(self):
        """Test that ProjectAgentAssignment model can be created."""
        async for session in get_session():
            # First create a project and agent (simplified - assumes they exist)
            # In real tests, these would be fixtures

            assignment = ProjectAgentAssignment(
                assignment_id=uuid.uuid4(),
                project_id=uuid.uuid4(),
                agent_id='test_agent',
                role_in_project='lead',
                is_active=True
            )
            session.add(assignment)
            await session.commit()

            # Verify it was saved
            result = await session.execute(
                select(ProjectAgentAssignment).where(
                    ProjectAgentAssignment.agent_id == 'test_agent'
                )
            )
            saved_assignment = result.scalar_one()
            assert saved_assignment.role_in_project == 'lead'

            # Cleanup
            await session.delete(saved_assignment)
            await session.commit()


@pytest.mark.asyncio
class TestUpdatedModels:
    """Tests for updated Phase 0 columns in existing models."""

    async def test_agent_has_new_columns(self):
        """Test that Agent model has new Phase 0 columns."""
        async for session in get_session():
            # Check that Agent table has the new columns
            result = await session.execute(
                select(func.count()).select_from(Agent)
            )
            count = result.scalar()

            if count > 0:
                # Get an existing agent to verify columns exist
                agent = await session.execute(select(Agent).limit(1))
                agent = agent.scalar_one_or_none()

                if agent:
                    # Verify new columns exist and have defaults
                    assert hasattr(agent, 'output_types')
                    assert hasattr(agent, 'specializations')
                    assert hasattr(agent, 'required_for_types')
                    assert isinstance(agent.output_types, (list, type(None)))
                    assert isinstance(agent.specializations, (list, type(None)))
                    assert isinstance(agent.required_for_types, (list, type(None)))

    async def test_project_has_new_columns(self):
        """Test that Project model has new Phase 0 columns."""
        async for session in get_session():
            result = await session.execute(
                select(func.count()).select_from(Project)
            )
            count = result.scalar()

            if count > 0:
                # Get an existing project to verify columns exist
                project = await session.execute(select(Project).limit(1))
                project = project.scalar_one_or_none()

                if project:
                    # Verify new columns exist
                    assert hasattr(project, 'project_type')
                    assert hasattr(project, 'deliverable_type')
                    assert hasattr(project, 'selected_agents')
                    # Check defaults
                    assert project.project_type is not None
                    assert isinstance(project.selected_agents, (list, type(None)))

    async def test_task_has_new_columns(self):
        """Test that Task model has new Phase 0 columns."""
        async for session in get_session():
            result = await session.execute(
                select(func.count()).select_from(Task)
            )
            count = result.scalar()

            if count > 0:
                # Get an existing task to verify columns exist
                task = await session.execute(select(Task).limit(1))
                task = task.scalar_one_or_none()

                if task:
                    # Verify new columns exist
                    assert hasattr(task, 'output_format')
                    assert hasattr(task, 'output_metadata')
                    # Check defaults
                    assert task.output_format is not None
                    assert isinstance(task.output_metadata, (dict, type(None)))


@pytest.mark.asyncio
class TestBackwardCompatibility:
    """Tests to ensure backward compatibility with existing data."""

    async def test_existing_projects_have_defaults(self):
        """Test that existing projects have sensible defaults for new columns."""
        async for session in get_session():
            result = await session.execute(
                select(Project).limit(1)
            )
            project = result.scalar_one_or_none()

            if project:
                # Verify defaults are set
                assert project.project_type is not None
                assert project.project_type == 'custom' or project.project_type == 'software_mvp'
                # selected_agents should be list-like
                if project.selected_agents:
                    assert isinstance(project.selected_agents, (list, str))

    async def test_existing_tasks_have_defaults(self):
        """Test that existing tasks have sensible defaults for new columns."""
        async for session in get_session():
            result = await session.execute(
                select(Task).limit(1)
            )
            task = result.scalar_one_or_none()

            if task:
                # Verify defaults are set
                assert task.output_format is not None
                assert task.output_format in ['text', 'code', 'markdown', 'json', 'pdf', 'docx', 'xlsx']
                # output_metadata should be dict-like or None
                if task.output_metadata:
                    assert isinstance(task.output_metadata, (dict, str))

    async def test_existing_agents_maintain_data(self):
        """Test that existing agents maintain their original data."""
        async for session in get_session():
            # Check for original 7 agents
            original_agents = [
                'ceo_001', 'cto_001', 'pm_001', 'hr_monitor_001',
                'backend_001', 'frontend_001', 'designer_001'
            ]

            for agent_id in original_agents:
                result = await session.execute(
                    select(Agent).where(Agent.agent_id == agent_id)
                )
                agent = result.scalar_one_or_none()

                if agent:
                    # Original data should be intact
                    assert agent.name is not None
                    assert agent.role is not None
                    assert agent.department is not None
                    # New columns should exist
                    assert hasattr(agent, 'output_types')
                    assert hasattr(agent, 'specializations')


@pytest.mark.asyncio
class TestDataIntegrity:
    """Tests for data integrity and constraints."""

    async def test_project_agent_assignment_uniqueness(self):
        """Test that project-agent combination is unique."""
        async for session in get_session():
            project_id = uuid.uuid4()
            agent_id = 'test_agent_123'

            # Create first assignment
            assignment1 = ProjectAgentAssignment(
                assignment_id=uuid.uuid4(),
                project_id=project_id,
                agent_id=agent_id,
                role_in_project='lead'
            )
            session.add(assignment1)
            await session.commit()

            # Try to create duplicate assignment
            assignment2 = ProjectAgentAssignment(
                assignment_id=uuid.uuid4(),
                project_id=project_id,
                agent_id=agent_id,
                role_in_project='contributor'
            )
            session.add(assignment2)

            # This should raise an integrity error
            with pytest.raises(Exception):  # SQLAlchemy will raise IntegrityError
                await session.commit()

            # Cleanup
            await session.rollback()

    async def test_project_foreign_key_to_deliverable_type(self):
        """Test that project deliverable_type foreign key works."""
        async for session in get_session():
            # Create a deliverable type
            dt = DeliverableType(
                type_id='test_fk_type',
                name='Test FK Type',
                output_format='pdf'
            )
            session.add(dt)
            await session.commit()

            # Project with valid deliverable_type should work
            project = Project(
                project_id=uuid.uuid4(),
                name='Test Project',
                status=ProjectStatus.PLANNING,
                priority=Priority.MEDIUM,
                owner_agent_id='ceo_001',
                deliverable_type='test_fk_type'
            )
            session.add(project)
            await session.commit()

            # Verify it was saved
            result = await session.execute(
                select(Project).where(Project.project_id == project.project_id)
            )
            saved_project = result.scalar_one()
            assert saved_project.deliverable_type == 'test_fk_type'

            # Cleanup
            await session.delete(saved_project)
            await session.delete(dt)
            await session.commit()


@pytest.mark.asyncio
class TestNewFeatures:
    """Tests for new Phase 0 features enabled by database changes."""

    async def test_project_with_agent_selection(self):
        """Test creating a project with selected agents."""
        async for session in get_session():
            selected_agents = ['ceo_001', 'cto_001', 'backend_001']
            project_id = uuid.uuid4()

            project = Project(
                project_id=project_id,
                name='Multi-Agent Project',
                status=ProjectStatus.PLANNING,
                priority=Priority.HIGH,
                owner_agent_id='ceo_001',
                project_type='software_mvp',
                deliverable_type='software_mvp',
                selected_agents=selected_agents
            )
            session.add(project)
            await session.commit()

            # Verify it was saved with selected agents
            result = await session.execute(
                select(Project).where(Project.project_id == project_id)
            )
            saved = result.scalar_one()
            assert saved.selected_agents == selected_agents
            assert saved.project_type == 'software_mvp'

            # Cleanup
            await session.delete(saved)
            await session.commit()

    async def test_task_with_output_format(self):
        """Test creating a task with specific output format."""
        async for session in get_session():
            project_id = uuid.uuid4()
            task_id = uuid.uuid4()

            task = Task(
                task_id=task_id,
                project_id=project_id,
                assigned_to_agent_id='backend_001',
                title='API Development',
                status=TaskStatus.PENDING,
                output_format='code',
                output_metadata={'language': 'python', 'framework': 'fastapi'}
            )
            session.add(task)
            await session.commit()

            # Verify it was saved with output format
            result = await session.execute(
                select(Task).where(Task.task_id == task_id)
            )
            saved = result.scalar_one()
            assert saved.output_format == 'code'
            assert isinstance(saved.output_metadata, (dict, str))

            # Cleanup
            await session.delete(saved)
            await session.commit()

    async def test_project_agent_assignments(self):
        """Test creating project-agent assignments."""
        async for session in get_session():
            project_id = uuid.uuid4()
            agents = ['ceo_001', 'cmo_001', 'designer_001']

            for agent_id in agents:
                assignment = ProjectAgentAssignment(
                    assignment_id=uuid.uuid4(),
                    project_id=project_id,
                    agent_id=agent_id,
                    role_in_project='team_member'
                )
                session.add(assignment)

            await session.commit()

            # Verify all assignments were saved
            result = await session.execute(
                select(func.count()).select_from(ProjectAgentAssignment).where(
                    ProjectAgentAssignment.project_id == project_id
                )
            )
            count = result.scalar()
            assert count == 3

            # Cleanup
            await session.execute(
                select(ProjectAgentAssignment).where(
                    ProjectAgentAssignment.project_id == project_id
                )
            )
            assignments = await session.execute(
                select(ProjectAgentAssignment).where(
                    ProjectAgentAssignment.project_id == project_id
                )
            )
            for assignment in assignments.scalars():
                await session.delete(assignment)
            await session.commit()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
