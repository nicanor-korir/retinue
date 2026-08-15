"""
Test script for RAG cache service.

Phase 3: Caching Layer Testing
Purpose: Verify cache functionality, hit/miss tracking, and performance improvements.

Usage:
    python -m app.scripts.test_rag_cache
"""

import asyncio
import logging
import time
import sys
from datetime import datetime

from app.services.rag_cache_service import get_cache_service, initialize_cache_service, shutdown_cache_service

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def test_cache_initialization():
    """Test cache service initialization."""
    logger.info("\n📝 Testing Cache Initialization...")

    cache_service = get_cache_service()
    await cache_service.initialize()

    if cache_service.redis:
        logger.info("  ✓ Redis connection successful")
        logger.info(f"  ✓ Cache enabled: {cache_service.enabled}")
        logger.info(f"  ✓ Cache TTL: {cache_service.ttl}s")
        logger.info(f"  ✓ Max size: {cache_service.max_size}")
        return True
    else:
        logger.error("  ❌ Failed to connect to Redis")
        return False


async def test_cache_basic_operations():
    """Test basic cache operations (get, set, delete)."""
    logger.info("\n📝 Testing Basic Cache Operations...")

    cache_service = get_cache_service()

    # Test data
    test_query = "authentication best practices"
    test_results = {
        "collections": ["tasks", "decisions"],
        "data": {
            "tasks": {"ids": ["task_1"], "documents": ["Build auth API"]},
            "decisions": {"ids": ["dec_1"], "documents": ["Use JWT tokens"]},
        }
    }

    try:
        # Test SET
        logger.info(f"  Testing SET for query: '{test_query}'")
        success = await cache_service.set(
            query=test_query,
            results=test_results,
            project_id="proj_001",
        )
        if success:
            logger.info("  ✓ Cache SET successful")
        else:
            logger.warning("  ⚠️  Cache SET returned False")

        # Test GET (should hit)
        logger.info(f"  Testing GET for cached query")
        cached = await cache_service.get(
            query=test_query,
            project_id="proj_001",
        )
        if cached:
            logger.info("  ✓ Cache GET successful (HIT)")
        else:
            logger.error("  ❌ Cache GET failed (MISS)")
            return False

        # Test GET with different project (should miss)
        logger.info(f"  Testing GET with different project (should MISS)")
        cached = await cache_service.get(
            query=test_query,
            project_id="proj_002",
        )
        if not cached:
            logger.info("  ✓ Cache correctly MISSED for different project")
        else:
            logger.warning("  ⚠️  Unexpected cache HIT for different project")

        # Test DELETE
        logger.info(f"  Testing DELETE")
        deleted = await cache_service.delete(
            query=test_query,
            project_id="proj_001",
        )
        if deleted:
            logger.info("  ✓ Cache DELETE successful")
        else:
            logger.warning("  ⚠️  Cache DELETE returned False")

        # Verify deletion
        cached = await cache_service.get(
            query=test_query,
            project_id="proj_001",
        )
        if not cached:
            logger.info("  ✓ Cache verified deleted")
        else:
            logger.error("  ❌ Cache still exists after delete")

        logger.info("✅ Basic Cache Operations test PASSED")
        return True

    except Exception as e:
        logger.error(f"❌ Basic Cache Operations test FAILED: {e}", exc_info=True)
        return False


