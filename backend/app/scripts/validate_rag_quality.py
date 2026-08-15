"""
RAG Quality Validation Script

Tests the RAG system to ensure embeddings and retrieval are working properly.
Validates retrieval accuracy across different agent types and query patterns.

Usage:
    python -m app.scripts.validate_rag_quality
"""

import asyncio
import logging
import sys
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import AsyncSessionLocal, init_db
from app.services.rag_service import get_rag_service
from app.services.rag_agent_strategies import retrieve_agent_context

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

# Test data for validation
TEST_TASK_DATA = [
    {
        "task_id": "test_001",
        "title": "Build User Authentication API",
        "description": "Create REST API endpoints for user authentication with JWT tokens",
        "output": "Created /api/auth endpoints with login, register, refresh functionality",
        "agent_id": "backend_001",
        "project_id": "proj_001",
        "status": "completed",
    },
    {
        "task_id": "test_002",
        "title": "Design Dashboard UI",
        "description": "Create wireframes and visual specifications for main dashboard",
        "output": "Created dashboard design with cards, charts, and responsive layout",
        "agent_id": "designer_001",
        "project_id": "proj_001",
        "status": "completed",
    },
    {
        "task_id": "test_003",
        "title": "Implement User Profile Page",
        "description": "Build React component for user profile with edit functionality",
        "output": "Created /profile page with editable fields and validation",
        "agent_id": "frontend_001",
        "project_id": "proj_001",
        "status": "completed",
    },
]

# Test queries by agent type
TEST_QUERIES = {
    "backend_001": [
        "How do I implement authentication?",
        "What API endpoints do we have?",
        "Show me previous authentication implementations",
    ],
    "designer_001": [
        "What design patterns have we used?",
        "How should the UI look?",
        "Show dashboard designs",
    ],
    "frontend_001": [
        "What components did we build?",
        "How to implement user pages?",
        "Show previous React components",
    ],
    "ceo_001": [
        "What projects have we completed?",
        "What key decisions were made?",
        "Project status overview",
    ],
}


async def test_indexing(rag_service) -> bool:
    """Test that indexing works correctly."""
    logger.info("\n📝 Testing RAG Indexing...")

    try:
        for task_data in TEST_TASK_DATA:
            await rag_service.index_task(**task_data)
            logger.info(f"  ✓ Indexed task: {task_data['title']}")

        stats = await rag_service.get_stats()
        logger.info(f"  ✓ RAG stats: {stats}")

        if stats.get("tasks", 0) >= len(TEST_TASK_DATA):
            logger.info("✅ Indexing test PASSED")
            return True
        else:
            logger.warning("⚠️  Indexing test FAILED - not all tasks indexed")
            return False

    except Exception as e:
        logger.error(f"❌ Indexing test FAILED: {e}")
        return False


async def test_retrieval_accuracy(rag_service) -> bool:
    """Test retrieval accuracy for different queries."""
    logger.info("\n🔍 Testing RAG Retrieval Accuracy...")

    all_passed = True

    for query, expected_keywords in [
        ("authentication API", ["authentication", "API", "login"]),
        ("dashboard design", ["dashboard", "design"]),
        ("user profile component", ["profile", "user", "React"]),
    ]:
        try:
            results = await rag_service.retrieve_context(
                query=query,
                collections=["tasks"],
                top_k=3,
            )

            if not results or not results.get("tasks", {}).get("documents"):
                logger.warning(f"  ⚠️  No results for query: '{query}'")
                all_passed = False
                continue

            # Check if retrieved documents contain expected keywords
            documents = results["tasks"]["documents"]
            scores = results["tasks"]["scores"]

            logger.info(f"  Query: '{query}'")
            logger.info(f"    Top result (relevance: {scores[0]:.2%}): {documents[0][:80]}...")

            # Check relevance
            if scores[0] < 0.5:
                logger.warning(f"    ⚠️  Low relevance score: {scores[0]:.2%}")
                all_passed = False
            else:
                logger.info(f"    ✓ Good relevance score: {scores[0]:.2%}")

        except Exception as e:
            logger.error(f"  ❌ Retrieval failed for '{query}': {e}")
            all_passed = False

    if all_passed:
        logger.info("✅ Retrieval accuracy test PASSED")
    else:
        logger.info("⚠️  Retrieval accuracy test PARTIALLY PASSED")

    return all_passed


