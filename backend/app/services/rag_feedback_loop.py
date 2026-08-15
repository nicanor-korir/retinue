"""
Feedback loop system for RAG optimization (Phase 3).

Purpose: Learn from retrieval quality feedback to:
1. Rank results based on previous feedback
2. Calculate quality scores over time
3. Improve relevance through user/agent feedback
4. Track which results were most useful
5. Identify and remove low-quality retrievals
"""

import logging
import json
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import redis.asyncio as redis

logger = logging.getLogger(__name__)


class FeedbackType(str, Enum):
    """Types of feedback on retrieval results."""
    HELPFUL = "helpful"          # Result was useful
    PARTIALLY_HELPFUL = "partial"  # Some information was useful
    NOT_HELPFUL = "not_helpful"  # Result was not relevant
    INCORRECT = "incorrect"      # Result contained wrong info
    DUPLICATE = "duplicate"      # Result was duplicate of another
    MISSING = "missing"          # Information was missing from results


class FeedbackSource(str, Enum):
    """Source of feedback."""
    AGENT = "agent"           # AI agent evaluation
    USER = "user"             # Human user feedback
    SYSTEM = "system"         # Automatic quality check


@dataclass
class RetrievalFeedback:
    """Feedback on a retrieval result."""
    feedback_id: str
    query: str
    result_id: str          # ID of the retrieved result
    feedback_type: FeedbackType
    source: FeedbackSource
    confidence: float       # How confident is this feedback (0-1)
    notes: Optional[str] = None
    agent_id: Optional[str] = None
    project_id: Optional[str] = None
    timestamp: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        data = asdict(self)
        data["feedback_type"] = self.feedback_type.value
        data["source"] = self.source.value
        if self.timestamp:
            data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class ResultQualityScore:
    """Quality score for a result."""
    result_id: str
    query: str
    helpful_count: int = 0
    partial_count: int = 0
    not_helpful_count: int = 0
    incorrect_count: int = 0
    duplicate_count: int = 0
    total_feedback: int = 0
    quality_score: float = 0.5  # 0-1
    relevance_score: float = 0.5  # 0-1
    usefulness_score: float = 0.5  # 0-1
    last_updated: Optional[datetime] = None


