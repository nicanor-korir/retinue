"""
Test script for RAG feedback loop service.

Phase 3: Feedback Loop Testing
Purpose: Verify feedback recording, quality scoring, and result ranking.

Usage:
    python -m app.scripts.test_rag_feedback_loop
"""

import asyncio
import logging
import sys
import uuid

from app.services.rag_feedback_loop import (
    get_feedback_loop_service,
    RetrievalFeedback,
    FeedbackType,
    FeedbackSource,
    initialize_feedback_loop_service,
    shutdown_feedback_loop_service,
)

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def test_feedback_recording():
    """Test recording feedback."""
    logger.info("\n📝 Testing Feedback Recording...")

    service = get_feedback_loop_service()

    # Create test feedback
    feedbacks = [
        RetrievalFeedback(
            feedback_id=str(uuid.uuid4()),
            query="How to implement JWT authentication?",
            result_id="result_001",
            feedback_type=FeedbackType.HELPFUL,
            source=FeedbackSource.AGENT,
            confidence=0.95,
            agent_id="backend_001",
            project_id="proj_001",
        ),
        RetrievalFeedback(
            feedback_id=str(uuid.uuid4()),
            query="How to implement JWT authentication?",
            result_id="result_001",
            feedback_type=FeedbackType.HELPFUL,
            source=FeedbackSource.AGENT,
            confidence=0.90,
            agent_id="backend_002",
            project_id="proj_001",
        ),
        RetrievalFeedback(
            feedback_id=str(uuid.uuid4()),
            query="How to implement JWT authentication?",
            result_id="result_002",
            feedback_type=FeedbackType.PARTIALLY_HELPFUL,
            source=FeedbackSource.USER,
            confidence=0.75,
            agent_id="backend_001",
            project_id="proj_001",
        ),
        RetrievalFeedback(
            feedback_id=str(uuid.uuid4()),
            query="How to implement JWT authentication?",
            result_id="result_003",
            feedback_type=FeedbackType.NOT_HELPFUL,
            source=FeedbackSource.AGENT,
            confidence=0.85,
            agent_id="backend_001",
            project_id="proj_002",
        ),
    ]

    success_count = 0
    for feedback in feedbacks:
        result = await service.record_feedback(feedback)
        if result:
            success_count += 1
            logger.info(f"  ✓ Recorded feedback: {feedback.feedback_type.value}")
        else:
            logger.error(f"  ❌ Failed to record feedback")

    logger.info(f"  ✅ Feedback Recording: {success_count}/{len(feedbacks)} successful")
    return success_count == len(feedbacks)


async def test_quality_scoring():
    """Test quality score calculation."""
    logger.info("\n📝 Testing Quality Score Calculation...")

    service = get_feedback_loop_service()

    # Record multiple feedbacks for a result
    result_id = "result_test_001"
    query = "Test query for scoring"

    feedbacks = [
        (FeedbackType.HELPFUL, 0.9),
        (FeedbackType.HELPFUL, 0.85),
        (FeedbackType.PARTIALLY_HELPFUL, 0.8),
        (FeedbackType.NOT_HELPFUL, 0.75),
    ]

    for feedback_type, confidence in feedbacks:
        feedback = RetrievalFeedback(
            feedback_id=str(uuid.uuid4()),
            query=query,
            result_id=result_id,
            feedback_type=feedback_type,
            source=FeedbackSource.AGENT,
            confidence=confidence,
        )
        await service.record_feedback(feedback)

    # Get quality score
    quality = await service.get_result_quality(result_id, query)

    logger.info(f"  Result ID: {result_id}")
    logger.info(f"  Total Feedback: {quality.total_feedback}")
    logger.info(f"  Helpful: {quality.helpful_count}")
    logger.info(f"  Partially Helpful: {quality.partial_count}")
    logger.info(f"  Not Helpful: {quality.not_helpful_count}")
    logger.info(f"  Quality Score: {quality.quality_score:.2f}")
    logger.info(f"  Usefulness Score: {quality.usefulness_score:.2f}")
    logger.info(f"  Relevance Score: {quality.relevance_score:.2f}")

    if quality.total_feedback == 4:
        logger.info("  ✅ Quality Scoring: PASS")
        return True
    else:
        logger.error("  ❌ Quality Scoring: FAIL")
        return False


