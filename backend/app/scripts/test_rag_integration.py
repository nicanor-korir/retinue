"""
Quick integration test for RAG with all agents.

Tests that RAG can be called from all agent types without errors.

Usage:
    python -m app.scripts.test_rag_integration
"""

import asyncio
import logging
import sys
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal, init_db
from app.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def test_rag_indexing():
    """Test basic RAG indexing and retrieval."""
    logger.info("\n📝 Testing RAG Indexing...")

    rag_service = get_rag_service()

    # Index test data
    test_data = [
        {
            "task_id": "test_task_001",
            "title": "Build Authentication API",
            "description": "Create JWT-based authentication endpoints",
            "output": "Implemented /auth/login, /auth/register, /auth/refresh endpoints",
            "agent_id": "backend_001",
            "project_id": "proj_001",
            "status": "completed",
        },
        {
            "decision_id": "test_decision_001",
            "question": "Which auth method to use?",
            "decision": "JWT tokens with refresh rotation",
            "rationale": "Secure, stateless, works well with microservices",
            "decision_type": "technical",
            "agent_id": "cto_001",
            "project_id": "proj_001",
            "approved": True,
        },
        {
            "message_id": "test_message_001",
            "content": "Code review approved - good error handling and validation",
            "from_agent_id": "cto_001",
            "to_agent_id": "backend_001",
            "message_type": "approval",
            "project_id": "proj_001",
            "task_id": None,
        },
    ]

    try:
        # Index task
        await rag_service.index_task(**test_data[0])
        logger.info("  ✓ Task indexed")

        # Index decision
        await rag_service.index_decision(**test_data[1])
        logger.info("  ✓ Decision indexed")

        # Index message
        await rag_service.index_message(**test_data[2])
        logger.info("  ✓ Message indexed")

        # Check stats
        stats = await rag_service.get_stats()
        logger.info(f"  ✓ RAG stats: {stats}")

        logger.info("✅ RAG Indexing test PASSED")
        return True

    except Exception as e:
        logger.error(f"❌ RAG Indexing test FAILED: {e}", exc_info=True)
        return False


async def test_rag_retrieval():
    """Test RAG retrieval for different queries."""
    logger.info("\n🔍 Testing RAG Retrieval...")

    rag_service = get_rag_service()

    test_queries = [
        ("authentication", ["tasks", "decisions"]),
        ("API endpoints", ["tasks"]),
        ("code review", ["messages"]),
    ]

    all_passed = True

    for query, collections in test_queries:
        try:
            results = await rag_service.retrieve_context(
                query=query,
                collections=collections,
                top_k=3,
            )

            if results and any(results.values()):
                logger.info(f"  ✓ Retrieved results for: '{query}'")
            else:
                logger.warning(f"  ⚠️  No results for: '{query}'")
                all_passed = False

        except Exception as e:
            logger.error(f"  ❌ Retrieval failed for '{query}': {e}")
            all_passed = False

    if all_passed:
        logger.info("✅ RAG Retrieval test PASSED")
    else:
        logger.info("⚠️  RAG Retrieval test PARTIALLY PASSED")

    return all_passed


async def test_agent_rag_calls():
    """Test that agents can call RAG without errors."""
    logger.info("\n👥 Testing Agent RAG Calls...")

    from app.services.rag_agent_strategies import retrieve_agent_context, format_agent_context

    agents = [
        ("ceo_001", "What strategic decisions were made?"),
        ("cto_001", "What technical implementations do we have?"),
        ("pm_001", "How have we structured projects?"),
        ("backend_001", "What APIs have we built?"),
        ("frontend_001", "What components did we create?"),
        ("designer_001", "What design patterns did we use?"),
    ]

    all_passed = True

    for agent_id, query in agents:
        try:
            # Test retrieve_agent_context
            context = await retrieve_agent_context(
                agent_id=agent_id,
                query=query,
                project_id="proj_001",
            )

            # Test format_agent_context
            if context:
                formatted = await format_agent_context(agent_id, context)
                logger.info(f"  ✓ {agent_id}: Retrieved and formatted context")
            else:
                logger.info(f"  ✓ {agent_id}: Gracefully handled empty context")

        except Exception as e:
            logger.error(f"  ❌ {agent_id} RAG call failed: {e}")
            all_passed = False

    if all_passed:
        logger.info("✅ Agent RAG calls test PASSED")
    else:
        logger.info("⚠️  Agent RAG calls test PARTIALLY PASSED")

    return all_passed


async def main():
    """Run all integration tests."""
    logger.info("=" * 60)
    logger.info("  RAG Integration Test Suite")
    logger.info("=" * 60)

    try:
        # Initialize database
        await init_db()

        # Run tests
        tests = [
            ("Indexing", test_rag_indexing),
            ("Retrieval", test_rag_retrieval),
            ("Agent RAG Calls", test_agent_rag_calls),
        ]

        results = {}
        for test_name, test_func in tests:
            results[test_name] = await test_func()

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("  📊 TEST SUMMARY")
        logger.info("=" * 60)

        passed = sum(1 for v in results.values() if v)
        total = len(results)

        for test_name, passed_flag in results.items():
            status = "✅ PASS" if passed_flag else "❌ FAIL"
            logger.info(f"  {status}: {test_name}")

        logger.info(f"\n  Total: {passed}/{total} tests passed")

        if passed == total:
            logger.info("\n✨ All integration tests PASSED!")
            logger.info("RAG system is fully integrated with agents!")
            sys.exit(0)
        else:
            logger.warning(f"\n⚠️  {total - passed} test(s) failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