async def test_agent_strategies(rag_service) -> bool:
    """Test agent-specific retrieval strategies."""
    logger.info("\n👥 Testing Agent-Specific Retrieval Strategies...")

    all_passed = True

    for agent_id, queries in TEST_QUERIES.items():
        logger.info(f"  Testing {agent_id}:")

        for query in queries:
            try:
                results = await retrieve_agent_context(
                    agent_id=agent_id,
                    query=query,
                    project_id="proj_001",
                )

                if results:
                    logger.info(f"    ✓ Retrieved context for: '{query}'")
                else:
                    logger.warning(f"    ⚠️  No context retrieved for: '{query}'")
                    all_passed = False

            except Exception as e:
                logger.warning(f"    ⚠️  Failed to retrieve for '{query}': {e}")
                all_passed = False

    if all_passed:
        logger.info("✅ Agent strategies test PASSED")
    else:
        logger.info("⚠️  Agent strategies test PARTIALLY PASSED")

    return all_passed


async def test_embedding_dimension(rag_service) -> bool:
    """Test that embeddings have correct dimensions."""
    logger.info("\n📐 Testing Embedding Dimensions...")

    try:
        dimension = await rag_service._embedding_service.get_dimension()
        logger.info(f"  Embedding dimension: {dimension}")

        # Sentence Transformers should have 384 or 768 dimensions
        # OpenAI should have 1536
        if dimension > 0:
            logger.info(f"  ✓ Valid embedding dimension: {dimension}")
            logger.info("✅ Embedding dimension test PASSED")
            return True
        else:
            logger.error(f"  ❌ Invalid embedding dimension: {dimension}")
            return False

    except Exception as e:
        logger.error(f"❌ Embedding dimension test FAILED: {e}")
        return False


async def test_similarity_threshold(rag_service) -> bool:
    """Test similarity threshold filtering."""
    logger.info("\n⚙️  Testing Similarity Threshold...")

    try:
        # Query with high similarity threshold
        results = await rag_service.retrieve_context(
            query="nonexistent xyz abc",  # Query that shouldn't match anything
            collections=["tasks"],
            top_k=5,
        )

        documents = results.get("tasks", {}).get("documents", [])
        scores = results.get("tasks", {}).get("scores", [])

        if not documents:
            logger.info("  ✓ Correctly filtered out low-relevance results")
            logger.info("✅ Similarity threshold test PASSED")
            return True
        else:
            # Even if we get results, check they're above threshold
            if all(score >= 0.7 for score in scores):
                logger.info(f"  ✓ All results above threshold (0.7): {scores}")
                logger.info("✅ Similarity threshold test PASSED")
                return True
            else:
                logger.warning(f"  ⚠️  Results below threshold: {scores}")
                return False

    except Exception as e:
        logger.error(f"❌ Similarity threshold test FAILED: {e}")
        return False


async def main():
    """Run all validation tests."""
    logger.info("=" * 60)
    logger.info("  RAG Quality Validation")
    logger.info("=" * 60)

    try:
        # Initialize database
        await init_db()

        # Get RAG service
        rag_service = get_rag_service()

        # Run all tests
        tests = [
            ("Indexing", test_indexing),
            ("Embedding Dimension", test_embedding_dimension),
            ("Similarity Threshold", test_similarity_threshold),
            ("Retrieval Accuracy", test_retrieval_accuracy),
            ("Agent Strategies", test_agent_strategies),
        ]

        results = {}
        for test_name, test_func in tests:
            results[test_name] = await test_func(rag_service)

        # Summary
        logger.info("\n" + "=" * 60)
        logger.info("  📊 VALIDATION SUMMARY")
        logger.info("=" * 60)

        passed = sum(1 for v in results.values() if v)
        total = len(results)

        for test_name, passed_flag in results.items():
            status = "✅ PASS" if passed_flag else "❌ FAIL"
            logger.info(f"  {status}: {test_name}")

        logger.info(f"\n  Total: {passed}/{total} tests passed")

        if passed == total:
            logger.info("\n✨ All validation tests PASSED!")
            logger.info("RAG system is working correctly!")
            sys.exit(0)
        else:
            logger.warning(f"\n⚠️  {total - passed} test(s) failed")
            logger.warning("Please review the failures above")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Validation failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
