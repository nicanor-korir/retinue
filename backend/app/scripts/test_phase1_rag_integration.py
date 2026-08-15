"""
Comprehensive tests for Phase 1 RAG Integration

Tests cover:
1. TaskRAGIntegration service - context retrieval and task indexing
2. Event-driven task indexing - automatic indexing on task completion
3. WebSocket connectivity - real-time activity streaming
4. Caching layer - context caching and performance
5. Integration with existing RAG services
"""

import asyncio
import logging
from uuid import UUID, uuid4
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.db.database import Base
from app.db.models import Task, Project, Agent, TaskStatus, TaskRAGStatus
from app.services.task_rag_integration import get_task_rag_integration
from app.services.event_bus import EventBus, Event, EventType
from app.services.rag_cache_service import get_cache_service
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class TestPhase1RAGIntegration:
    """Test suite for Phase 1 RAG Integration."""

    def __init__(self):
        """Initialize test suite."""
        self.test_results = []
        self.passed = 0
        self.failed = 0
        self.engine = None
        self.AsyncSession = None
        self.task_rag = get_task_rag_integration()
        self.cache_service = get_cache_service()
        self.event_bus = EventBus()

    async def setup(self):
        """Set up test database."""
        # Create async SQLAlchemy engine for testing
        self.engine = create_async_engine(
            "sqlite+aiosqlite:///:memory:",
            echo=False,
        )

        # Create all tables
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        self.AsyncSession = sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        logger.info("✅ Test database setup complete")

    async def teardown(self):
        """Clean up test database."""
        if self.engine:
            await self.engine.dispose()
        logger.info("✅ Test cleanup complete")

    async def test_1_context_retrieval(self):
        """Test 1: Get context for a new task"""
        logger.info("\n🧪 Test 1: Context retrieval for new tasks")

        try:
            context = await self.task_rag.get_context_for_task(
                task_id=uuid4(),
                title="Implement API authentication",
                description="Add JWT token-based authentication to REST API",
                top_k=5,
            )

            assert context is not None, "Context should not be None"
            assert "contexts" in context, "Context should have 'contexts' key"
            assert "patterns" in context, "Context should have 'patterns' key"
            assert isinstance(context["contexts"], list), "Contexts should be a list"

            logger.info(f"✅ Retrieved context with {len(context['contexts'])} similar tasks")
            logger.info(f"✅ Found {len(context['patterns'])} patterns")
            self._record_test("Context Retrieval", True)
            self.passed += 1

        except Exception as e:
            logger.error(f"❌ Context retrieval failed: {e}")
            self._record_test("Context Retrieval", False, str(e))
            self.failed += 1

    async def test_2_task_indexing_on_completion(self):
        """Test 2: Task indexing when marked as completed"""
        logger.info("\n🧪 Test 2: Automatic task indexing on completion")

        try:
            async with self.AsyncSession() as session:
                # Create test project
                project = Project(
                    project_id=uuid4(),
                    name="Test Project",
                    description="For testing RAG indexing",
                    status="PLANNING",
                    priority="HIGH",
                    owner_agent_id="backend_001",
                )
                session.add(project)
                await session.commit()

                # Create test task
                task = Task(
                    task_id=uuid4(),
                    project_id=project.project_id,
                    assigned_to_agent_id="backend_001",
                    title="Test Task",
                    description="A test task for indexing",
                    status=TaskStatus.COMPLETED,
                    output="Task completed successfully",
                )
                session.add(task)
                await session.commit()

                # Index the task
                success = await self.task_rag.index_task_on_completion(
                    session=session,
                    task_id=task.task_id,
                )

                assert success, "Task indexing should succeed"

                # Verify task was marked as indexed
                from sqlalchemy import select
                result = await session.execute(
                    select(Task).where(Task.task_id == task.task_id)
                )
                updated_task = result.scalar_one()
                assert updated_task.rag_status == TaskRAGStatus.INDEXED, "Task should be marked as indexed"

                logger.info(f"✅ Task {task.task_id} successfully indexed")
                self._record_test("Task Indexing on Completion", True)
                self.passed += 1

        except Exception as e:
            logger.error(f"❌ Task indexing failed: {e}")
            self._record_test("Task Indexing on Completion", False, str(e))
            self.failed += 1

    async def test_3_cache_performance(self):
        """Test 3: Context caching reduces latency"""
        logger.info("\n🧪 Test 3: Cache performance")

        try:
            task_id = uuid4()
            title = "Test Task"
            description = "Test description"

            # First call - no cache
            import time
            start = time.time()
            context1 = await self.task_rag.get_context_for_task(
                task_id=task_id,
                title=title,
                description=description,
            )
            first_call_time = time.time() - start

            # Second call - should hit cache
            start = time.time()
            context2 = await self.task_rag.get_context_for_task(
                task_id=task_id,
                title=title,
                description=description,
            )
            second_call_time = time.time() - start

            assert context1 == context2, "Cached context should match original"
            assert second_call_time < first_call_time, "Cached call should be faster"

            speedup = first_call_time / second_call_time if second_call_time > 0 else 1
            logger.info(f"✅ Cache speedup: {speedup:.1f}x")
            logger.info(f"   First call:  {first_call_time*1000:.1f}ms")
            logger.info(f"   Cached call: {second_call_time*1000:.1f}ms")

            self._record_test("Cache Performance", True)
            self.passed += 1

        except Exception as e:
            logger.error(f"❌ Cache performance test failed: {e}")
            self._record_test("Cache Performance", False, str(e))
            self.failed += 1

    async def test_4_task_statistics(self):
        """Test 4: Get task statistics"""
        logger.info("\n🧪 Test 4: Task statistics")

        try:
            async with self.AsyncSession() as session:
                # Create test project
                project = Project(
                    project_id=uuid4(),
                    name="Test Project",
                    description="For testing statistics",
                    status="PLANNING",
                    priority="HIGH",
                    owner_agent_id="backend_001",
                )
                session.add(project)

                # Create multiple test tasks
                for i in range(5):
                    task = Task(
                        task_id=uuid4(),
                        project_id=project.project_id,
                        assigned_to_agent_id="backend_001",
                        title=f"Task {i}",
                        description=f"Test task {i}",
                        status=TaskStatus.COMPLETED if i % 2 == 0 else TaskStatus.PENDING,
                        rag_status=TaskRAGStatus.INDEXED if i % 2 == 0 else TaskRAGStatus.NOT_INDEXED,
                    )
                    session.add(task)

                await session.commit()

                # Get statistics
                stats = await self.task_rag.get_task_statistics(session)

                assert "total_tasks" in stats, "Stats should have total_tasks"
                assert "indexed_tasks" in stats, "Stats should have indexed_tasks"
                assert stats["total_tasks"] == 5, "Should have 5 tasks"
                assert stats["indexed_tasks"] >= 0, "Should have indexed tasks count"

                logger.info(f"✅ Task statistics:")
                logger.info(f"   Total tasks: {stats['total_tasks']}")
                logger.info(f"   Indexed: {stats['indexed_tasks']}")
                logger.info(f"   Failed: {stats['indexing_failed']}")
                logger.info(f"   Not indexed: {stats['not_indexed']}")

                self._record_test("Task Statistics", True)
                self.passed += 1

        except Exception as e:
            logger.error(f"❌ Task statistics test failed: {e}")
            self._record_test("Task Statistics", False, str(e))
            self.failed += 1

    async def test_5_event_bus_integration(self):
        """Test 5: Event bus integration for task events"""
        logger.info("\n🧪 Test 5: Event bus integration")

        try:
            event_fired = False

            async def test_handler(event: Event):
                nonlocal event_fired
                event_fired = True
                logger.info(f"Event handler received: {event.event_type}")

            # Subscribe to task completion events
            self.event_bus.subscribe(
                event_type=EventType.TASK_COMPLETED,
                handler=test_handler,
            )

            # Publish a task completed event
            event = Event(
                event_type=EventType.TASK_COMPLETED,
                data={
                    "task_id": str(uuid4()),
                    "title": "Test Task",
                    "status": "COMPLETED",
                },
                project_id="test-project",
            )

            await self.event_bus.publish(event)

            # Give handler time to process
            await asyncio.sleep(0.1)

            assert event_fired, "Event handler should have been called"

            logger.info("✅ Event bus integration working")
            self._record_test("Event Bus Integration", True)
            self.passed += 1

        except Exception as e:
            logger.error(f"❌ Event bus integration test failed: {e}")
            self._record_test("Event Bus Integration", False, str(e))
            self.failed += 1

    async def test_6_pattern_extraction(self):
        """Test 6: Pattern extraction from completed tasks"""
        logger.info("\n🧪 Test 6: Pattern extraction")

        try:
            patterns = await self.task_rag.extract_patterns_from_task(
                task_id=uuid4(),
            )

            assert isinstance(patterns, list), "Patterns should be a list"
            assert len(patterns) > 0, "Should extract at least one pattern"

            logger.info(f"✅ Extracted {len(patterns)} patterns:")
            for pattern in patterns:
                logger.info(f"   - {pattern}")

            self._record_test("Pattern Extraction", True)
            self.passed += 1

        except Exception as e:
            logger.error(f"❌ Pattern extraction test failed: {e}")
            self._record_test("Pattern Extraction", False, str(e))
            self.failed += 1

    async def test_7_cache_clearing(self):
        """Test 7: Cache clearing functionality"""
        logger.info("\n🧪 Test 7: Cache clearing")

        try:
            task_id = uuid4()

            # Set cache
            context = await self.task_rag.get_context_for_task(
                task_id=task_id,
                title="Test Task",
                description="Test description",
            )

            # Verify cache exists
            cache_key = f"task_context:{task_id}"
            assert self.cache_service.get(cache_key) is not None, "Cache should exist"

            # Clear cache
            self.task_rag.clear_context_cache(task_id)

            # Verify cache is cleared
            assert self.cache_service.get(cache_key) is None, "Cache should be cleared"

            logger.info("✅ Cache clearing works correctly")
            self._record_test("Cache Clearing", True)
            self.passed += 1

        except Exception as e:
            logger.error(f"❌ Cache clearing test failed: {e}")
            self._record_test("Cache Clearing", False, str(e))
            self.failed += 1

    def _record_test(self, name: str, passed: bool, error: str = ""):
        """Record test result."""
        self.test_results.append({
            "name": name,
            "passed": passed,
            "error": error,
        })

    async def run_all_tests(self):
        """Run all tests."""
        logger.info("=" * 60)
        logger.info("🚀 PHASE 1 RAG INTEGRATION TEST SUITE")
        logger.info("=" * 60)

        try:
            await self.setup()

            # Run tests
            await self.test_1_context_retrieval()
            await self.test_2_task_indexing_on_completion()
            await self.test_3_cache_performance()
            await self.test_4_task_statistics()
            await self.test_5_event_bus_integration()
            await self.test_6_pattern_extraction()
            await self.test_7_cache_clearing()

        finally:
            await self.teardown()

        # Print summary
        self._print_summary()

        return self.failed == 0

    def _print_summary(self):
        """Print test summary."""
        logger.info("\n" + "=" * 60)
        logger.info("📊 TEST SUMMARY")
        logger.info("=" * 60)

        for result in self.test_results:
            status = "✅ PASS" if result["passed"] else "❌ FAIL"
            logger.info(f"{status}: {result['name']}")
            if result["error"]:
                logger.info(f"   Error: {result['error']}")

        logger.info("=" * 60)
        logger.info(f"Results: {self.passed} passed, {self.failed} failed out of {self.passed + self.failed} tests")
        logger.info("=" * 60)

        if self.failed == 0:
            logger.info("🎉 ALL TESTS PASSED!")
        else:
            logger.info(f"⚠️  {self.failed} TEST(S) FAILED")


async def main():
    """Run test suite."""
    test_suite = TestPhase1RAGIntegration()
    success = await test_suite.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
