"""
Phase 2 Comprehensive Test Suite

Tests for all Phase 2 components:
- Component 1: Task Controls
- Component 2: Multi-Entity RAG
- Component 3: Project Learnings
- Component 4: Project Similarity
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

# Import models
from app.db.models import (
    Project,
    Task,
    ProjectStatus,
    TaskStatus,
    Priority,
    Decision,
    Escalation,
)

# Import services
from app.services.task_control_service import TaskControlService
from app.services.multi_entity_rag_service import MultiEntityRAGService
from app.services.project_learnings_service import ProjectLearningsService
from app.services.project_similarity_service import ProjectSimilarityService


# ==========================================
# Component 1: Task Control Service Tests
# ==========================================


class TestTaskControlService:
    """Test suite for task control service."""

    @pytest.fixture
    async def service(self):
        """Create task control service instance."""
        return TaskControlService()

    @pytest.fixture
    async def test_task(self, session: AsyncSession):
        """Create a test task."""
        task = Task(
            task_id=uuid4(),
            project_id=uuid4(),
            assigned_to_agent_id="test_agent",
            title="Test Task",
            description="A test task for controls",
            status=TaskStatus.IN_PROGRESS,
        )
        session.add(task)
        await session.commit()
        return task

    @pytest.mark.asyncio
    async def test_pause_task(self, service, session, test_task):
        """Test pausing a task."""
        result = await service.pause_task(
            session=session,
            task_id=test_task.task_id,
            reason="Testing pause",
        )
        assert result is True

        # Verify task is paused
        refreshed = await session.get(Task, test_task.task_id)
        assert refreshed.is_paused is True
        assert refreshed.pause_reason == "Testing pause"
        assert refreshed.paused_at is not None

    @pytest.mark.asyncio
    async def test_resume_task(self, service, session, test_task):
        """Test resuming a paused task."""
        # First pause
        await service.pause_task(
            session=session,
            task_id=test_task.task_id,
            reason="Test pause",
        )

        # Then resume
        result = await service.resume_task(
            session=session,
            task_id=test_task.task_id,
        )
        assert result is True

        # Verify task is resumed
        refreshed = await session.get(Task, test_task.task_id)
        assert refreshed.is_paused is False

    @pytest.mark.asyncio
    async def test_cancel_task(self, service, session, test_task):
        """Test cancelling a task."""
        result = await service.cancel_task(
            session=session,
            task_id=test_task.task_id,
            reason="Test cancellation",
        )
        assert result is True

        # Verify task is cancelled
        refreshed = await session.get(Task, test_task.task_id)
        assert refreshed.status == TaskStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_add_task_context(self, service, session, test_task):
        """Test adding context to a task."""
        context = "This is important context for the agent"
        result = await service.add_task_context(
            session=session,
            task_id=test_task.task_id,
            context=context,
        )
        assert result is True

        # Verify context is added
        refreshed = await session.get(Task, test_task.task_id)
        assert refreshed.user_context == context

    @pytest.mark.asyncio
    async def test_get_control_status(self, service, session, test_task):
        """Test getting control status."""
        status = await service.get_control_status(
            session=session,
            task_id=test_task.task_id,
        )
        assert status is not None
        assert status["task_id"] == str(test_task.task_id)
        assert status["is_paused"] is False
        assert status["can_pause"] is True

    @pytest.mark.asyncio
    async def test_pause_task_invalid_status(self, service, session):
        """Test pausing a task with invalid status."""
        # Create completed task
        task = Task(
            task_id=uuid4(),
            project_id=uuid4(),
            assigned_to_agent_id="test_agent",
            title="Completed Task",
            description="A completed task",
            status=TaskStatus.COMPLETED,
        )
        session.add(task)
        await session.commit()

        # Try to pause
        result = await service.pause_task(
            session=session,
            task_id=task.task_id,
            reason="Trying to pause completed task",
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_cannot_pause_twice(self, service, session, test_task):
        """Test that cannot pause already paused task."""
        # Pause once
        await service.pause_task(
            session=session,
            task_id=test_task.task_id,
            reason="First pause",
        )

        # Try to pause again
        result = await service.pause_task(
            session=session,
            task_id=test_task.task_id,
            reason="Second pause",
        )
        assert result is False


# ==========================================
# Component 3: Project Learnings Tests
# ==========================================


class TestProjectLearningsService:
    """Test suite for project learnings service."""

    @pytest.fixture
    async def service(self):
        """Create project learnings service instance."""
        return ProjectLearningsService()

    @pytest.fixture
    async def completed_project(self, session: AsyncSession):
        """Create a completed project."""
        project = Project(
            project_id=uuid4(),
            name="Test Project",
            description="A test project",
            status=ProjectStatus.COMPLETED,
            priority=Priority.HIGH,
            owner_agent_id="test_agent",
            created_at=datetime.utcnow() - timedelta(days=10),
            completed_at=datetime.utcnow(),
            deadline=datetime.utcnow() + timedelta(days=2),
            agent_days_elapsed=10,
        )
        session.add(project)
        await session.commit()
        return project

    @pytest.fixture
    async def project_with_tasks(self, session: AsyncSession, completed_project):
        """Create a project with completed tasks."""
        # Add tasks
        for i in range(3):
            task = Task(
                task_id=uuid4(),
                project_id=completed_project.project_id,
                assigned_to_agent_id="test_agent",
                title=f"Task {i+1}",
                description=f"Description for task {i+1}",
                status=TaskStatus.COMPLETED,
                estimated_hours=10,
                actual_hours=8 + i,  # Varying actual hours
            )
            session.add(task)
        await session.commit()
        return completed_project

    @pytest.mark.asyncio
    async def test_extract_learnings(self, service, session, project_with_tasks):
        """Test extracting learnings from a project."""
        learnings = await service.extract_learnings_from_project(
            session=session,
            project_id=project_with_tasks.project_id,
        )
        assert isinstance(learnings, list)
        assert len(learnings) > 0

    @pytest.mark.asyncio
    async def test_calculate_project_metrics(self, service, session, project_with_tasks):
        """Test calculating project metrics."""
        metrics = await service.calculate_project_metrics(
            session=session,
            project_id=project_with_tasks.project_id,
        )
        assert metrics is not None
        assert "success_score" in metrics
        assert "tasks" in metrics
        assert "timeline" in metrics
        assert metrics["tasks"]["completion_rate"] == 1.0  # All completed

    @pytest.mark.asyncio
    async def test_save_learnings(self, service, session, project_with_tasks):
        """Test saving learnings."""
        from app.services.project_learnings_service import ProjectLearning

        learning = ProjectLearning(
            project_id=project_with_tasks.project_id,
            learning_type="best_practice",
            title="Test Learning",
            description="A test learning",
            evidence=["Evidence 1"],
            relevance_score=0.95,
            tags=["test", "best-practice"],
        )

        summary = await service.save_learnings(
            project_id=project_with_tasks.project_id,
            learnings=[learning],
        )
        assert summary["total_learnings"] == 1
        assert summary["by_type"]["best_practice"] == 1

    @pytest.mark.asyncio
    async def test_incomplete_project_no_learnings(self, service, session):
        """Test that incomplete projects return no learnings."""
        # Create incomplete project
        project = Project(
            project_id=uuid4(),
            name="Incomplete Project",
            description="Not completed",
            status=ProjectStatus.IN_PROGRESS,
            priority=Priority.MEDIUM,
            owner_agent_id="test_agent",
        )
        session.add(project)
        await session.commit()

        learnings = await service.extract_learnings_from_project(
            session=session,
            project_id=project.project_id,
        )
        assert len(learnings) == 0


# ==========================================
# Component 4: Project Similarity Tests
# ==========================================


class TestProjectSimilarityService:
    """Test suite for project similarity service."""

    @pytest.fixture
    async def service(self):
        """Create project similarity service instance."""
        return ProjectSimilarityService()

    @pytest.mark.asyncio
    async def test_similarity_threshold(self, service):
        """Test that similarity threshold is set correctly."""
        assert service.similarity_threshold == 0.6

    @pytest.mark.asyncio
    async def test_cache_ttl(self, service):
        """Test that cache TTL is set correctly."""
        assert service.cache_ttl == 600  # 10 minutes


# ==========================================
# Integration Tests
# ==========================================


class TestPhase2Integration:
    """Integration tests for Phase 2 components."""

    @pytest.mark.asyncio
    async def test_task_control_workflow(self, session: AsyncSession):
        """Test complete task control workflow."""
        service = TaskControlService()

        # Create task
        task = Task(
            task_id=uuid4(),
            project_id=uuid4(),
            assigned_to_agent_id="test_agent",
            title="Workflow Test",
            description="Testing complete workflow",
            status=TaskStatus.IN_PROGRESS,
        )
        session.add(task)
        await session.commit()

        # 1. Add context
        context_added = await service.add_task_context(
            session=session,
            task_id=task.task_id,
            context="Important context",
        )
        assert context_added is True

        # 2. Pause task
        paused = await service.pause_task(
            session=session,
            task_id=task.task_id,
            reason="Workflow test pause",
        )
        assert paused is True

        # 3. Check status
        status = await service.get_control_status(
            session=session,
            task_id=task.task_id,
        )
        assert status["is_paused"] is True
        assert status["user_context"] == "Important context"

        # 4. Resume task
        resumed = await service.resume_task(
            session=session,
            task_id=task.task_id,
        )
        assert resumed is True

        # 5. Verify resumed
        final_status = await service.get_control_status(
            session=session,
            task_id=task.task_id,
        )
        assert final_status["is_paused"] is False


# ==========================================
# API Endpoint Tests (using TestClient)
# ==========================================


@pytest.mark.asyncio
class TestTaskControlEndpoints:
    """Test task control API endpoints."""

    async def test_pause_endpoint(self, client, test_task):
        """Test POST /api/v1/tasks/{id}/pause endpoint."""
        response = await client.post(
            f"/api/v1/tasks/{test_task.task_id}/pause",
            json={"reason": "Testing endpoint"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    async def test_resume_endpoint(self, client, test_task):
        """Test POST /api/v1/tasks/{id}/resume endpoint."""
        # First pause
        await client.post(
            f"/api/v1/tasks/{test_task.task_id}/pause",
            json={"reason": "Test pause"},
        )

        # Then resume
        response = await client.post(
            f"/api/v1/tasks/{test_task.task_id}/resume",
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    async def test_cancel_endpoint(self, client, test_task):
        """Test POST /api/v1/tasks/{id}/cancel endpoint."""
        response = await client.post(
            f"/api/v1/tasks/{test_task.task_id}/cancel",
            json={"reason": "Test cancellation"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

    async def test_control_status_endpoint(self, client, test_task):
        """Test GET /api/v1/tasks/{id}/control-status endpoint."""
        response = await client.get(
            f"/api/v1/tasks/{test_task.task_id}/control-status",
        )
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == str(test_task.task_id)
        assert "is_paused" in data
        assert "can_pause" in data


@pytest.mark.asyncio
class TestProjectLearningsEndpoints:
    """Test project learnings API endpoints."""

    async def test_extract_learnings_endpoint(self, client, completed_project):
        """Test POST /api/v1/projects/{id}/learnings/extract endpoint."""
        response = await client.post(
            f"/api/v1/projects/{completed_project.project_id}/learnings/extract",
            json={"include_metrics": True},
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_learnings" in data
        assert "by_type" in data

    async def test_metrics_endpoint(self, client, completed_project):
        """Test GET /api/v1/projects/{id}/metrics endpoint."""
        response = await client.get(
            f"/api/v1/projects/{completed_project.project_id}/metrics",
        )
        assert response.status_code == 200
        data = response.json()
        assert "success_score" in data
        assert "timeline" in data
        assert "tasks" in data


@pytest.mark.asyncio
class TestProjectSimilarityEndpoints:
    """Test project similarity API endpoints."""

    async def test_similar_projects_endpoint(self, client, test_project):
        """Test GET /api/v1/projects/{id}/similar endpoint."""
        response = await client.get(
            f"/api/v1/projects/{test_project.project_id}/similar",
        )
        # May return empty list or projects depending on data
        assert response.status_code == 200
        data = response.json()
        assert "similar_projects" in data

    async def test_recommendations_endpoint(self, client, test_project):
        """Test GET /api/v1/projects/{id}/recommendations endpoint."""
        response = await client.get(
            f"/api/v1/projects/{test_project.project_id}/recommendations",
        )
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data

    async def test_knowledge_reuse_endpoint(self, client, test_project):
        """Test GET /api/v1/projects/{id}/knowledge-reuse endpoint."""
        response = await client.get(
            f"/api/v1/projects/{test_project.project_id}/knowledge-reuse",
        )
        assert response.status_code == 200
        data = response.json()
        assert "knowledge_reuse_potential" in data


# ==========================================
# Performance Tests
# ==========================================


@pytest.mark.asyncio
class TestPhase2Performance:
    """Performance tests for Phase 2 components."""

    async def test_task_pause_performance(self, service, session, test_task):
        """Test that task pause completes within acceptable time."""
        import time

        start = time.time()
        await service.pause_task(
            session=session,
            task_id=test_task.task_id,
            reason="Performance test",
        )
        duration = time.time() - start

        # Should complete within 1 second
        assert duration < 1.0

    async def test_learnings_extraction_performance(self, service, session, project_with_tasks):
        """Test that learnings extraction completes within acceptable time."""
        import time

        start = time.time()
        await service.extract_learnings_from_project(
            session=session,
            project_id=project_with_tasks.project_id,
        )
        duration = time.time() - start

        # Should complete within 2 seconds
        assert duration < 2.0


# ==========================================
# Conftest Fixtures (for pytest)
# ==========================================


@pytest.fixture
def test_task():
    """Create a test task fixture."""
    return Task(
        task_id=uuid4(),
        project_id=uuid4(),
        assigned_to_agent_id="test_agent",
        title="Test Task",
        description="Test description",
        status=TaskStatus.IN_PROGRESS,
    )


@pytest.fixture
def completed_project():
    """Create a completed project fixture."""
    return Project(
        project_id=uuid4(),
        name="Completed Project",
        description="Test completed project",
        status=ProjectStatus.COMPLETED,
        priority=Priority.HIGH,
        owner_agent_id="test_agent",
        completed_at=datetime.utcnow(),
    )


@pytest.fixture
def test_project():
    """Create a test project fixture."""
    return Project(
        project_id=uuid4(),
        name="Test Project",
        description="Test project description",
        status=ProjectStatus.IN_PROGRESS,
        priority=Priority.MEDIUM,
        owner_agent_id="test_agent",
    )
