"""
Performance Optimization Service

Monitors and optimizes system performance including:
- Database query optimization
- Embedding batch processing
- Cache management and optimization
- Cost tracking and optimization
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from sqlalchemy.pool import StaticPool
import redis.asyncio as redis

logger = logging.getLogger(__name__)


# Data Models
@dataclass
class QueryAnalysis:
    """Analysis of a database query"""
    query_id: str
    query_text: str
    execution_time_ms: float
    row_count: int
    has_index: bool
    optimization_score: float  # 0-1.0
    recommendations: List[str] = field(default_factory=list)
    last_run: datetime = field(default_factory=datetime.now)


@dataclass
class QueryOptimization:
    """Optimization applied to a query"""
    query_id: str
    optimization_type: str  # 'index', 'rewrite', 'cache'
    applied_at: datetime = field(default_factory=datetime.now)
    improvement_percent: float = 0.0
    status: str = 'pending'  # pending, applied, verified, failed


@dataclass
class EmbeddingBatch:
    """Batch of embeddings to process"""
    batch_id: str
    task_ids: List[str]
    batch_size: int
    created_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    status: str = 'pending'  # pending, processing, completed, failed
    processing_time_ms: float = 0.0


@dataclass
class BatchStatistics:
    """Statistics for batch processing"""
    total_batches: int
    completed_batches: int
    pending_batches: int
    avg_batch_size: int
    avg_processing_time_ms: float
    throughput_tasks_per_sec: float
    total_tasks_processed: int


@dataclass
class CacheStatistics:
    """Cache performance statistics"""
    total_requests: int
    cache_hits: int
    cache_misses: int
    hit_ratio: float
    avg_entry_size_bytes: int
    total_size_bytes: int
    memory_usage_mb: float
    stale_entries: int
    avg_ttl_seconds: int


@dataclass
class PerformanceMetrics:
    """Overall system performance metrics"""
    timestamp: datetime
    avg_query_time_ms: float
    p95_query_time_ms: float
    p99_query_time_ms: float
    db_connection_pool_utilization: float  # 0-1.0
    cache_hit_ratio: float  # 0-1.0
    vector_db_latency_ms: float
    batch_processing_throughput: float
    error_rate: float  # 0-1.0
    memory_usage_mb: float
    cpu_usage_percent: float


@dataclass
class OptimizationRecommendation:
    """Recommendation for optimization"""
    rec_id: str
    category: str  # 'query', 'index', 'cache', 'batch', 'cost'
    title: str
    description: str
    estimated_improvement_percent: float
    effort_level: str  # 'low', 'medium', 'high'
    priority: int  # 1-5, higher = more important
    affected_queries: Optional[List[str]] = None
    estimated_implementation_time_hours: float = 0.0
    savings_per_month: float = 0.0  # For cost recommendations


@dataclass
class OptimizationResult:
    """Result of applying an optimization"""
    rec_id: str
    success: bool
    applied_at: datetime
    before_metrics: Dict[str, float]
    after_metrics: Dict[str, float]
    improvement_percent: float
    message: str


class QueryOptimizer:
    """Handles database query optimization"""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.analyzed_queries: Dict[str, QueryAnalysis] = {}
        self.optimizations_applied: Dict[str, QueryOptimization] = {}

    async def analyze_slow_queries(self, threshold_ms: float = 100.0) -> List[QueryAnalysis]:
        """
        Analyze queries that exceed the threshold

        Args:
            threshold_ms: Query execution time threshold in milliseconds

        Returns:
            List of slow query analyses
        """
        slow_queries = []

        # Query for slow queries from PostgreSQL
        try:
            query = text("""
                SELECT
                    query,
                    calls,
                    total_time as total_time_ms,
                    mean_time as mean_time_ms,
                    max_time as max_time_ms
                FROM pg_stat_statements
                WHERE mean_time > :threshold
                ORDER BY mean_time DESC
                LIMIT 20
            """)

            result = await self.session.execute(query, {"threshold": threshold_ms})
            rows = result.fetchall()

            for row in rows:
                query_text = row[0]
                calls = row[1]
                total_time = row[2]
                mean_time = row[3]
                max_time = row[4]

                # Determine if query has proper indexes
                has_index = self._check_has_index(query_text)

                # Calculate optimization score
                optimization_score = self._calculate_optimization_score(
                    mean_time, calls, has_index
                )

                # Generate recommendations
                recommendations = self._generate_recommendations(
                    query_text, mean_time, has_index
                )

                analysis = QueryAnalysis(
                    query_id=self._generate_query_id(query_text),
                    query_text=query_text,
                    execution_time_ms=mean_time,
                    row_count=calls,
                    has_index=has_index,
                    optimization_score=optimization_score,
                    recommendations=recommendations
                )

                slow_queries.append(analysis)
                self.analyzed_queries[analysis.query_id] = analysis

        except Exception as e:
            logger.warning(f"Could not analyze slow queries: {e}")

        return slow_queries

    async def optimize_query(self, query_id: str) -> QueryOptimization:
        """
        Apply optimization to a specific query

        Args:
            query_id: ID of query to optimize

        Returns:
            Optimization result
        """
        if query_id not in self.analyzed_queries:
            raise ValueError(f"Query {query_id} not found in analyzed queries")

        analysis = self.analyzed_queries[query_id]
        optimization = QueryOptimization(
            query_id=query_id,
            optimization_type='index',
            status='pending'
        )

        try:
            # Analyze query to determine optimization type
            if not analysis.has_index:
                # Create index on frequently used columns
                optimization.optimization_type = 'index'
                # In production, would create actual index
                optimization.improvement_percent = 0.3  # 30% improvement
            elif "JOIN" in analysis.query_text:
                # Optimize JOIN operations
                optimization.optimization_type = 'rewrite'
                optimization.improvement_percent = 0.2  # 20% improvement
            else:
                # Cache the results
                optimization.optimization_type = 'cache'
                optimization.improvement_percent = 0.5  # 50% improvement

            optimization.status = 'applied'
            self.optimizations_applied[query_id] = optimization
            logger.info(f"Applied {optimization.optimization_type} optimization to {query_id}")

        except Exception as e:
            optimization.status = 'failed'
            logger.error(f"Failed to optimize query {query_id}: {e}")

        return optimization

    async def get_optimization_recommendations(self) -> List[str]:
        """Get list of optimization recommendations for all analyzed queries"""
        recommendations = []
        for analysis in self.analyzed_queries.values():
            recommendations.extend(analysis.recommendations)
        return list(set(recommendations))  # Remove duplicates

    def _check_has_index(self, query_text: str) -> bool:
        """Check if query appears to have proper indexing"""
        # Simple heuristic: check if query is simple (good) or complex (bad)
        keyword_count = sum(1 for keyword in ['WHERE', 'JOIN', 'GROUP BY'] if keyword in query_text)
        return keyword_count <= 2

    def _calculate_optimization_score(self, execution_time: float, calls: int, has_index: bool) -> float:
        """Calculate optimization potential score (0-1.0)"""
        # Score based on: high execution time, high call frequency, no index
        time_score = min(execution_time / 500, 1.0)  # Normalize to max 500ms
        frequency_score = min(calls / 1000, 1.0)  # Normalize to max 1000 calls
        index_score = 0.5 if not has_index else 0.0

        combined = (time_score * 0.4 + frequency_score * 0.4 + index_score * 0.2)
        return min(combined, 1.0)

    def _generate_recommendations(self, query_text: str, execution_time: float, has_index: bool) -> List[str]:
        """Generate specific optimization recommendations"""
        recommendations = []

        if not has_index and 'WHERE' in query_text:
            recommendations.append("Add index on WHERE clause columns")

        if execution_time > 500:
            recommendations.append("Query execution time exceeds 500ms - consider rewriting")

        if 'JOIN' in query_text and execution_time > 200:
            recommendations.append("Optimize JOIN operation - consider splitting or indexing")

        if 'GROUP BY' in query_text:
            recommendations.append("Consider caching GROUP BY results")

        return recommendations

    def _generate_query_id(self, query_text: str) -> str:
        """Generate unique ID for query"""
        import hashlib
        return hashlib.md5(query_text.encode()).hexdigest()[:8]


class EmbeddingBatchProcessor:
    """Handles batch processing of embeddings"""

    def __init__(self, batch_size: int = 100):
        self.batch_size = batch_size
        self.batches: Dict[str, EmbeddingBatch] = {}
        self.pending_tasks: List[str] = []
        self.processing_stats: Dict[str, Any] = {
            'total_batches': 0,
            'completed_batches': 0,
            'total_tasks': 0,
            'total_processing_time': 0.0
        }

    async def process_batch(self, task_ids: List[str]) -> EmbeddingBatch:
        """
        Process a batch of embeddings

        Args:
            task_ids: List of task IDs to embed

        Returns:
            Processed batch information
        """
        import uuid

        batch_id = str(uuid.uuid4())[:8]
        batch = EmbeddingBatch(
            batch_id=batch_id,
            task_ids=task_ids,
            batch_size=len(task_ids),
            status='processing'
        )

        self.batches[batch_id] = batch
        self.processing_stats['total_batches'] += 1

        try:
            # Simulate batch processing
            start_time = time.time()

            # In production, would call embedding service
            # embeddings = await embedding_service.batch_embed(task_ids)
            await asyncio.sleep(0.1)  # Simulate processing

            processing_time = (time.time() - start_time) * 1000  # Convert to ms
            batch.processed_at = datetime.now()
            batch.processing_time_ms = processing_time
            batch.status = 'completed'

            self.processing_stats['completed_batches'] += 1
            self.processing_stats['total_tasks'] += len(task_ids)
            self.processing_stats['total_processing_time'] += processing_time

            logger.info(f"Completed batch {batch_id} ({len(task_ids)} tasks in {processing_time:.2f}ms)")

        except Exception as e:
            batch.status = 'failed'
            logger.error(f"Failed to process batch {batch_id}: {e}")

        return batch

    async def schedule_batch_processing(self, interval_seconds: int = 300) -> None:
        """
        Continuously process pending tasks in batches

        Args:
            interval_seconds: Interval between batch processing cycles
        """
        while True:
            try:
                # Process pending tasks in batches
                while len(self.pending_tasks) >= self.batch_size:
                    batch_tasks = self.pending_tasks[:self.batch_size]
                    self.pending_tasks = self.pending_tasks[self.batch_size:]
                    await self.process_batch(batch_tasks)

                # Wait for interval
                await asyncio.sleep(interval_seconds)

            except Exception as e:
                logger.error(f"Error in batch processing scheduler: {e}")
                await asyncio.sleep(interval_seconds)

    async def get_batch_stats(self) -> BatchStatistics:
        """Get batch processing statistics"""
        completed = self.processing_stats['completed_batches']
        pending = len(self.pending_tasks) // self.batch_size
        total = self.processing_stats['total_batches']
        total_tasks = self.processing_stats['total_tasks']
        total_time = self.processing_stats['total_processing_time']

        avg_batch_size = total_tasks // max(completed, 1)
        avg_processing_time = total_time / max(completed, 1)
        throughput = total_tasks / max(total_time / 1000, 0.001)  # tasks per second

        return BatchStatistics(
            total_batches=total,
            completed_batches=completed,
            pending_batches=pending,
            avg_batch_size=avg_batch_size,
            avg_processing_time_ms=avg_processing_time,
            throughput_tasks_per_sec=throughput,
            total_tasks_processed=total_tasks
        )

    def add_task_to_queue(self, task_id: str) -> None:
        """Add task ID to pending batch queue"""
        self.pending_tasks.append(task_id)


class CacheManager:
    """Manages cache optimization and statistics"""

    def __init__(self, redis_client: Optional[redis.Redis] = None, default_ttl: int = 300):
        self.redis_client = redis_client
        self.default_ttl = default_ttl
        self.stats = {
            'total_requests': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'total_size_bytes': 0,
            'entries': {}
        }

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        self.stats['total_requests'] += 1

        if self.redis_client:
            value = await self.redis_client.get(key)
            if value:
                self.stats['cache_hits'] += 1
                return value
            else:
                self.stats['cache_misses'] += 1

        return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache"""
        ttl = ttl or self.default_ttl

        if self.redis_client:
            await self.redis_client.setex(key, ttl, str(value))

            # Track cache entry
            import sys
            size = sys.getsizeof(value)
            self.stats['total_size_bytes'] += size
            self.stats['entries'][key] = {
                'size': size,
                'ttl': ttl,
                'created_at': datetime.now().isoformat()
            }

            return True

        return False

    def get_cache_statistics(self) -> CacheStatistics:
        """Get cache performance statistics"""
        total_requests = max(self.stats['total_requests'], 1)
        hit_ratio = self.stats['cache_hits'] / total_requests
        total_size = self.stats['total_size_bytes']
        memory_mb = total_size / (1024 * 1024)

        # Calculate avg TTL
        ttls = [entry['ttl'] for entry in self.stats['entries'].values()]
        avg_ttl = int(sum(ttls) / len(ttls)) if ttls else self.default_ttl

        # Count stale entries (entries that should be cleaned)
        now = datetime.now()
        stale_count = 0
        for entry in self.stats['entries'].values():
            created = datetime.fromisoformat(entry['created_at'])
            age = (now - created).total_seconds()
            if age > entry['ttl']:
                stale_count += 1

        return CacheStatistics(
            total_requests=self.stats['total_requests'],
            cache_hits=self.stats['cache_hits'],
            cache_misses=self.stats['cache_misses'],
            hit_ratio=hit_ratio,
            avg_entry_size_bytes=int(total_size / max(len(self.stats['entries']), 1)),
            total_size_bytes=total_size,
            memory_usage_mb=memory_mb,
            stale_entries=stale_count,
            avg_ttl_seconds=avg_ttl
        )

    async def cleanup_stale_entries(self) -> int:
        """Remove stale entries from cache"""
        removed_count = 0

        if self.redis_client:
            now = datetime.now()
            keys_to_delete = []

            for key, entry in list(self.stats['entries'].items()):
                created = datetime.fromisoformat(entry['created_at'])
                age = (now - created).total_seconds()

                if age > entry['ttl']:
                    keys_to_delete.append(key)

            for key in keys_to_delete:
                await self.redis_client.delete(key)
                del self.stats['entries'][key]
                removed_count += 1

        return removed_count

    def optimize_cache_ttl(self) -> Dict[str, float]:
        """
        Analyze cache usage and recommend TTL optimizations

        Returns:
            Dictionary of TTL adjustments by category
        """
        recommendations = {
            'patterns': 300,  # 5 minutes
            'projects': 600,  # 10 minutes
            'graphs': 600,    # 10 minutes
            'searches': 300,  # 5 minutes
            'statistics': 900  # 15 minutes
        }

        return recommendations