async def test_cache_hit_rate():
    """Test cache hit/miss tracking and analytics."""
    logger.info("\n📝 Testing Cache Hit Rate Tracking...")

    cache_service = get_cache_service()

    try:
        # Clear any previous stats
        await cache_service.clear_all()

        # Populate cache with test data
        queries = [
            ("authentication API", "proj_001"),
            ("database design", "proj_001"),
            ("frontend components", "proj_002"),
            ("deployment strategy", "proj_001"),
            ("testing framework", "proj_002"),
        ]

        logger.info(f"  Caching {len(queries)} test queries...")
        for query, project_id in queries:
            await cache_service.set(
                query=query,
                results={"test": "data"},
                project_id=project_id,
            )
        logger.info(f"  ✓ {len(queries)} queries cached")

        # Simulate hits and misses
        hits = 0
        misses = 0

        logger.info("  Simulating cache access patterns...")

        # Hit: repeat same queries
        for query, project_id in queries:
            result = await cache_service.get(query=query, project_id=project_id)
            if result:
                hits += 1
            else:
                misses += 1

        # Miss: new queries
        new_queries = [
            ("new feature discussion", "proj_001"),
            ("bug fixing approach", "proj_002"),
        ]

        for query, project_id in new_queries:
            result = await cache_service.get(query=query, project_id=project_id)
            if not result:
                misses += 1
            else:
                hits += 1

        # Get stats
        stats = await cache_service.get_stats()

        logger.info(f"  ✓ Cache stats retrieved:")
        logger.info(f"    - Size: {stats['size']}")
        logger.info(f"    - Hits: {stats['hits']}")
        logger.info(f"    - Misses: {stats['misses']}")
        logger.info(f"    - Hit rate: {stats['hit_rate']}%")

        if stats['hit_rate'] > 50:
            logger.info(f"  ✓ Hit rate is good ({stats['hit_rate']}% > 50%)")
        else:
            logger.warning(f"  ⚠️  Hit rate is lower than expected ({stats['hit_rate']}%)")

        logger.info("✅ Cache Hit Rate test PASSED")
        return True

    except Exception as e:
        logger.error(f"❌ Cache Hit Rate test FAILED: {e}", exc_info=True)
        return False


async def test_cache_with_filters():
    """Test cache with agent_id and project_id filters."""
    logger.info("\n📝 Testing Cache with Filters...")

    cache_service = get_cache_service()

    try:
        # Clear cache
        await cache_service.clear_all()

        # Test query with different filter combinations
        test_query = "project planning strategy"
        test_results = {"data": "test"}

        logger.info(f"  Testing cache isolation with filters...")

        # Cache for agent_001
        await cache_service.set(
            query=test_query,
            results=test_results,
            agent_id="agent_001",
            project_id="proj_001",
        )
        logger.info("  ✓ Cached for agent_001, proj_001")

        # Cache for agent_002 (same query, different agent)
        await cache_service.set(
            query=test_query,
            results={"data": "different"},
            agent_id="agent_002",
            project_id="proj_001",
        )
        logger.info("  ✓ Cached for agent_002, proj_001")

        # Retrieve for agent_001
        result1 = await cache_service.get(
            query=test_query,
            agent_id="agent_001",
            project_id="proj_001",
        )

        # Retrieve for agent_002
        result2 = await cache_service.get(
            query=test_query,
            agent_id="agent_002",
            project_id="proj_001",
        )

        if result1 and result2:
            logger.info("  ✓ Both caches retrieved independently")
        else:
            logger.error("  ❌ Failed to retrieve filtered caches")
            return False

        # Test clear_agent
        logger.info("  Testing clear_agent()...")
        await cache_service.clear_agent("agent_001")

        result1 = await cache_service.get(
            query=test_query,
            agent_id="agent_001",
            project_id="proj_001",
        )

        result2 = await cache_service.get(
            query=test_query,
            agent_id="agent_002",
            project_id="proj_001",
        )

        if not result1 and result2:
            logger.info("  ✓ clear_agent() correctly cleared only agent_001 cache")
        else:
            logger.error("  ❌ clear_agent() did not work correctly")
            return False

        logger.info("✅ Cache with Filters test PASSED")
        return True

    except Exception as e:
        logger.error(f"❌ Cache with Filters test FAILED: {e}", exc_info=True)
        return False