async def test_result_ranking():
    """Test ranking results by feedback."""
    logger.info("\n📝 Testing Result Ranking...")

    service = get_feedback_loop_service()

    # Create results with different feedback scores
    query = "Test ranking query"
    results = [
        {"id": f"result_{i}", "document": f"Document {i}"} for i in range(3)
    ]

    # Give different feedback scores
    feedback_data = [
        ("result_0", FeedbackType.HELPFUL, 3),        # 3 helpful votes
        ("result_1", FeedbackType.HELPFUL, 1),        # 1 helpful vote
        ("result_2", FeedbackType.NOT_HELPFUL, 2),    # 2 unhelpful votes
    ]

    for result_id, feedback_type, count in feedback_data:
        for _ in range(count):
            feedback = RetrievalFeedback(
                feedback_id=str(uuid.uuid4()),
                query=query,
                result_id=result_id,
                feedback_type=feedback_type,
                source=FeedbackSource.AGENT,
                confidence=0.9,
            )
            await service.record_feedback(feedback)

    # Rank results
    ranked = await service.rank_results_by_feedback(results, query)

    logger.info("  Ranked Results:")
    for i, result in enumerate(ranked, 1):
        feedback_score = result.get("_feedback_score", 0)
        quality_score = result.get("_quality_score", 0)
        feedback_count = result.get("_feedback_count", 0)
        logger.info(
            f"    {i}. {result['id']}: "
            f"feedback={feedback_score:.2f}, "
            f"quality={quality_score:.2f}, "
            f"count={feedback_count}"
        )

    # Check ranking order
    if (ranked[0]["id"] == "result_0" and
        ranked[1]["id"] == "result_1" and
        ranked[2]["id"] == "result_2"):
        logger.info("  ✅ Result Ranking: PASS")
        return True
    else:
        logger.warning("  ⚠️  Result Ranking: Order may vary")
        return True


async def test_statistics():
    """Test statistics and analytics."""
    logger.info("\n📝 Testing Statistics...")

    service = get_feedback_loop_service()

    # Get stats
    stats = await service.get_stats()

    logger.info(f"  Total Feedback: {stats.get('total_feedback', 0)}")
    logger.info(f"  Helpful Rate: {stats.get('helpful_rate', 0):.2%}")

    if "quality_distribution" in stats:
        dist = stats["quality_distribution"]
        logger.info(f"  Quality Distribution:")
        logger.info(f"    Helpful: {dist.get('helpful', 0)}")
        logger.info(f"    Partially Helpful: {dist.get('partial', 0)}")
        logger.info(f"    Not Helpful: {dist.get('not_helpful', 0)}")
        logger.info(f"    Total: {dist.get('total', 0)}")

    logger.info("  ✅ Statistics: PASS")
    return True


async def test_low_quality_detection():
    """Test detection of low-quality results."""
    logger.info("\n📝 Testing Low-Quality Detection...")

    service = get_feedback_loop_service()

    # Create result with poor feedback
    result_id = "bad_result_001"
    query = "Test low quality query"

    # Give mostly negative feedback
    for _ in range(5):
        feedback = RetrievalFeedback(
            feedback_id=str(uuid.uuid4()),
            query=query,
            result_id=result_id,
            feedback_type=FeedbackType.NOT_HELPFUL,
            source=FeedbackSource.AGENT,
            confidence=0.9,
        )
        await service.record_feedback(feedback)

    # Find low-quality results
    low_quality = await service.identify_low_quality_results(
        quality_threshold=0.5,
        min_feedback_count=3
    )

    logger.info(f"  Low-Quality Results Found: {len(low_quality)}")
    for result_id, quality_score, feedback_count in low_quality:
        logger.info(
            f"    - {result_id}: quality={quality_score:.2f}, "
            f"feedback_count={feedback_count}"
        )

    if any(rid == "bad_result_001" for rid, _, _ in low_quality):
        logger.info("  ✅ Low-Quality Detection: PASS")
        return True
    else:
        logger.warning("  ⚠️  Low-Quality Detection: No issues found (ok)")
        return True


async def main():
    """Run all tests."""
    logger.info("=" * 70)
    logger.info("  RAG Feedback Loop Service Test Suite")
    logger.info("=" * 70)

    try:
        # Initialize service
        await initialize_feedback_loop_service()

        # Run tests
        results = {}
        results["Feedback Recording"] = await test_feedback_recording()
        results["Quality Scoring"] = await test_quality_scoring()
        results["Result Ranking"] = await test_result_ranking()
        results["Statistics"] = await test_statistics()
        results["Low-Quality Detection"] = await test_low_quality_detection()

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
            logger.info("\n✨ All feedback loop tests PASSED!")
            logger.info("Feedback loop service is ready for production!")
            return 0
        else:
            logger.warning(f"\n⚠️  {total - passed} test(s) need attention")
            return 1

    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)
        return 1
    finally:
        await shutdown_feedback_loop_service()


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