class FeedbackLoopService:
    """
    Service for managing RAG result feedback and learning from it.

    Features:
    - Record feedback on retrieval results
    - Calculate quality scores
    - Rank results based on historical feedback
    - Identify low-quality results
    - Track feedback trends
    """

    def __init__(self, redis_url: str = "redis://localhost:6379"):
        """Initialize the feedback loop service."""
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.prefix = "rag:feedback"
        self.enabled = True

    async def initialize(self) -> None:
        """Initialize Redis connection."""
        try:
            self.redis = await redis.from_url(
                self.redis_url,
                encoding="utf8",
                decode_responses=True,
                socket_connect_timeout=5,
            )
            await self.redis.ping()
            logger.info("✅ Feedback Loop Service initialized (Redis connected)")
        except Exception as e:
            logger.warning(f"⚠️  Failed to initialize feedback loop: {e}")
            self.redis = None
            self.enabled = False

    async def shutdown(self) -> None:
        """Shutdown Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("✅ Feedback Loop Service shutdown")

    async def record_feedback(
        self,
        feedback: RetrievalFeedback,
    ) -> bool:
        """
        Record feedback on a retrieval result.

        Args:
            feedback: Feedback data

        Returns:
            True if recorded successfully
        """
        if not self.enabled or not self.redis:
            return False

        try:
            # Set timestamp if not provided
            if not feedback.timestamp:
                feedback.timestamp = datetime.utcnow()

            # Store feedback
            feedback_key = f"{self.prefix}:feedback:{feedback.feedback_id}"
            await self.redis.setex(
                feedback_key,
                86400 * 30,  # 30 days retention
                json.dumps(feedback.to_dict(), default=str)
            )

            # Update result quality scores
            await self._update_quality_scores(feedback)

            # Record feedback for analytics
            await self._record_analytics(feedback)

            logger.debug(f"Recorded feedback: {feedback.feedback_id}")
            return True

        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
            return False

    async def get_result_quality(
        self,
        result_id: str,
        query: str,
    ) -> ResultQualityScore:
        """
        Get quality score for a result.

        Args:
            result_id: ID of the result
            query: Query the result was retrieved for

        Returns:
            Quality score data
        """
        if not self.enabled or not self.redis:
            return ResultQualityScore(result_id=result_id, query=query)

        try:
            quality_key = f"{self.prefix}:quality:{result_id}"
            data = await self.redis.get(quality_key)

            if data:
                score_dict = json.loads(data)
                return ResultQualityScore(**score_dict)
            else:
                return ResultQualityScore(result_id=result_id, query=query)

        except Exception as e:
            logger.error(f"Error getting quality score: {e}")
            return ResultQualityScore(result_id=result_id, query=query)

    async def rank_results_by_feedback(
        self,
        results: List[Dict[str, Any]],
        query: str,
    ) -> List[Dict[str, Any]]:
        """
        Re-rank results based on feedback history.

        Args:
            results: List of retrieved results
            query: Original query

        Returns:
            Ranked results with feedback scores
        """
        if not self.enabled:
            return results

        try:
            # Get quality scores for each result
            scored_results = []

            for result in results:
                result_id = result.get("id") or result.get("_id")
                if not result_id:
                    continue

                quality = await self.get_result_quality(result_id, query)

                scored_results.append({
                    **result,
                    "_feedback_score": quality.usefulness_score,
                    "_quality_score": quality.quality_score,
                    "_feedback_count": quality.total_feedback,
                })

            # Sort by feedback score (highest first)
            ranked = sorted(
                scored_results,
                key=lambda x: (x["_feedback_count"] > 0, x["_feedback_score"]),
                reverse=True
            )

            logger.debug(f"Ranked {len(ranked)} results based on feedback")
            return ranked

        except Exception as e:
            logger.error(f"Error ranking results: {e}")
            return results

    async def _update_quality_scores(
        self,
        feedback: RetrievalFeedback,
    ) -> None:
        """Update quality scores based on feedback."""
        try:
            result_id = feedback.result_id
            quality_key = f"{self.prefix}:quality:{result_id}"

            # Get current quality score
            data = await self.redis.get(quality_key)
            if data:
                score_dict = json.loads(data)
                quality = ResultQualityScore(**score_dict)
            else:
                quality = ResultQualityScore(
                    result_id=result_id,
                    query=feedback.query
                )

            # Update counts based on feedback type
            if feedback.feedback_type == FeedbackType.HELPFUL:
                quality.helpful_count += 1
            elif feedback.feedback_type == FeedbackType.PARTIALLY_HELPFUL:
                quality.partial_count += 1
            elif feedback.feedback_type == FeedbackType.NOT_HELPFUL:
                quality.not_helpful_count += 1
            elif feedback.feedback_type == FeedbackType.INCORRECT:
                quality.incorrect_count += 1
            elif feedback.feedback_type == FeedbackType.DUPLICATE:
                quality.duplicate_count += 1

            quality.total_feedback += 1
            quality.last_updated = datetime.utcnow()

            # Calculate quality score (0-1)
            # Formula: (helpful + 0.5*partial - incorrect - duplicate) / total
            quality.quality_score = max(0, min(1, (
                quality.helpful_count +
                0.5 * quality.partial_count -
                quality.incorrect_count -
                quality.duplicate_count
            ) / quality.total_feedback))

            # Calculate usefulness score
            # Formula: (helpful + 0.5*partial) / total
            quality.usefulness_score = (
                quality.helpful_count +
                0.5 * quality.partial_count
            ) / quality.total_feedback

            # Calculate relevance score
            # Formula: 1 - (not_helpful + 0.5*partial) / total
            quality.relevance_score = max(0, min(1, 1 - (
                quality.not_helpful_count +
                0.5 * quality.partial_count
            ) / quality.total_feedback))

            # Store updated score
            quality_data = asdict(quality)
            quality_data["last_updated"] = quality.last_updated.isoformat()
            await self.redis.setex(
                quality_key,
                86400 * 365,  # 1 year retention
                json.dumps(quality_data, default=str)
            )

        except Exception as e:
            logger.error(f"Error updating quality scores: {e}")

    async def _record_analytics(
        self,
        feedback: RetrievalFeedback,
    ) -> None:
        """Record feedback for analytics."""
        try:
            # Record feedback count
            feedback_count_key = f"{self.prefix}:analytics:feedback_count"
            await self.redis.incr(feedback_count_key)

            # Record feedback type count
            type_key = f"{self.prefix}:analytics:type:{feedback.feedback_type.value}"
            await self.redis.incr(type_key)

            # Record source count
            source_key = f"{self.prefix}:analytics:source:{feedback.source.value}"
            await self.redis.incr(source_key)

            # Record by project if available
            if feedback.project_id:
                project_key = f"{self.prefix}:analytics:project:{feedback.project_id}"
                await self.redis.incr(project_key)

            # Record by agent if available
            if feedback.agent_id:
                agent_key = f"{self.prefix}:analytics:agent:{feedback.agent_id}"
                await self.redis.incr(agent_key)

        except Exception as e:
            logger.error(f"Error recording analytics: {e}")

    async def get_quality_distribution(self) -> Dict[str, Any]:
        """Get distribution of feedback types."""
        if not self.enabled or not self.redis:
            return {}

        try:
            distribution = {}

            for feedback_type in FeedbackType:
                type_key = f"{self.prefix}:analytics:type:{feedback_type.value}"
                count = await self.redis.get(type_key)
                distribution[feedback_type.value] = int(count or 0)

            total = await self.redis.get(f"{self.prefix}:analytics:feedback_count")
            distribution["total"] = int(total or 0)

            return distribution

        except Exception as e:
            logger.error(f"Error getting quality distribution: {e}")
            return {}

    async def get_source_distribution(self) -> Dict[str, int]:
        """Get distribution of feedback sources."""
        if not self.enabled or not self.redis:
            return {}

        try:
            distribution = {}

            for source in FeedbackSource:
                source_key = f"{self.prefix}:analytics:source:{source.value}"
                count = await self.redis.get(source_key)
                distribution[source.value] = int(count or 0)

            return distribution

        except Exception as e:
            logger.error(f"Error getting source distribution: {e}")
            return {}

    async def get_stats(self) -> Dict[str, Any]:
        """Get feedback loop statistics."""
        if not self.enabled or not self.redis:
            return {"enabled": False}

        try:
            quality_dist = await self.get_quality_distribution()
            source_dist = await self.get_source_distribution()

            total_feedback = quality_dist.get("total", 0)
            helpful = quality_dist.get("helpful", 0)

            return {
                "enabled": True,
                "total_feedback": total_feedback,
                "helpful_rate": helpful / total_feedback if total_feedback > 0 else 0,
                "quality_distribution": quality_dist,
                "source_distribution": source_dist,
            }

        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {"enabled": False, "error": str(e)}

    async def identify_low_quality_results(
        self,
        quality_threshold: float = 0.4,
        min_feedback_count: int = 3,
    ) -> List[Tuple[str, float, int]]:
        """
        Identify results that consistently receive poor feedback.

        Args:
            quality_threshold: Quality score below which to flag (0-1)
            min_feedback_count: Minimum feedback count before flagging

        Returns:
            List of (result_id, quality_score, feedback_count)
        """
        if not self.enabled or not self.redis:
            return []

        try:
            low_quality = []

            # Scan all quality keys
            pattern = f"{self.prefix}:quality:*"
            cursor = 0

            while True:
                cursor, keys = await self.redis.scan(
                    cursor, match=pattern, count=100
                )

                for key in keys:
                    data = await self.redis.get(key)
                    if not data:
                        continue

                    score_dict = json.loads(data)
                    quality = ResultQualityScore(**score_dict)

                    # Check criteria
                    if (quality.quality_score < quality_threshold and
                        quality.total_feedback >= min_feedback_count):
                        low_quality.append((
                            quality.result_id,
                            quality.quality_score,
                            quality.total_feedback
                        ))

                if cursor == 0:
                    break

            return sorted(low_quality, key=lambda x: x[1])

        except Exception as e:
            logger.error(f"Error identifying low quality results: {e}")
            return []

    async def clear_feedback(self, days_old: int = 90) -> int:
        """
        Clear old feedback records.

        Args:
            days_old: Clear feedback older than this many days

        Returns:
            Number of records cleared
        """
        if not self.enabled or not self.redis:
            return 0

        try:
            cleared = 0
            pattern = f"{self.prefix}:feedback:*"
            cutoff_time = datetime.utcnow() - timedelta(days=days_old)

            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(
                    cursor, match=pattern, count=100
                )

                for key in keys:
                    data = await self.redis.get(key)
                    if data:
                        feedback_dict = json.loads(data)
                        timestamp = datetime.fromisoformat(
                            feedback_dict["timestamp"]
                        )
                        if timestamp < cutoff_time:
                            await self.redis.delete(key)
                            cleared += 1

                if cursor == 0:
                    break

            logger.info(f"Cleared {cleared} old feedback records")
            return cleared

        except Exception as e:
            logger.error(f"Error clearing feedback: {e}")
            return 0


# Global instance
_feedback_loop_service: Optional[FeedbackLoopService] = None


def get_feedback_loop_service() -> FeedbackLoopService:
    """Get or create the feedback loop service singleton."""
    global _feedback_loop_service
    if _feedback_loop_service is None:
        from app.core.config import settings
        _feedback_loop_service = FeedbackLoopService(redis_url=settings.REDIS_URL)
    return _feedback_loop_service


async def initialize_feedback_loop_service() -> None:
    """Initialize the feedback loop service."""
    service = get_feedback_loop_service()
    await service.initialize()


async def shutdown_feedback_loop_service() -> None:
    """Shutdown the feedback loop service."""
    global _feedback_loop_service
    if _feedback_loop_service:
        await _feedback_loop_service.shutdown()
        _feedback_loop_service = None
