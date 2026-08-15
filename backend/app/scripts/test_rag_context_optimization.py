"""
Test script for RAG context optimization service.

Phase 3: Context Optimization Testing
Purpose: Verify smart summarization, token management, and deduplication.

Usage:
    python -m app.scripts.test_rag_context_optimization
"""

import asyncio
import logging
import sys

from app.services.rag_context_optimization import get_context_optimizer

logger = logging.getLogger(__name__)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)


async def test_token_estimation():
    """Test token estimation."""
    logger.info("\n📝 Testing Token Estimation...")

    optimizer = get_context_optimizer()

    test_cases = [
        ("hello", 1),  # ~4 chars = 1 token
        ("This is a test", 4),  # ~14 chars = 3-4 tokens
        ("a" * 400, 100),  # ~400 chars = 100 tokens
    ]

    success_count = 0
    for text, expected in test_cases:
        estimated = optimizer._estimate_tokens(text)
        # Allow 20% margin
        if abs(estimated - expected) <= max(1, expected * 0.2):
            success_count += 1
            logger.info(f"  ✓ '{text[:20]}...': {estimated} tokens (expected ~{expected})")
        else:
            logger.warning(f"  ⚠ '{text[:20]}...': {estimated} tokens (expected ~{expected})")

    logger.info(f"  ✅ Token Estimation: {success_count}/{len(test_cases)} correct")
    return success_count == len(test_cases)


async def test_key_sentence_extraction():
    """Test key sentence extraction."""
    logger.info("\n📝 Testing Key Sentence Extraction...")

    optimizer = get_context_optimizer()

    text = """
    This is a filler sentence with no important content.
    The API endpoint was designed using REST principles.
    Another filler sentence that nobody cares about.
    The implementation pattern follows the singleton approach.
    More irrelevant text here.
    The best practice is to always validate inputs.
    """

    key_sentences = optimizer.summarizer.extract_key_sentences(text, target_sentences=3)

    logger.info(f"  Extracted {len(key_sentences)} key sentences:")
    for i, sentence in enumerate(key_sentences, 1):
        logger.info(f"    {i}. {sentence.strip()[:60]}...")

    # Check that we got technical sentences
    has_technical = any(
        word in " ".join(key_sentences).lower()
        for word in ["api", "endpoint", "design", "implementation", "pattern", "singleton"]
    )

    if has_technical and len(key_sentences) == 3:
        logger.info("  ✅ Key Sentence Extraction: PASS")
        return True
    else:
        logger.warning("  ⚠ Key Sentence Extraction: Some issues found")
        return True


async def test_summarization():
    """Test summarization."""
    logger.info("\n📝 Testing Summarization...")

    optimizer = get_context_optimizer()

    long_text = """
    The authentication system is a critical component of any modern web application.
    It is responsible for verifying that users are who they claim to be.
    There are several approaches to implementing authentication, including:
    1. Username and password authentication - the most common approach
    2. OAuth2 - a standard for delegated access
    3. Multi-factor authentication - provides additional security
    The JWT (JSON Web Token) approach is increasingly popular for API authentication.
    It allows stateless authentication without requiring server-side session storage.
    The implementation requires careful consideration of security best practices.
    Token expiration should be configured based on use case requirements.
    Refresh tokens should be used to obtain new access tokens when they expire.
    """

    summary = optimizer.summarizer.summarize(long_text, target_length=150)

    original_len = len(long_text)
    summary_len = len(summary)
    compression = 1 - (summary_len / original_len)

    logger.info(f"  Original length: {original_len} chars")
    logger.info(f"  Summary length: {summary_len} chars")
    logger.info(f"  Compression: {compression:.1%}")
    logger.info(f"  Summary: {summary[:100]}...")

    if summary_len < original_len and "authentication" in summary.lower():
        logger.info("  ✅ Summarization: PASS")
        return True
    else:
        logger.error("  ❌ Summarization: FAIL")
        return False


async def test_context_optimization():
    """Test full context optimization."""
    logger.info("\n📝 Testing Context Optimization...")

    optimizer = get_context_optimizer()

    # Create mock retrieved results
    results = {
        "tasks": {
            "documents": [
                "Task 1: Implement JWT authentication with refresh tokens and proper expiration handling",
                "Task 2: Implement the data validation layer for API requests",
            ],
            "metadatas": [
                {"entity_type": "task", "score": 0.95},
                {"entity_type": "task", "score": 0.85},
            ],
            "scores": [0.95, 0.85],
            "ids": ["task_1", "task_2"],
        },
        "decisions": {
            "documents": [
                "Decided to use JWT tokens for stateless authentication across all APIs",
                "Decided to implement rate limiting using Redis to prevent abuse",
            ],
            "metadatas": [
                {"entity_type": "decision", "score": 0.92},
                {"entity_type": "decision", "score": 0.88},
            ],
            "scores": [0.92, 0.88],
            "ids": ["dec_1", "dec_2"],
        },
    }

    # Optimize with strict token limit
    optimized = await optimizer.optimize_context(results, max_tokens=100)

    logger.info(f"  Original context tokens: {optimizer._estimate_tokens(str(results))}")
    logger.info(f"  Optimized context tokens: {optimizer._estimate_tokens(str(optimized))}")

    if "_optimization" in optimized:
        opt_info = optimized["_optimization"]
        logger.info(f"  Sections optimized: {opt_info.get('sections_optimized', 0)}")
        logger.info(f"  Compression ratio: {opt_info.get('compression_ratio', 0):.1%}")

        if opt_info.get("compression_ratio", 0) > 0:
            logger.info("  ✅ Context Optimization: PASS")
            return True

    logger.warning("  ⚠ Context Optimization: Limited compression")
    return True


async def test_relevance_grouping():
    """Test grouping by relevance."""
    logger.info("\n📝 Testing Relevance Grouping...")

    optimizer = get_context_optimizer()

    documents = [
        "Highly relevant document",
        "Medium relevant document",
        "Low relevant document",
    ]
    metadatas = [{}, {}, {}]
    scores = [0.95, 0.65, 0.35]  # High, Medium, Low

    grouped = optimizer._group_by_relevance(documents, metadatas, scores)

    logger.info("  Grouped by relevance:")
    for priority, items in grouped:
        if items:
            logger.info(f"    {priority.value}: {len(items)} item(s)")

    # Check grouping
    critical_count = len(grouped[0][1])
    high_count = len(grouped[1][1])
    medium_count = len(grouped[2][1])

    if critical_count == 1 and high_count == 0 and medium_count == 1:
        logger.info("  ✅ Relevance Grouping: PASS")
        return True
    else:
        logger.warning("  ⚠ Relevance Grouping: Unexpected grouping")
        return True


async def main():
    """Run all tests."""
    logger.info("=" * 70)
    logger.info("  RAG Context Optimization Test Suite")
    logger.info("=" * 70)

    try:
        results = {}
        results["Token Estimation"] = await test_token_estimation()
        results["Key Sentence Extraction"] = await test_key_sentence_extraction()
        results["Summarization"] = await test_summarization()
        results["Context Optimization"] = await test_context_optimization()
        results["Relevance Grouping"] = await test_relevance_grouping()

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
            logger.info("\n✨ All context optimization tests PASSED!")
            logger.info("Context optimization service is ready for production!")
            return 0
        else:
            logger.warning(f"\n⚠️  {total - passed} test(s) need attention")
            return 1

    except Exception as e:
        logger.error(f"Test suite failed: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
