"""
Performance monitoring and analytics service for RAG (Phase 3.4).

Purpose: Track and analyze RAG system performance:
1. Retrieval latency - Measure retrieval speed
2. Quality metrics - Track result usefulness
3. Cache effectiveness - Monitor cache hit rates
4. Query patterns - Understand usage trends
5. Agent performance - Compare agent efficiency
6. Cost tracking - Monitor resource usage
7. Anomaly detection - Alert on performance issues
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class MetricType(str, Enum):
    """Types of metrics tracked."""
    RETRIEVAL_LATENCY = "retrieval_latency"
    QUALITY_SCORE = "quality_score"
    CACHE_HIT_RATE = "cache_hit_rate"
    CACHE_MISS_RATE = "cache_miss_rate"
    COMPRESSION_RATIO = "compression_ratio"
    TOKEN_COUNT = "token_count"
    SUMMARY_COUNT = "summary_count"
    ERROR_RATE = "error_rate"


class AnomalyLevel(str, Enum):
    """Severity levels for anomalies."""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass
class RetrievalMetrics:
    """Metrics from a single retrieval operation."""
    timestamp: datetime
    query: str
    agent_id: Optional[str]
    project_id: Optional[str]
    latency_ms: float
    cache_hit: bool
    result_count: int
    total_tokens: int
    quality_score: float
    compression_ratio: float
    summarized_count: int
    errors: List[str] = field(default_factory=list)
    enhancement_applied: bool = False
    optimization_applied: bool = False


@dataclass
class PerformanceStats:
    """Aggregated performance statistics."""
    period: str
    metric_type: MetricType
    count: int
    mean: float
    median: float
    p95: float
    p99: float
    min: float
    max: float
    std_dev: float


class PerformanceMonitor:
    """
    Monitors and analyzes RAG system performance.

    Tracks:
    - Retrieval latency (p95, p99)
    - Quality metrics (average quality scores)
    - Cache effectiveness (hit rates)
    - Query patterns (common queries, domains)
    - Agent performance (agent-specific metrics)
    - Cost metrics (tokens, summary operations)
    - Error rates and anomalies
    """

    def __init__(self, history_size: int = 10000):
        """Initialize the performance monitor.

        Args:
            history_size: Max retrieval metrics to keep in memory
        """
        self.history_size = history_size
        self.metrics: List[RetrievalMetrics] = []
        self.anomalies: List[Tuple[datetime, AnomalyLevel, str]] = []

        # Aggregated stats
        self.query_frequency: Dict[str, int] = defaultdict(int)
        self.agent_stats: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {
                "total_retrievals": 0,
                "avg_latency": 0,
                "cache_hit_rate": 0,
                "avg_quality": 0,
                "error_count": 0,
            }
        )
        self.project_stats: Dict[str, Dict[str, float]] = defaultdict(
            lambda: {
                "total_retrievals": 0,
                "avg_latency": 0,
                "cache_hit_rate": 0,
                "total_tokens": 0,
            }
        )

        # Performance thresholds for anomaly detection
        self.latency_threshold_ms = 500  # Alert if > 500ms
        self.quality_threshold = 0.5  # Alert if < 0.5
        self.error_threshold = 0.1  # Alert if error rate > 10%
        self.cache_hit_threshold = 0.3  # Alert if < 30%

    async def record_retrieval(self, metrics: RetrievalMetrics) -> None:
        """Record metrics from a retrieval operation.

        Args:
            metrics: RetrievalMetrics instance with retrieval data
        """
        try:
            # Add to history
            self.metrics.append(metrics)

            # Keep history size bounded
            if len(self.metrics) > self.history_size:
                self.metrics.pop(0)

            # Update query frequency
            query_key = metrics.query.lower().strip()[:100]
            self.query_frequency[query_key] += 1

            # Update agent stats
            if metrics.agent_id:
                await self._update_agent_stats(metrics)

            # Update project stats
            if metrics.project_id:
                await self._update_project_stats(metrics)

            # Check for anomalies
            await self._detect_anomalies(metrics)

            logger.debug(f"Recorded retrieval: {metrics.latency_ms:.1f}ms, "
                        f"quality={metrics.quality_score:.2f}")

        except Exception as e:
            logger.error(f"Error recording retrieval metrics: {e}")

    async def _update_agent_stats(self, metrics: RetrievalMetrics) -> None:
        """Update statistics for an agent."""
        agent_id = metrics.agent_id
        stats = self.agent_stats[agent_id]

        # Update counters
        total = stats["total_retrievals"]
        stats["total_retrievals"] = total + 1

        # Update average latency
        avg_latency = stats["avg_latency"]
        stats["avg_latency"] = (
            (avg_latency * total + metrics.latency_ms) / (total + 1)
        )

        # Update cache hit rate
        cache_hits = stats["cache_hit_rate"] * total
        if metrics.cache_hit:
            cache_hits += 1
        stats["cache_hit_rate"] = cache_hits / (total + 1)

        # Update average quality
        avg_quality = stats["avg_quality"]
        stats["avg_quality"] = (
            (avg_quality * total + metrics.quality_score) / (total + 1)
        )

        # Update error count
        if metrics.errors:
            stats["error_count"] += len(metrics.errors)

    async def _update_project_stats(self, metrics: RetrievalMetrics) -> None:
        """Update statistics for a project."""
        project_id = metrics.project_id
        stats = self.project_stats[project_id]

        # Update counters
        total = stats["total_retrievals"]
        stats["total_retrievals"] = total + 1

        # Update average latency
        avg_latency = stats["avg_latency"]
        stats["avg_latency"] = (
            (avg_latency * total + metrics.latency_ms) / (total + 1)
        )

        # Update cache hit rate
        cache_hits = stats["cache_hit_rate"] * total
        if metrics.cache_hit:
            cache_hits += 1
        stats["cache_hit_rate"] = cache_hits / (total + 1)

        # Update total tokens
        stats["total_tokens"] += metrics.total_tokens

    async def _detect_anomalies(self, metrics: RetrievalMetrics) -> None:
        """Detect anomalies in retrieval metrics."""
        now = datetime.now()

        # Check latency
        if metrics.latency_ms > self.latency_threshold_ms:
            message = (
                f"High latency detected: {metrics.latency_ms:.1f}ms "
                f"(threshold: {self.latency_threshold_ms}ms)"
            )
            self.anomalies.append((now, AnomalyLevel.WARNING, message))
            logger.warning(message)

        # Check quality
        if metrics.quality_score < self.quality_threshold:
            message = (
                f"Low quality detected: {metrics.quality_score:.2f} "
                f"(threshold: {self.quality_threshold})"
            )
            self.anomalies.append((now, AnomalyLevel.WARNING, message))
            logger.warning(message)

        # Check errors
        if metrics.errors:
            message = f"Errors during retrieval: {', '.join(metrics.errors)}"
            self.anomalies.append((now, AnomalyLevel.WARNING, message))
            logger.warning(message)

    def get_stats(self, period: str = "all") -> Dict[str, Any]:
        """Get aggregated statistics.

        Args:
            period: "all", "1h", "24h", "7d"

        Returns:
            Dictionary of statistics
        """
        try:
            # Filter metrics by period
            metrics = self._filter_by_period(period)

            if not metrics:
                return {"count": 0, "message": "No metrics in period"}

            # Calculate latency stats
            latencies = [m.latency_ms for m in metrics]
            latency_stats = self._calculate_percentiles(latencies)

            # Calculate quality stats
            qualities = [m.quality_score for m in metrics]
            quality_stats = self._calculate_percentiles(qualities)

            # Calculate cache hit rate
            cache_hits = sum(1 for m in metrics if m.cache_hit)
            cache_hit_rate = cache_hits / len(metrics) if metrics else 0

            # Calculate error rate
            error_count = sum(len(m.errors) for m in metrics)
            error_rate = error_count / len(metrics) if metrics else 0

            # Calculate compression stats
            compressions = [m.compression_ratio for m in metrics if m.optimization_applied]
            compression_stats = self._calculate_percentiles(compressions) if compressions else {}

            # Count summarized items
            total_summarized = sum(m.summarized_count for m in metrics)

            return {
                "period": period,
                "total_retrievals": len(metrics),
                "latency": {
                    "mean": latency_stats["mean"],
                    "median": latency_stats["median"],
                    "p95": latency_stats["p95"],
                    "p99": latency_stats["p99"],
                    "min": latency_stats["min"],
                    "max": latency_stats["max"],
                },
                "quality": {
                    "mean": quality_stats["mean"],
                    "median": quality_stats["median"],
                    "p95": quality_stats["p95"],
                    "min": quality_stats["min"],
                    "max": quality_stats["max"],
                },
                "cache": {
                    "hit_rate": cache_hit_rate,
                    "miss_rate": 1 - cache_hit_rate,
                    "hits": cache_hits,
                },
                "optimization": {
                    "applied_count": sum(1 for m in metrics if m.optimization_applied),
                    "average_compression": compression_stats.get("mean", 0),
                    "total_summarized": total_summarized,
                },
                "errors": {
                    "count": error_count,
                    "rate": error_rate,
                },
                "enhancement": {
                    "applied_count": sum(1 for m in metrics if m.enhancement_applied),
                },
                "anomalies": self._count_anomalies(period),
            }

        except Exception as e:
            logger.error(f"Error calculating stats: {e}")
            return {"error": str(e)}

    def _filter_by_period(self, period: str) -> List[RetrievalMetrics]:
        """Filter metrics by time period."""
        if period == "all":
            return self.metrics

        now = datetime.now()
        if period == "1h":
            cutoff = now - timedelta(hours=1)
        elif period == "24h":
            cutoff = now - timedelta(days=1)
        elif period == "7d":
            cutoff = now - timedelta(days=7)
        else:
            return self.metrics

        return [m for m in self.metrics if m.timestamp >= cutoff]

    def _calculate_percentiles(self, values: List[float]) -> Dict[str, float]:
        """Calculate percentile statistics."""
        if not values:
            return {
                "mean": 0,
                "median": 0,
                "p95": 0,
                "p99": 0,
                "min": 0,
                "max": 0,
                "std_dev": 0,
            }

        sorted_values = sorted(values)
        n = len(sorted_values)

        return {
            "mean": sum(values) / n,
            "median": sorted_values[n // 2],
            "p95": sorted_values[int(n * 0.95)],
            "p99": sorted_values[int(n * 0.99)],
            "min": min(values),
            "max": max(values),
            "std_dev": self._std_dev(values),
        }

    @staticmethod
    def _std_dev(values: List[float]) -> float:
        """Calculate standard deviation."""
        if not values or len(values) < 2:
            return 0.0

        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5

    def _count_anomalies(self, period: str) -> Dict[str, int]:
        """Count anomalies in period."""
        now = datetime.now()

        if period == "1h":
            cutoff = now - timedelta(hours=1)
        elif period == "24h":
            cutoff = now - timedelta(days=1)
        elif period == "7d":
            cutoff = now - timedelta(days=7)
        else:
            cutoff = datetime.min

        anomalies = [a for a in self.anomalies if a[0] >= cutoff]

        return {
            "total": len(anomalies),
            "warning": sum(1 for a in anomalies if a[1] == AnomalyLevel.WARNING),
            "critical": sum(1 for a in anomalies if a[1] == AnomalyLevel.CRITICAL),
        }

    def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """Get statistics for a specific agent.

        Args:
            agent_id: Agent identifier

        Returns:
            Agent-specific statistics
        """
        stats = self.agent_stats.get(agent_id, {})

        if not stats.get("total_retrievals"):
            return {"message": f"No data for agent {agent_id}"}

        return {
            "agent_id": agent_id,
            "total_retrievals": stats["total_retrievals"],
            "avg_latency_ms": stats["avg_latency"],
            "cache_hit_rate": stats["cache_hit_rate"],
            "avg_quality_score": stats["avg_quality"],
            "error_count": stats["error_count"],
        }

    def get_project_stats(self, project_id: str) -> Dict[str, Any]:
        """Get statistics for a specific project.

        Args:
            project_id: Project identifier

        Returns:
            Project-specific statistics
        """
        stats = self.project_stats.get(project_id, {})

        if not stats.get("total_retrievals"):
            return {"message": f"No data for project {project_id}"}

        return {
            "project_id": project_id,
            "total_retrievals": stats["total_retrievals"],
            "avg_latency_ms": stats["avg_latency"],
            "cache_hit_rate": stats["cache_hit_rate"],
            "total_tokens_used": stats["total_tokens"],
        }

    def get_top_queries(self, limit: int = 10) -> List[Tuple[str, int]]:
        """Get most frequent queries.

        Args:
            limit: Number of queries to return

        Returns:
            List of (query, count) tuples
        """
        sorted_queries = sorted(
            self.query_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return sorted_queries[:limit]

    def get_anomalies(self, level: Optional[AnomalyLevel] = None,
                     limit: int = 10) -> List[Tuple[datetime, str, str]]:
        """Get recent anomalies.

        Args:
            level: Filter by severity level
            limit: Number of anomalies to return

        Returns:
            List of (timestamp, level, message) tuples
        """
        anomalies = self.anomalies

        if level:
            anomalies = [a for a in anomalies if a[1] == level]

        # Return most recent
        sorted_anomalies = sorted(anomalies, key=lambda x: x[0], reverse=True)
        result = [(a[0], a[1].value, a[2]) for a in sorted_anomalies[:limit]]

        return result

    def get_performance_trend(self, metric: MetricType,
                            period: str = "24h",
                            bucket_size_minutes: int = 15) -> Dict[str, List[float]]:
        """Get performance trend over time.

        Args:
            metric: Metric to track
            period: Time period ("1h", "24h", "7d")
            bucket_size_minutes: Size of time buckets

        Returns:
            Dictionary of timestamps to metric values
        """
        try:
            metrics = self._filter_by_period(period)

            if not metrics:
                return {"timestamps": [], "values": []}

            # Group into time buckets
            buckets: Dict[datetime, List[float]] = defaultdict(list)

            for m in metrics:
                # Round timestamp to bucket
                bucket_minutes = (m.timestamp.minute // bucket_size_minutes) * bucket_size_minutes
                bucket = m.timestamp.replace(
                    minute=bucket_minutes,
                    second=0,
                    microsecond=0
                )

                # Extract metric value
                value = self._extract_metric_value(m, metric)
                if value is not None:
                    buckets[bucket].append(value)

            # Calculate averages per bucket
            sorted_buckets = sorted(buckets.items())
            timestamps = [str(b[0]) for b in sorted_buckets]
            values = [sum(b[1]) / len(b[1]) for b in sorted_buckets]

            return {
                "metric": metric.value,
                "period": period,
                "timestamps": timestamps,
                "values": values,
            }

        except Exception as e:
            logger.error(f"Error calculating trend: {e}")
            return {"error": str(e)}

    @staticmethod
    def _extract_metric_value(m: RetrievalMetrics, metric: MetricType) -> Optional[float]:
        """Extract metric value from retrieval metrics."""
        if metric == MetricType.RETRIEVAL_LATENCY:
            return m.latency_ms
        elif metric == MetricType.QUALITY_SCORE:
            return m.quality_score
        elif metric == MetricType.CACHE_HIT_RATE:
            return 1.0 if m.cache_hit else 0.0
        elif metric == MetricType.COMPRESSION_RATIO:
            return m.compression_ratio if m.optimization_applied else None
        elif metric == MetricType.TOKEN_COUNT:
            return float(m.total_tokens)
        elif metric == MetricType.ERROR_RATE:
            return 1.0 if m.errors else 0.0
        return None

    def export_metrics(self, format: str = "json") -> str:
        """Export metrics in specified format.

        Args:
            format: Output format ("json", "csv")

        Returns:
            Formatted metrics string
        """
        if format == "json":
            import json
            data = {
                "timestamp": datetime.now().isoformat(),
                "metrics_count": len(self.metrics),
                "stats": self.get_stats(),
                "agents": dict(self.agent_stats),
                "projects": dict(self.project_stats),
            }
            return json.dumps(data, indent=2, default=str)

        elif format == "csv":
            lines = [
                "timestamp,agent_id,project_id,latency_ms,cache_hit,quality_score,"
                "compression_ratio,error_count"
            ]
            for m in self.metrics:
                lines.append(
                    f"{m.timestamp.isoformat()},"
                    f"{m.agent_id or ''},"
                    f"{m.project_id or ''},"
                    f"{m.latency_ms:.2f},"
                    f"{1 if m.cache_hit else 0},"
                    f"{m.quality_score:.2f},"
                    f"{m.compression_ratio:.2f},"
                    f"{len(m.errors)}"
                )
            return "\n".join(lines)

        return ""

    def reset_metrics(self) -> None:
        """Reset all collected metrics."""
        self.metrics.clear()
        self.query_frequency.clear()
        self.agent_stats.clear()
        self.project_stats.clear()
        self.anomalies.clear()
        logger.info("Performance metrics reset")


# Global instance
_performance_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get or create the performance monitor singleton."""
    global _performance_monitor
    if _performance_monitor is None:
        _performance_monitor = PerformanceMonitor()
    return _performance_monitor


async def initialize_performance_monitor() -> None:
    """Initialize performance monitor."""
    monitor = get_performance_monitor()
    logger.info("Performance monitor initialized")


async def shutdown_performance_monitor() -> None:
    """Shutdown performance monitor."""
    monitor = get_performance_monitor()
    logger.info("Performance monitor shutdown")