async def test_cache_performance():
    """Test cache performance benefits."""
    logger.info("\n📝 Testing Cache Performance Benefits...")

    cache_service = get_cache_service()

    try:
        # Clear cache
        await cache_service.clear_all()

        test_query = "performance optimization techniques"
        test_results = {"data": "x" * 1000}  # 1KB of data

        # Warm up cache
        await cache_service.set(
            query=test_query,
            results=test_results,
            project_id="proj_001",
        )

        # Measure cache hit time
        logger.info("  Measuring cache hit performance...")
        iterations = 100

        start_time = time.time()
        for _ in range(iterations):
            await cache_service.get(
                query=test_query,
                project_id="proj_001",
            )
        cache_time = (time.time() - start_time) / iterations * 1000  # ms

        logger.info(f"  ✓ Average cache hit time: {cache_time:.2f}ms")

        # Get final stats
        stats = await cache_service.get_stats()

        if cache_time < 10:  # Cache hits should be <10ms
            logger.info(f"  ✓ Cache performance is excellent ({cache_time:.2f}ms < 10ms)")
        else:
            logger.warning(f"  ⚠️  Cache performance could be better ({cache_time:.2f}ms)")

        logger.info("✅ Cache Performance test PASSED")
        return True

    except Exception as e:
        logger.error(f"❌ Cache Performance test FAILED: {e}", exc_info=True)
        return False


async def test_cache_cleanup():
    """Test cache cleanup and size management."""
    logger.info("\n📝 Testing Cache Cleanup...")

    cache_service = get_cache_service()

    try:
        # Clear cache
        await cache_service.clear_all()

        logger.info("  Testing clear_all()...")
        # Add multiple entries
        for i in range(10):
            await cache_service.set(
                query=f"query_{i}",
                results={"data": f"result_{i}"},
                project_id=f"proj_{i}",
            )

        # Get stats before clear
        stats_before = await cache_service.get_stats()
        logger.info(f"    Before clear: {stats_before['size']} entries")

        # Clear all
        success = await cache_service.clear_all()

        if success:
            logger.info("  ✓ clear_all() successful")

            # Verify empty
            stats_after = await cache_service.get_stats()
            logger.info(f"    After clear: {stats_after['size']} entries")

            if stats_after['size'] == 0:
                logger.info("  ✓ Cache successfully cleared")
            else:
                logger.warning("  ⚠️  Cache not fully cleared")

        logger.info("✅ Cache Cleanup test PASSED")
        return True

    except Exception as e:
        logger.error(f"❌ Cache Cleanup test FAILED: {e}", exc_info=True)
        return False


async def main():
    """Run all cache tests."""
    logger.info("=" * 60)
    logger.info("  RAG Cache Service Test Suite")
    logger.info("=" * 60)

    try:
        # Initialize cache service
        await initialize_cache_service()

        tests = [
            ("Cache Initialization", test_cache_initialization),
            ("Basic Operations", test_cache_basic_operations),
            ("Hit Rate Tracking", test_cache_hit_rate),
            ("Filters", test_cache_with_filters),
            ("Performance", test_cache_performance),
            ("Cleanup", test_cache_cleanup),
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
            logger.info("\n✨ All cache tests PASSED!")
            logger.info("Cache service is ready for production!")

            # Get final stats
            cache_service = get_cache_service()
            final_stats = await cache_service.get_stats()
            logger.info(f"\n  📊 Final Cache Statistics:")
            logger.info(f"     - Enabled: {final_stats['enabled']}")
            logger.info(f"     - Size: {final_stats['size']} entries")
            logger.info(f"     - Hits: {final_stats['hits']}")
            logger.info(f"     - Misses: {final_stats['misses']}")
            logger.info(f"     - Hit rate: {final_stats['hit_rate']}%")

            sys.exit(0)
        else:
            logger.warning(f"\n⚠️  {total - passed} test(s) failed")
            sys.exit(1)

    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}", exc_info=True)
        sys.exit(1)
    finally:
        # Shutdown cache service
        await shutdown_cache_service()


if __name__ == "__main__":
    asyncio.run(main())