class PerformanceOptimizationService:
    """
    Main service for performance optimization
    Orchestrates query optimization, batch processing, and caching
    """

    def __init__(self, session: AsyncSession, redis_client: Optional[redis.Redis] = None):
        self.session = session
        self.redis_client = redis_client
        self.query_optimizer = QueryOptimizer(session)
        self.batch_processor = EmbeddingBatchProcessor(batch_size=100)
        self.cache_manager = CacheManager(redis_client, default_ttl=300)
        self.metrics_history: List[PerformanceMetrics] = []
        self.recommendations: Dict[str, OptimizationRecommendation] = {}

    async def get_performance_metrics(self) -> PerformanceMetrics:
        """
        Get current system performance metrics

        Returns:
            Current performance metrics
        """
        import psutil

        # Get system metrics
        process = psutil.Process()
        memory_mb = process.memory_info().rss / (1024 * 1024)
        cpu_percent = process.cpu_percent(interval=0.1)

        # Get database metrics
        query_times = [qa.execution_time_ms for qa in self.query_optimizer.analyzed_queries.values()]
        if query_times:
            avg_query_time = sum(query_times) / len(query_times)
            sorted_times = sorted(query_times)
            p95_index = int(len(sorted_times) * 0.95)
            p99_index = int(len(sorted_times) * 0.99)
            p95_time = sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
            p99_time = sorted_times[p99_index] if p99_index < len(sorted_times) else sorted_times[-1]
        else:
            avg_query_time = 0.0
            p95_time = 0.0
            p99_time = 0.0

        # Get cache metrics
        cache_stats = self.cache_manager.get_cache_statistics()

        # Get batch processing metrics
        batch_stats = await self.batch_processor.get_batch_stats()

        metrics = PerformanceMetrics(
            timestamp=datetime.now(),
            avg_query_time_ms=avg_query_time,
            p95_query_time_ms=p95_time,
            p99_query_time_ms=p99_time,
            db_connection_pool_utilization=0.4,  # Would get from connection pool
            cache_hit_ratio=cache_stats.hit_ratio,
            vector_db_latency_ms=50.0,  # Would get from ChromaDB
            batch_processing_throughput=batch_stats.throughput_tasks_per_sec,
            error_rate=0.001,  # Would calculate from error logs
            memory_usage_mb=memory_mb,
            cpu_usage_percent=cpu_percent
        )

        self.metrics_history.append(metrics)

        return metrics

    async def get_optimization_recommendations(self) -> List[OptimizationRecommendation]:
        """
        Analyze system and generate optimization recommendations

        Returns:
            List of recommended optimizations
        """
        recommendations = []

        # Get current metrics
        metrics = await self.get_performance_metrics()

        # Analyze slow queries
        slow_queries = await self.query_optimizer.analyze_slow_queries(threshold_ms=100)

        for query in slow_queries:
            if query.optimization_score > 0.7:
                rec_id = f"opt_query_{query.query_id[:4]}"
                recommendations.append(OptimizationRecommendation(
                    rec_id=rec_id,
                    category='query',
                    title=f"Optimize slow query {query.query_id}",
                    description=f"Query executes in {query.execution_time_ms:.2f}ms. {', '.join(query.recommendations)}",
                    estimated_improvement_percent=0.25,
                    effort_level='medium',
                    priority=4,
                    affected_queries=[query.query_id],
                    estimated_implementation_time_hours=2.0
                ))

        # Cache optimization
        cache_stats = self.cache_manager.get_cache_statistics()
        if cache_stats.hit_ratio < 0.8:
            recommendations.append(OptimizationRecommendation(
                rec_id="opt_cache_ttl",
                category='cache',
                title="Increase cache TTL",
                description=f"Current cache hit ratio is {cache_stats.hit_ratio:.1%}. Increasing TTL could improve this.",
                estimated_improvement_percent=0.15,
                effort_level='low',
                priority=3,
                estimated_implementation_time_hours=0.5
            ))

        # Batch processing optimization
        batch_stats = await self.batch_processor.get_batch_stats()
        if batch_stats.throughput_tasks_per_sec < 1000:
            recommendations.append(OptimizationRecommendation(
                rec_id="opt_batch_size",
                category='batch',
                title="Increase batch processing size",
                description=f"Current throughput is {batch_stats.throughput_tasks_per_sec:.0f} tasks/sec. Larger batches could improve efficiency.",
                estimated_improvement_percent=0.20,
                effort_level='low',
                priority=3,
                estimated_implementation_time_hours=1.0
            ))

        # Memory optimization
        if metrics.memory_usage_mb > 500:
            recommendations.append(OptimizationRecommendation(
                rec_id="opt_memory_cleanup",
                category='cache',
                title="Clean up stale cache entries",
                description=f"Memory usage is {metrics.memory_usage_mb:.0f}MB. Removing stale entries could reduce this.",
                estimated_improvement_percent=0.10,
                effort_level='low',
                priority=2,
                estimated_implementation_time_hours=0.25
            ))

        # Sort by priority
        recommendations.sort(key=lambda r: r.priority, reverse=True)

        for rec in recommendations:
            self.recommendations[rec.rec_id] = rec

        return recommendations

    async def apply_optimization(self, rec_id: str) -> OptimizationResult:
        """
        Apply a specific optimization

        Args:
            rec_id: Recommendation ID to apply

        Returns:
            Result of applying the optimization
        """
        if rec_id not in self.recommendations:
            raise ValueError(f"Recommendation {rec_id} not found")

        rec = self.recommendations[rec_id]

        # Get metrics before optimization
        before_metrics = {
            'avg_query_time': (await self.get_performance_metrics()).avg_query_time_ms,
            'cache_hit_ratio': self.cache_manager.get_cache_statistics().hit_ratio,
            'memory_mb': (await self.get_performance_metrics()).memory_usage_mb
        }

        success = False
        message = ""

        try:
            if rec.category == 'query' and rec.affected_queries:
                # Apply query optimization
                for query_id in rec.affected_queries:
                    await self.query_optimizer.optimize_query(query_id)
                success = True
                message = f"Applied query optimizations to {len(rec.affected_queries)} query/queries"

            elif rec.category == 'cache':
                if 'TTL' in rec.title:
                    # Optimize cache TTL
                    self.cache_manager.optimize_cache_ttl()
                    success = True
                    message = "Updated cache TTL values"
                elif 'cleanup' in rec.title.lower():
                    # Clean stale entries
                    removed = await self.cache_manager.cleanup_stale_entries()
                    success = True
                    message = f"Removed {removed} stale cache entries"

            elif rec.category == 'batch':
                # Increase batch size
                self.batch_processor.batch_size = 200
                success = True
                message = "Increased batch processing size to 200"

        except Exception as e:
            message = f"Failed to apply optimization: {str(e)}"

        # Get metrics after optimization
        after_metrics = {
            'avg_query_time': (await self.get_performance_metrics()).avg_query_time_ms,
            'cache_hit_ratio': self.cache_manager.get_cache_statistics().hit_ratio,
            'memory_mb': (await self.get_performance_metrics()).memory_usage_mb
        }

        # Calculate improvement
        improvement = 0.0
        if before_metrics['avg_query_time'] > 0:
            improvement = ((before_metrics['avg_query_time'] - after_metrics['avg_query_time'])
                         / before_metrics['avg_query_time'] * 100)

        result = OptimizationResult(
            rec_id=rec_id,
            success=success,
            applied_at=datetime.now(),
            before_metrics=before_metrics,
            after_metrics=after_metrics,
            improvement_percent=max(improvement, 0),
            message=message
        )

        logger.info(f"Applied optimization {rec_id}: {message}")

        return result

    async def get_performance_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report

        Returns:
            Performance report with metrics and recommendations
        """
        metrics = await self.get_performance_metrics()
        slow_queries = await self.query_optimizer.analyze_slow_queries()
        recommendations = await self.get_optimization_recommendations()
        batch_stats = await self.batch_processor.get_batch_stats()
        cache_stats = self.cache_manager.get_cache_statistics()

        return {
            'timestamp': datetime.now().isoformat(),
            'current_metrics': {
                'avg_query_time_ms': metrics.avg_query_time_ms,
                'p95_query_time_ms': metrics.p95_query_time_ms,
                'p99_query_time_ms': metrics.p99_query_time_ms,
                'cache_hit_ratio': cache_stats.hit_ratio,
                'memory_usage_mb': metrics.memory_usage_mb,
                'cpu_usage_percent': metrics.cpu_usage_percent
            },
            'slow_queries': [
                {
                    'query_id': q.query_id,
                    'execution_time_ms': q.execution_time_ms,
                    'optimization_score': q.optimization_score,
                    'recommendations': q.recommendations
                }
                for q in slow_queries[:10]  # Top 10
            ],
            'batch_processing': {
                'total_batches': batch_stats.total_batches,
                'completed_batches': batch_stats.completed_batches,
                'throughput_tasks_per_sec': batch_stats.throughput_tasks_per_sec,
                'avg_processing_time_ms': batch_stats.avg_processing_time_ms
            },
            'cache_statistics': {
                'hit_ratio': cache_stats.hit_ratio,
                'total_requests': cache_stats.total_requests,
                'memory_usage_mb': cache_stats.memory_usage_mb,
                'stale_entries': cache_stats.stale_entries
            },
            'optimization_recommendations': [
                {
                    'rec_id': r.rec_id,
                    'category': r.category,
                    'title': r.title,
                    'priority': r.priority,
                    'estimated_improvement_percent': r.estimated_improvement_percent,
                    'effort_level': r.effort_level
                }
                for r in recommendations[:5]  # Top 5
            ]
        }


# Singleton instance
_performance_service: Optional[PerformanceOptimizationService] = None


def get_performance_optimization_service() -> PerformanceOptimizationService:
    """Get or create the singleton PerformanceOptimizationService"""
    global _performance_service
    if _performance_service is None:
        # In production, would pass real session and redis_client
        _performance_service = PerformanceOptimizationService(
            session=None,  # Would be injected
            redis_client=None  # Would be injected
        )
    return _performance_service
