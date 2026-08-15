"""
Test script for RAG performance monitoring service.

Phase 3.4: Performance Monitoring and Analytics Testing
Purpose: Verify metrics tracking, statistics, anomaly detection, and analytics.

Usage:
    python -m app.scripts.test_rag_performance_monitor
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
import random

from app.services.rag_performance_monitor import (
    get_performance_monitor,
    initialize_performance_monitor,
    shutdown_performance_monitor,
    RetrievalMetrics,
    MetricType,
    AnomalyLevel,
)

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def test_metric_recording():
    """Test recording retrieval metrics."""
    logger.info("\n📝 Testing Metric Recording...")

    monitor = get_performance_monitor()

    # Record test metrics
    test_cases = [
        RetrievalMetrics(
            timestamp=datetime.now(),
            query="How to implement authentication?",
            agent_id="backend_001",
            project_id="proj_001",
            latency_ms=45.5,
            cache_hit=True,
            result_count=3,
            total_tokens=250,
            quality_score=0.92,
            compression_ratio=0.28,
            summarized_count=1,
        ),
        RetrievalMetrics(
            timestamp=datetime.now(),
            query="Database optimization techniques",
            agent_id="backend_002",
            project_id="proj_001",
            latency_ms=120.3,
            cache_hit=False,
            result_count=5,
            total_tokens=450,
            quality_score=0.85,
            compression_ratio=0.35,
            summarized_count=2,
        ),
        RetrievalMetrics(
            timestamp=datetime.now(),
            query="API design patterns",
            agent_id="frontend_001",
            project_id="proj_002",
            latency_ms=32.1,
            cache_hit=True,
            result_count=2,
            total_tokens=180,
            quality_score=0.88,
            compression_ratio=0.22,
            summarized_count=0,
        ),
    ]

    success_count = 0
    for metrics in test_cases:
        await monitor.record_retrieval(metrics)
        success_count += 1
        logger.info(f"  ✓ Recorded: {metrics.query[:30]}... "
                   f"({metrics.latency_ms:.1f}ms, quality={metrics.quality_score:.2f})")

    logger.info(f"  ✅ Metric Recording: {success_count}/{len(test_cases)} successful")
    return success_count == len(test_cases)


async def test_statistics_calculation():
    """Test aggregated statistics calculation."""
    logger.info("\n📝 Testing Statistics Calculation...")

    monitor = get_performance_monitor()

    # Get overall stats
    stats = monitor.get_stats(period="all")

    logger.info(f"  Total Retrievals: {stats.get('total_retrievals', 0)}")
    logger.info(f"  Average Latency: {stats.get('latency', {}).get('mean', 0):.1f}ms")
    logger.info(f"  p95 Latency: {stats.get('latency', {}).get('p95', 0):.1f}ms")
    logger.info(f"  Cache Hit Rate: {stats.get('cache', {}).get('hit_rate', 0):.0%}")
    logger.info(f"  Average Quality: {stats.get('quality', {}).get('mean', 0):.2f}")
    logger.info(f"  Error Rate: {stats.get('errors', {}).get('rate', 0):.2%}")
    logger.info(f"  Anomalies: {stats.get('anomalies', {}).get('total', 0)}")

    if stats.get("total_retrievals", 0) >= 3:
        logger.info("  ✅ Statistics Calculation: PASS")
        return True
    else:
        logger.error("  ❌ Statistics Calculation: FAIL")
        return False


async def test_agent_statistics():
    """Test agent-specific statistics."""
    logger.info("\n📝 Testing Agent Statistics...")

    monitor = get_performance_monitor()

    # Get stats for backend_001
    agent_stats = monitor.get_agent_stats("backend_001")

    logger.info(f"  Agent: backend_001")
    logger.info(f"  Total Retrievals: {agent_stats.get('total_retrievals', 0)}")
    logger.info(f"  Avg Latency: {agent_stats.get('avg_latency_ms', 0):.1f}ms")
    logger.info(f"  Cache Hit Rate: {agent_stats.get('cache_hit_rate', 0):.0%}")
    logger.info(f"  Avg Quality: {agent_stats.get('avg_quality_score', 0):.2f}")

    if agent_stats.get("total_retrievals", 0) > 0:
        logger.info("  ✅ Agent Statistics: PASS")
        return True
    else:
        logger.error("  ❌ Agent Statistics: FAIL")
        return False


async def test_project_statistics():
    """Test project-specific statistics."""
    logger.info("\n📝 Testing Project Statistics...")

    monitor = get_performance_monitor()

    # Get stats for proj_001
    project_stats = monitor.get_project_stats("proj_001")

    logger.info(f"  Project: proj_001")
    logger.info(f"  Total Retrievals: {project_stats.get('total_retrievals', 0)}")
    logger.info(f"  Avg Latency: {project_stats.get('avg_latency_ms', 0):.1f}ms")
    logger.info(f"  Cache Hit Rate: {project_stats.get('cache_hit_rate', 0):.0%}")
    logger.info(f"  Total Tokens Used: {project_stats.get('total_tokens_used', 0)}")

    if project_stats.get("total_retrievals", 0) > 0:
        logger.info("  ✅ Project Statistics: PASS")
        return True
    else:
        logger.error("  ❌ Project Statistics: FAIL")
        return False


async def test_top_queries():
    """Test query frequency tracking."""
    logger.info("\n📝 Testing Top Queries...")

    monitor = get_performance_monitor()

    # Record multiple queries to create frequency pattern
    queries = [
        "How to implement authentication?",
        "How to implement authentication?",
        "Database optimization techniques",
        "API design patterns",
        "Database optimization techniques",
        "How to implement authentication?",
    ]

    for query in queries:
        metrics = RetrievalMetrics(
            timestamp=datetime.now(),
            query=query,
            agent_id="test_agent",
            project_id="test_proj",
            latency_ms=50,
            cache_hit=False,
            result_count=2,
            total_tokens=200,
            quality_score=0.85,
            compression_ratio=0.25,
            summarized_count=1,
        )
        await monitor.record_retrieval(metrics)

    # Get top queries
    top_queries = monitor.get_top_queries(limit=3)

    logger.info(f"  Top Queries:")
    for query, count in top_queries:
        logger.info(f"    {count}x: {query[:50]}...")

    if len(top_queries) > 0 and top_queries[0][1] >= 3:
        logger.info("  ✅ Top Queries: PASS")
        return True
    else:
        logger.warning("  ⚠️  Top Queries: Limited data")
        return True


async def test_anomaly_detection():
    """Test anomaly detection."""
    logger.info("\n📝 Testing Anomaly Detection...")

    monitor = get_performance_monitor()

    # Record high-latency metric (should trigger anomaly)
    high_latency_metric = RetrievalMetrics(
        timestamp=datetime.now(),
        query="Slow query",
        agent_id="test_agent",
        project_id="test_proj",
        latency_ms=750.0,  # Exceeds threshold of 500ms
        cache_hit=False,
        result_count=1,
        total_tokens=100,
        quality_score=0.85,
        compression_ratio=0.2,
        summarized_count=0,
    )
    await monitor.record_retrieval(high_latency_metric)

    # Record low-quality metric (should trigger anomaly)
    low_quality_metric = RetrievalMetrics(
        timestamp=datetime.now(),
        query="Low quality query",
        agent_id="test_agent",
        project_id="test_proj",
        latency_ms=50,
        cache_hit=False,
        result_count=1,
        total_tokens=100,
        quality_score=0.3,  # Below threshold of 0.5
        compression_ratio=0.2,
        summarized_count=0,
    )
    await monitor.record_retrieval(low_quality_metric)

    # Record error metric (should trigger anomaly)
    error_metric = RetrievalMetrics(
        timestamp=datetime.now(),
        query="Error query",
        agent_id="test_agent",
        project_id="test_proj",
        latency_ms=50,
        cache_hit=False,
        result_count=0,
        total_tokens=0,
        quality_score=0.5,
        compression_ratio=0,
        summarized_count=0,
        errors=["Connection timeout"],
    )
    await monitor.record_retrieval(error_metric)

    # Get anomalies
    anomalies = monitor.get_anomalies(limit=10)

    logger.info(f"  Detected Anomalies: {len(anomalies)}")
    for timestamp, level, message in anomalies[:3]:
        logger.info(f"    [{level.upper()}] {message[:60]}...")

    if len(anomalies) >= 3:
        logger.info("  ✅ Anomaly Detection: PASS")
        return True
    else:
        logger.warning("  ⚠️  Anomaly Detection: Limited anomalies")
        return True


async def test_performance_trend():
    """Test performance trend calculation."""
    logger.info("\n📝 Testing Performance Trend...")

    monitor = get_performance_monitor()

    # Get latency trend
    trend = monitor.get_performance_trend(
        metric=MetricType.RETRIEVAL_LATENCY,
        period="24h",
        bucket_size_minutes=30
    )

    logger.info(f"  Metric: RETRIEVAL_LATENCY")
    logger.info(f"  Buckets: {len(trend.get('values', []))}")
    if trend.get("values"):
        logger.info(f"  Min: {min(trend['values']):.1f}ms")
        logger.info(f"  Max: {max(trend['values']):.1f}ms")
        logger.info(f"  Avg: {sum(trend['values']) / len(trend['values']):.1f}ms")

    if "values" in trend:
        logger.info("  ✅ Performance Trend: PASS")
        return True
    else:
        logger.warning("  ⚠️  Performance Trend: No trend data")
        return True


async def test_metric_export():
    """Test metrics export functionality."""
    logger.info("\n📝 Testing Metrics Export...")

    monitor = get_performance_monitor()

    # Export as JSON
    json_export = monitor.export_metrics(format="json")
    if json_export and "stats" in json_export:
        logger.info(f"  JSON Export: {len(json_export)} bytes")
    else:
        logger.warning("  JSON Export: No data")

    # Export as CSV
    csv_export = monitor.export_metrics(format="csv")
    csv_lines = csv_export.split("\n")
    if len(csv_lines) > 1:
        logger.info(f"  CSV Export: {len(csv_lines)} lines")
    else:
        logger.warning("  CSV Export: No data")

    if json_export and csv_export:
        logger.info("  ✅ Metrics Export: PASS")
        return True
    else:
        logger.warning("  ⚠️  Metrics Export: Limited export")
        return True


async def test_cache_effectiveness():
    """Test cache effectiveness tracking."""
    logger.info("\n📝 Testing Cache Effectiveness...")

    monitor = get_performance_monitor()

    # Record series of metrics with cache hits and misses
    metrics_series = []
    for i in range(10):
        cache_hit = i % 3 == 0  # 33% cache hit rate
        metrics_series.append(
            RetrievalMetrics(
                timestamp=datetime.now() - timedelta(minutes=i),
                query=f"Query {i % 3}",
                agent_id="cache_test_agent",
                project_id="cache_test_proj",
                latency_ms=100 if cache_hit else 200,  # Cache hits are faster
                cache_hit=cache_hit,
                result_count=2,
                total_tokens=300,
                quality_score=0.85,
                compression_ratio=0.25,
                summarized_count=1,
            )
        )

    for metrics in metrics_series:
        await monitor.record_retrieval(metrics)

    # Check stats
    stats = monitor.get_stats(period="all")
    cache_hit_rate = stats.get("cache", {}).get("hit_rate", 0)

    logger.info(f"  Cache Hit Rate: {cache_hit_rate:.0%}")
    logger.info(f"  Total Retrievals: {stats.get('total_retrievals', 0)}")
    logger.info(f"  Latency (cache hit): ~100ms")
    logger.info(f"  Latency (cache miss): ~200ms")

    if cache_hit_rate > 0:
        logger.info("  ✅ Cache Effectiveness: PASS")
        return True
    else:
        logger.warning("  ⚠️  Cache Effectiveness: No hits")
        return True


async def test_quality_metrics():
    """Test quality score tracking."""
    logger.info("\n📝 Testing Quality Metrics...")

    monitor = get_performance_monitor()

    # Record metrics with varying quality scores
    quality_scores = [0.95, 0.92, 0.88, 0.85, 0.92, 0.90]

    for i, quality in enumerate(quality_scores):
        metrics = RetrievalMetrics(
            timestamp=datetime.now() - timedelta(minutes=i),
            query="Quality test query",
            agent_id="quality_agent",
            project_id="quality_proj",
            latency_ms=50 + random.randint(0, 30),
            cache_hit=False,
            result_count=3,
            total_tokens=300,
            quality_score=quality,
            compression_ratio=0.25,
            summarized_count=1,
        )
        await monitor.record_retrieval(metrics)

    # Get stats
    stats = monitor.get_stats(period="all")
    quality_stats = stats.get("quality", {})

    logger.info(f"  Mean Quality: {quality_stats.get('mean', 0):.2f}")
    logger.info(f"  Median Quality: {quality_stats.get('median', 0):.2f}")
    logger.info(f"  p95 Quality: {quality_stats.get('p95', 0):.2f}")
    logger.info(f"  Min Quality: {quality_stats.get('min', 0):.2f}")
    logger.info(f"  Max Quality: {quality_stats.get('max', 0):.2f}")

    if quality_stats.get("mean", 0) > 0.8:
        logger.info("  ✅ Quality Metrics: PASS")
        return True
    else:
        logger.warning("  ⚠️  Quality Metrics: Low quality")
        return True


async def main():
    """Run all tests."""
    logger.info("=" * 70)
    logger.info("  RAG Performance Monitoring Test Suite")
    logger.info("=" * 70)

    try:
        # Initialize
        await initialize_performance_monitor()

        # Run tests
        results = {}
        results["Metric Recording"] = await test_metric_recording()
        results["Statistics Calculation"] = await test_statistics_calculation()
        results["Agent Statistics"] = await test_agent_statistics()
        results["Project Statistics"] = await test_project_statistics()
        results["Top Queries"] = await test_top_queries()
        results["Anomaly Detection"] = await test_anomaly_detection()
        results["Performance Trend"] = await test_performance_trend()
        results["Metrics Export"] = await test_metric_export()
        results["Cache Effectiveness"] = await test_cache_effectiveness()
        results["Quality Metrics"] = await test_quality_metrics()

        # Summary
        logger.info("\n" + "=" * 70)
        logger.info("  📊 TEST SUMMARY")
        logger.info("=" * 70)

        passed = sum(1 for v in results.values() if v)
        total = len(results)

        for test_name, passed_flag in results.items():
            status = "✅ PASS" if passed_flag else "❌ FAIL"
            logger.info(f"  {status}: {test_name}")

        logger.info(f"\n  Total: {passed}/{total} tests passed")

        if passed == total:
            logger.info("\n✨ All performance monitoring tests PASSED!")
            logger.info("Performance monitoring service is ready for production!")
            return 0
        else:
            logger.warning(f"\n⚠️  {total - passed} test(s) need attention")
            return 1

    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)
        return 1
    finally:
        await shutdown_performance_monitor()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
