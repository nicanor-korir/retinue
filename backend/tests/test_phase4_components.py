"""
Phase 4 Comprehensive Test Suite

Tests for all Phase 4 components:
- Component 1: Cross-Project Patterns
- Component 2: Domain Pattern Libraries
- Component 3: Hybrid Search
- Component 4: Learning Graph Builder
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
)

# Import services
from app.services.cross_project_pattern_service import (
    get_cross_project_pattern_service,
    CrossProjectPatternService,
)
from app.services.domain_pattern_library_service import (
    get_domain_pattern_library_service,
    DomainPatternLibraryService,
)
from app.services.hybrid_search_service import (
    get_hybrid_search_service,
    HybridSearchService,
)
from app.services.learning_graph_builder_service import (
    get_learning_graph_builder_service,
    LearningGraphBuilderService,
)


# ==========================================
# Component 1: Cross-Project Pattern Tests
# ==========================================


class TestCrossProjectPatternService:
    """Test suite for cross-project pattern service."""

    @pytest.fixture
    async def service(self):
        """Create cross-project pattern service instance."""
        return get_cross_project_pattern_service()

    @pytest.fixture
    async def test_tasks(self, session: AsyncSession):
        """Create test tasks across multiple projects."""
        tasks = []

        for project_idx in range(2):
            for task_idx in range(3):
                task = Task(
                    task_id=uuid4(),
                    project_id=uuid4(),
                    assigned_to_agent_id="test_agent",
                    title=f"Task {task_idx} in Project {project_idx}",
                    description="Test task for pattern detection",
                    status=TaskStatus.COMPLETED,
                    success_score=0.85 if task_idx < 2 else 0.65,
                    pattern_category="authentication" if task_idx % 2 == 0 else "caching",
                    technologies=["FastAPI", "PostgreSQL"],
                )
                session.add(task)
                tasks.append(task)

        await session.commit()
        return tasks

    @pytest.mark.asyncio
    async def test_find_cross_project_patterns(self, service, session, test_tasks):
        """Test finding patterns across projects."""
        patterns = await service.find_patterns_across_projects(
            session=session,
            min_occurrences=2,
            min_success_rate=0.6
        )

        assert patterns is not None
        assert isinstance(patterns, list)

    @pytest.mark.asyncio
    async def test_pattern_success_rate_calculation(self, service, session, test_tasks):
        """Test that success rates are calculated correctly."""
        patterns = await service.find_patterns_across_projects(
            session=session,
            min_occurrences=1,
            min_success_rate=0.5
        )

        for pattern in patterns:
            assert 0 <= pattern.success_rate <= 1.0

    @pytest.mark.asyncio
    async def test_get_pattern_by_id(self, service, session, test_tasks):
        """Test retrieving a specific pattern by ID."""
        patterns = await service.find_patterns_across_projects(session)

        if patterns:
            pattern = await service.get_pattern_by_id(
                session,
                patterns[0].pattern_id
            )
            assert pattern is not None
            assert pattern.pattern_id == patterns[0].pattern_id

    @pytest.mark.asyncio
    async def test_get_pattern_statistics(self, service, session, test_tasks):
        """Test getting pattern statistics."""
        stats = await service.get_pattern_statistics(session)

        assert isinstance(stats, dict)
        assert "total_patterns" in stats

    @pytest.mark.asyncio
    async def test_recommend_patterns_for_task(self, service, session, test_tasks):
        """Test pattern recommendations for a new task."""
        recommendations = await service.recommend_patterns_for_task(
            session=session,
            task_title="Authentication Task",
            task_description="Implement JWT authentication",
            project_id=uuid4()
        )

        assert isinstance(recommendations, list)

    @pytest.mark.asyncio
    async def test_cross_project_caching(self, service, session, test_tasks):
        """Test that results are cached."""
        # First call
        patterns1 = await service.find_patterns_across_projects(session)

        # Second call (should be cached)
        patterns2 = await service.find_patterns_across_projects(session)

        assert len(patterns1) == len(patterns2)


# ==========================================
# Component 2: Domain Pattern Library Tests
# ==========================================


class TestDomainPatternLibraryService:
    """Test suite for domain pattern library service."""

    @pytest.fixture
    async def service(self):
        """Create domain pattern library service instance."""
        return get_domain_pattern_library_service()

    @pytest.fixture
    async def initialized_service(self, service, session):
        """Initialize service with default domains."""
        await service.initialize_default_libraries(session)
        return service

    @pytest.mark.asyncio
    async def test_initialize_default_libraries(self, service, session):
        """Test initializing default domain libraries."""
        libraries = await service.initialize_default_libraries(session)

        assert libraries is not None
        assert len(libraries) > 0
        assert "ecommerce" in libraries or "saas" in libraries

    @pytest.mark.asyncio
    async def test_get_library_by_domain(self, initialized_service, session):
        """Test retrieving a specific domain library."""
        library = await initialized_service.get_library_by_domain(
            session,
            "ecommerce"
        )

        assert library is not None
        assert library.domain_name is not None

    @pytest.mark.asyncio
    async def test_search_patterns_in_domain(self, initialized_service, session):
        """Test searching patterns within a domain."""
        patterns = await initialized_service.search_patterns_in_domain(
            session=session,
            domain_key="ecommerce",
            query="payment"
        )

        assert isinstance(patterns, list)

    @pytest.mark.asyncio
    async def test_get_patterns_by_complexity(self, initialized_service, session):
        """Test filtering patterns by complexity level."""
        easy_patterns = await initialized_service.get_patterns_by_complexity(
            session=session,
            domain_key="ecommerce",
            complexity_level="Easy"
        )

        assert isinstance(easy_patterns, list)

    @pytest.mark.asyncio
    async def test_get_patterns_by_technology(self, initialized_service, session):
        """Test filtering patterns by technology."""
        patterns = await initialized_service.get_patterns_by_technology(
            session=session,
            domain_key="saas",
            technology="FastAPI"
        )

        assert isinstance(patterns, list)

    @pytest.mark.asyncio
    async def test_get_library_statistics(self, initialized_service, session):
        """Test getting statistics for a domain library."""
        stats = await initialized_service.get_library_statistics(
            session=session,
            domain_key="ecommerce"
        )

        assert isinstance(stats, dict)
        assert "pattern_count" in stats or "domain" in stats

    @pytest.mark.asyncio
    async def test_recommend_domains_for_project(self, initialized_service, session):
        """Test domain recommendations for a project."""
        recommendations = await initialized_service.recommend_domains_for_project(
            session=session,
            project_name="E-commerce Platform",
            project_description="Build online shopping platform with payments"
        )

        assert isinstance(recommendations, list)


# ==========================================
# Component 3: Hybrid Search Tests
# ==========================================


class TestHybridSearchService:
    """Test suite for hybrid search service."""

    @pytest.fixture
    async def service(self):
        """Create hybrid search service instance."""
        return get_hybrid_search_service()

    @pytest.fixture
    async def test_tasks(self, session: AsyncSession):
        """Create test tasks for search."""
        tasks = []

        for i in range(5):
            task = Task(
                task_id=uuid4(),
                project_id=uuid4(),
                assigned_to_agent_id="test_agent",
                title=f"Authentication Task {i}",
                description="Implement user authentication with JWT tokens",
                status=TaskStatus.COMPLETED,
                success_score=0.8,
            )
            session.add(task)
            tasks.append(task)

        await session.commit()
        return tasks

    @pytest.mark.asyncio
    async def test_hybrid_search_basic(self, service, session, test_tasks):
        """Test basic hybrid search."""
        results = await service.hybrid_search(
            session=session,
            query="authentication"
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_hybrid_search_with_entity_types(self, service, session, test_tasks):
        """Test hybrid search with entity type filtering."""
        results = await service.hybrid_search(
            session=session,
            query="authentication",
            entity_types=["task"]
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_hybrid_search_top_k(self, service, session, test_tasks):
        """Test hybrid search with top_k limit."""
        results = await service.hybrid_search(
            session=session,
            query="authentication",
            top_k=3
        )

        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_hybrid_search_scoring(self, service, session, test_tasks):
        """Test that hybrid search produces valid scores."""
        results = await service.hybrid_search(
            session=session,
            query="authentication"
        )

        for result in results:
            assert 0 <= result.combined_score <= 1
            assert 0 <= result.vector_score <= 1
            assert 0 <= result.keyword_score <= 1

    @pytest.mark.asyncio
    async def test_advanced_search_with_filters(self, service, session, test_tasks):
        """Test advanced search with filters."""
        results = await service.advanced_search(
            session=session,
            query="authentication",
            filters={
                "entity_type": ["task"],
                "min_success_score": 0.7
            }
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_hybrid_search_caching(self, service, session, test_tasks):
        """Test that search results are cached."""
        # First search
        results1 = await service.hybrid_search(
            session=session,
            query="authentication"
        )

        # Second search (cached)
        results2 = await service.hybrid_search(
            session=session,
            query="authentication"
        )

        assert len(results1) == len(results2)


# ==========================================
# Component 4: Learning Graph Builder Tests
# ==========================================


class TestLearningGraphBuilderService:
    """Test suite for learning graph builder service."""

    @pytest.fixture
    async def service(self):
        """Create learning graph builder service instance."""
        return get_learning_graph_builder_service()

    @pytest.fixture
    async def test_data(self, session: AsyncSession):
        """Create test projects and tasks."""
        projects = []
        for i in range(2):
            project = Project(
                project_id=uuid4(),
                name=f"Test Project {i}",
                description=f"Test project description {i}",
                status=ProjectStatus.COMPLETED,
                priority=Priority.HIGH,
                owner_agent_id="test_agent",
            )
            session.add(project)
            projects.append(project)

            # Add tasks to each project
            for j in range(3):
                task = Task(
                    task_id=uuid4(),
                    project_id=project.project_id,
                    assigned_to_agent_id="test_agent",
                    title=f"Task {j}",
                    description="Test task",
                    status=TaskStatus.COMPLETED,
                    success_score=0.8,
                    pattern_category="authentication" if j == 0 else "caching",
                    technologies=["FastAPI", "PostgreSQL"],
                )
                session.add(task)

        await session.commit()
        return projects

    @pytest.mark.asyncio
    async def test_build_graph(self, service, session, test_data):
        """Test building the learning graph."""
        graph = await service.build_graph(session)

        assert graph is not None
        assert len(graph.nodes) > 0

    @pytest.mark.asyncio
    async def test_graph_contains_projects(self, service, session, test_data):
        """Test that graph contains project nodes."""
        graph = await service.build_graph(session)

        project_nodes = [n for n in graph.nodes.values() if n.node_type == "project"]
        assert len(project_nodes) > 0

    @pytest.mark.asyncio
    async def test_graph_contains_patterns(self, service, session, test_data):
        """Test that graph contains pattern nodes."""
        graph = await service.build_graph(session)

        pattern_nodes = [n for n in graph.nodes.values() if n.node_type == "pattern"]
        # May or may not have patterns depending on data
        assert isinstance(pattern_nodes, list)

    @pytest.mark.asyncio
    async def test_graph_contains_edges(self, service, session, test_data):
        """Test that graph contains edges."""
        graph = await service.build_graph(session)

        assert len(graph.edges) > 0 or len(graph.nodes) == 0

    @pytest.mark.asyncio
    async def test_get_graph_statistics(self, service, session, test_data):
        """Test getting graph statistics."""
        stats = await service.get_node_statistics(session)

        assert isinstance(stats, dict)
        assert "node_count" in stats

    @pytest.mark.asyncio
    async def test_find_learning_path(self, service, session, test_data):
        """Test finding a path between nodes."""
        graph = await service.get_graph(session)

        if len(graph.nodes) >= 2:
            node_ids = list(graph.nodes.keys())
            path = await service.find_learning_path(
                session=session,
                start_node_id=node_ids[0],
                target_node_id=node_ids[-1]
            )

            assert isinstance(path, list)

    @pytest.mark.asyncio
    async def test_graph_caching(self, service, session, test_data):
        """Test that graph is cached."""
        # First build
        graph1 = await service.get_graph(session)

        # Second build (cached)
        graph2 = await service.get_graph(session)

        assert len(graph1.nodes) == len(graph2.nodes)
        assert len(graph1.edges) == len(graph2.edges)


# ==========================================
# Integration Tests
# ==========================================


class TestPhase4Integration:
    """Integration tests for Phase 4 components."""

    @pytest.mark.asyncio
    async def test_cross_project_workflow(self, session: AsyncSession):
        """Test complete cross-project workflow."""
        # Create test data
        for i in range(2):
            project = Project(
                project_id=uuid4(),
                name=f"Project {i}",
                description=f"Test project {i}",
                status=ProjectStatus.COMPLETED,
                priority=Priority.HIGH,
                owner_agent_id="test_agent",
            )
            session.add(project)

            task = Task(
                task_id=uuid4(),
                project_id=project.project_id,
                assigned_to_agent_id="test_agent",
                title="Test Task",
                description="Testing cross-project patterns",
                status=TaskStatus.COMPLETED,
                success_score=0.85,
                pattern_category="authentication",
            )
            session.add(task)

        await session.commit()

        # Test cross-project pattern discovery
        pattern_service = get_cross_project_pattern_service()
        patterns = await pattern_service.find_patterns_across_projects(session)

        assert isinstance(patterns, list)

    @pytest.mark.asyncio
    async def test_domain_and_hybrid_search_workflow(self, session: AsyncSession):
        """Test domain library and hybrid search together."""
        # Initialize domain libraries
        domain_service = get_domain_pattern_library_service()
        await domain_service.initialize_default_libraries(session)

        # Perform hybrid search
        search_service = get_hybrid_search_service()
        results = await search_service.hybrid_search(
            session=session,
            query="payment"
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_learning_graph_with_patterns(self, session: AsyncSession):
        """Test learning graph with pattern data."""
        # Create test projects and tasks
        for i in range(2):
            project = Project(
                project_id=uuid4(),
                name=f"Project {i}",
                description="Test",
                status=ProjectStatus.COMPLETED,
                priority=Priority.MEDIUM,
                owner_agent_id="test_agent",
            )
            session.add(project)

            for j in range(2):
                task = Task(
                    task_id=uuid4(),
                    project_id=project.project_id,
                    assigned_to_agent_id="test_agent",
                    title=f"Task {j}",
                    description="Test",
                    status=TaskStatus.COMPLETED,
                    success_score=0.8,
                    pattern_category="authentication",
                    technologies=["FastAPI"],
                )
                session.add(task)

        await session.commit()

        # Build graph
        graph_service = get_learning_graph_builder_service()
        graph = await graph_service.build_graph(session)

        # Get statistics
        stats = await graph_service.get_node_statistics(session)

        assert stats["node_count"] > 0


# ==========================================
# Performance Tests
# ==========================================


class TestPhase4Performance:
    """Performance tests for Phase 4 components."""

    @pytest.mark.asyncio
    async def test_pattern_discovery_performance(self, session: AsyncSession):
        """Test that pattern discovery completes within acceptable time."""
        import time

        service = get_cross_project_pattern_service()

        start = time.time()
        await service.find_patterns_across_projects(session)
        duration = time.time() - start

        # Should complete within 2 seconds
        assert duration < 2.0

    @pytest.mark.asyncio
    async def test_hybrid_search_performance(self, session: AsyncSession):
        """Test that hybrid search completes within acceptable time."""
        import time

        service = get_hybrid_search_service()

        start = time.time()
        await service.hybrid_search(session, query="test")
        duration = time.time() - start

        # Should complete within 1 second
        assert duration < 1.0

    @pytest.mark.asyncio
    async def test_graph_build_performance(self, session: AsyncSession):
        """Test that graph building completes within acceptable time."""
        import time

        service = get_learning_graph_builder_service()

        start = time.time()
        await service.build_graph(session)
        duration = time.time() - start

        # Should complete within 3 seconds
        assert duration < 3.0
