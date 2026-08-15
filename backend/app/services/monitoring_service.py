"""
Monitoring Service

Tracks and monitors:
- RAG effectiveness and quality metrics
- Pattern success rates and trends
- API and infrastructure costs
- System health and alerts
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# Enums
class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class MetricCategory(Enum):
    """Metric categories"""
    RAG_EFFECTIVENESS = "rag_effectiveness"
    PATTERN_SUCCESS = "pattern_success"
    COST = "cost"
    PERFORMANCE = "performance"
    ERROR = "error"


# Data Models
@dataclass
class RetrievalQuality:
    """Metrics for retrieval quality"""
    timestamp: datetime
    accuracy: float  # 0-1.0: How accurate are retrieved results
    relevance: float  # 0-1.0: How relevant are retrieved results
    diversity: float  # 0-1.0: Diversity of retrieved results
    latency_ms: float
    success_rate: float  # 0-1.0: Percentage of successful retrievals


@dataclass
class RAGEffectivenessMetrics:
    """Overall RAG effectiveness metrics"""
    timestamp: datetime
    effectiveness_score: float  # 0-1.0
    retrieval_quality: RetrievalQuality
    pattern_accuracy: float  # 0-1.0
    recommendation_acceptance_rate: float  # 0-1.0: Users accept recommendations
    total_queries: int
    successful_queries: int
    failed_queries: int
    avg_query_latency_ms: float


@dataclass
class PatternPerformance:
    """Performance metrics for a single pattern"""
    pattern_id: str
    pattern_name: str
    usage_count: int
    success_count: int
    failure_count: int
    success_rate: float  # 0-1.0
    last_used: datetime
    trend: float  # -1.0 to 1.0: -1 declining, 0 stable, 1 improving
    avg_improvement_percent: float
    total_value_added: float


@dataclass
class CostBreakdown:
    """Cost breakdown by provider and type"""
    timestamp: datetime
    total_cost: float
    by_provider: Dict[str, float]  # Provider name -> cost
    by_type: Dict[str, float]  # API type -> cost (embedding, llm, vector_search)
    monthly_projection: float
    cost_per_query: float
    cost_per_pattern_discovery: float


@dataclass
class CostTrend:
    """Cost trend information"""
    date: datetime
    total_cost: float
    by_provider: Dict[str, float]
    trend_percent: float  # Percentage change from previous period


@dataclass
class Alert:
    """System alert"""
    alert_id: str
    severity: AlertSeverity
    category: MetricCategory
    title: str
    description: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    metrics: Dict[str, float] = field(default_factory=dict)
    recommended_action: str = ""


@dataclass
class HealthStatus:
    """Overall system health status"""
    timestamp: datetime
    overall_health: str  # 'healthy', 'degraded', 'critical'
    rag_effectiveness_healthy: bool
    pattern_discovery_healthy: bool
    cost_monitoring_healthy: bool
    performance_healthy: bool
    error_rate_healthy: bool
    active_alerts: int
    critical_alerts: int


@dataclass
class SystemMetrics:
    """Overall system metrics"""
    timestamp: datetime
    rag_effectiveness: RAGEffectivenessMetrics
    top_patterns: List[PatternPerformance]
    health_status: HealthStatus
    cost_metrics: CostBreakdown
    active_alerts: List[Alert]


class RAGEffectivenessMonitor:
    """Monitors RAG system effectiveness"""

    def __init__(self):
        self.metrics_history: Dict[str, List[RAGEffectivenessMetrics]] = {}
        self.current_metrics: Optional[RAGEffectivenessMetrics] = None
        self.retrieval_stats = {
            'total_queries': 0,
            'successful_queries': 0,
            'failed_queries': 0,
            'total_latency_ms': 0
        }

    async def calculate_effectiveness_score(self) -> float:
        """
        Calculate overall RAG effectiveness score (0-1.0)

        Returns:
            Effectiveness score
        """
        if self.current_metrics is None:
            return 0.5

        # Weighted calculation
        retrieval_quality = self.current_metrics.retrieval_quality
        weights = {
            'accuracy': 0.25,
            'relevance': 0.25,
            'pattern_accuracy': 0.20,
            'success_rate': 0.20,
            'acceptance': 0.10
        }

        score = (
            retrieval_quality.accuracy * weights['accuracy'] +
            retrieval_quality.relevance * weights['relevance'] +
            self.current_metrics.pattern_accuracy * weights['pattern_accuracy'] +
            retrieval_quality.success_rate * weights['success_rate'] +
            self.current_metrics.recommendation_acceptance_rate * weights['acceptance']
        )

        return round(score, 3)

    async def get_retrieval_quality(self) -> Optional[RetrievalQuality]:
        """Get current retrieval quality metrics"""
        if self.current_metrics is None:
            return None

        return self.current_metrics.retrieval_quality

    async def get_pattern_accuracy(self) -> float:
        """Get current pattern accuracy"""
        if self.current_metrics is None:
            return 0.0

        return self.current_metrics.pattern_accuracy

    async def track_metric(self, metric_name: str, value: float) -> None:
        """Track a metric value"""
        if metric_name == 'retrieval_accuracy' and self.current_metrics:
            self.current_metrics.retrieval_quality.accuracy = min(max(value, 0), 1.0)
        elif metric_name == 'retrieval_relevance' and self.current_metrics:
            self.current_metrics.retrieval_quality.relevance = min(max(value, 0), 1.0)
        elif metric_name == 'pattern_accuracy' and self.current_metrics:
            self.current_metrics.pattern_accuracy = min(max(value, 0), 1.0)
        elif metric_name == 'acceptance_rate' and self.current_metrics:
            self.current_metrics.recommendation_acceptance_rate = min(max(value, 0), 1.0)

    async def update_metrics(self) -> RAGEffectivenessMetrics:
        """
        Update and return current RAG effectiveness metrics

        Returns:
            Current RAG effectiveness metrics
        """
        total = max(self.retrieval_stats['total_queries'], 1)
        success_rate = self.retrieval_stats['successful_queries'] / total
        avg_latency = self.retrieval_stats['total_latency_ms'] / total

        retrieval_quality = RetrievalQuality(
            timestamp=datetime.now(),
            accuracy=0.85,  # Would calculate from actual retrievals
            relevance=0.80,  # Would calculate from user feedback
            diversity=0.75,  # Would calculate from result diversity
            latency_ms=avg_latency,
            success_rate=success_rate
        )

        self.current_metrics = RAGEffectivenessMetrics(
            timestamp=datetime.now(),
            effectiveness_score=await self.calculate_effectiveness_score(),
            retrieval_quality=retrieval_quality,
            pattern_accuracy=0.82,  # Would calculate from pattern validation
            recommendation_acceptance_rate=0.78,  # Would track from user actions
            total_queries=self.retrieval_stats['total_queries'],
            successful_queries=self.retrieval_stats['successful_queries'],
            failed_queries=self.retrieval_stats['failed_queries'],
            avg_query_latency_ms=avg_latency
        )

        return self.current_metrics


class PatternSuccessTracker:
    """Tracks pattern success rates and trends"""

    def __init__(self):
        self.pattern_stats: Dict[str, Dict[str, Any]] = {}
        self.usage_history: Dict[str, List[Tuple[datetime, bool]]] = {}

    async def track_pattern_usage(self, pattern_id: str, success: bool) -> None:
        """
        Track pattern usage

        Args:
            pattern_id: ID of the pattern
            success: Whether the pattern usage was successful
        """
        if pattern_id not in self.pattern_stats:
            self.pattern_stats[pattern_id] = {
                'usage_count': 0,
                'success_count': 0,
                'failure_count': 0,
                'last_used': None,
                'created_at': datetime.now()
            }
            self.usage_history[pattern_id] = []

        # Update stats
        self.pattern_stats[pattern_id]['usage_count'] += 1
        self.pattern_stats[pattern_id]['last_used'] = datetime.now()

        if success:
            self.pattern_stats[pattern_id]['success_count'] += 1
        else:
            self.pattern_stats[pattern_id]['failure_count'] += 1

        # Track in history
        self.usage_history[pattern_id].append((datetime.now(), success))

    async def get_pattern_success_rate(self, pattern_id: str) -> float:
        """Get success rate for a specific pattern"""
        if pattern_id not in self.pattern_stats:
            return 0.0

        stats = self.pattern_stats[pattern_id]
        total = stats['usage_count']

        if total == 0:
            return 0.0

        return stats['success_count'] / total

    async def get_top_patterns(self, limit: int = 10) -> List[PatternPerformance]:
        """Get top performing patterns"""
        patterns = []

        for pattern_id, stats in self.pattern_stats.items():
            success_rate = stats['success_count'] / max(stats['usage_count'], 1)

            # Calculate trend (simplified: based on recent vs overall)
            if pattern_id in self.usage_history:
                recent = self.usage_history[pattern_id][-10:] if len(self.usage_history[pattern_id]) >= 10 else self.usage_history[pattern_id]
                recent_success_rate = sum(1 for _, success in recent if success) / max(len(recent), 1)
                trend = recent_success_rate - success_rate
            else:
                trend = 0.0

            perf = PatternPerformance(
                pattern_id=pattern_id,
                pattern_name=f"Pattern {pattern_id[:8]}",  # Would get from database
                usage_count=stats['usage_count'],
                success_count=stats['success_count'],
                failure_count=stats['failure_count'],
                success_rate=success_rate,
                last_used=stats['last_used'],
                trend=trend,
                avg_improvement_percent=0.15,  # Would calculate from results
                total_value_added=stats['success_count'] * 0.5  # Simplified
            )

            patterns.append(perf)

        # Sort by success rate
        patterns.sort(key=lambda p: p.success_rate, reverse=True)

        return patterns[:limit]

    async def get_pattern_trends(self, pattern_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get trend data for a pattern"""
        if pattern_id not in self.usage_history:
            return []

        cutoff_date = datetime.now() - timedelta(days=days)
        recent_usage = [
            usage for usage in self.usage_history[pattern_id]
            if usage[0] > cutoff_date
        ]

        if not recent_usage:
            return []

        # Group by day
        trends_by_day: Dict[str, List[bool]] = {}
        for usage_date, success in recent_usage:
            day_key = usage_date.strftime("%Y-%m-%d")
            if day_key not in trends_by_day:
                trends_by_day[day_key] = []
            trends_by_day[day_key].append(success)

        # Calculate daily stats
        trends = []
        for day_key in sorted(trends_by_day.keys()):
            usages = trends_by_day[day_key]
            success_rate = sum(1 for s in usages if s) / len(usages)
            trends.append({
                'date': day_key,
                'usage_count': len(usages),
                'success_rate': success_rate
            })

        return trends


class CostMonitor:
    """Monitors API and infrastructure costs"""

    def __init__(self):
        self.cost_records: List[Dict[str, Any]] = []
        self.monthly_budgets: Dict[str, float] = {
            'embeddings': 50.0,
            'llm_calls': 100.0,
            'vector_search': 25.0,
            'infrastructure': 150.0
        }

    async def track_api_call(self, provider: str, cost: float, call_type: str = 'api') -> None:
        """
        Track an API call cost

        Args:
            provider: API provider name (OpenAI, Anthropic, etc.)
            cost: Cost in dollars
            call_type: Type of call (embedding, llm_call, vector_search)
        """
        self.cost_records.append({
            'timestamp': datetime.now(),
            'provider': provider,
            'cost': cost,
            'call_type': call_type
        })

        logger.debug(f"Tracked {call_type} from {provider}: ${cost:.4f}")

    async def get_total_cost(self, days: int = 30) -> float:
        """Get total cost for the last N days"""
        cutoff_date = datetime.now() - timedelta(days=days)
        total = sum(
            record['cost'] for record in self.cost_records
            if record['timestamp'] > cutoff_date
        )
        return round(total, 2)

    async def get_cost_breakdown(self) -> CostBreakdown:
        """Get cost breakdown by provider and type"""
        cutoff_date = datetime.now() - timedelta(days=30)
        recent_costs = [r for r in self.cost_records if r['timestamp'] > cutoff_date]

        # Group by provider
        by_provider: Dict[str, float] = {}
        by_type: Dict[str, float] = {}
        total = 0.0

        for record in recent_costs:
            provider = record['provider']
            call_type = record['call_type']
            cost = record['cost']

            by_provider[provider] = by_provider.get(provider, 0.0) + cost
            by_type[call_type] = by_type.get(call_type, 0.0) + cost
            total += cost

        # Calculate projections and per-query costs
        total_queries = max(len(recent_costs), 1)
        monthly_projection = (total / 30) * 30
        cost_per_query = total / total_queries if total_queries > 0 else 0.0
        cost_per_pattern = total / max(total_queries // 5, 1)  # Estimate: 1 pattern per 5 queries

        return CostBreakdown(
            timestamp=datetime.now(),
            total_cost=round(total, 2),
            by_provider=by_provider,
            by_type=by_type,
            monthly_projection=round(monthly_projection, 2),
            cost_per_query=round(cost_per_query, 4),
            cost_per_pattern_discovery=round(cost_per_pattern, 2)
        )

    async def get_cost_trends(self, days: int = 30) -> List[CostTrend]:
        """Get cost trends over time"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_costs = [r for r in self.cost_records if r['timestamp'] > cutoff_date]

        # Group by day
        costs_by_day: Dict[str, Dict[str, float]] = {}

        for record in recent_costs:
            day_key = record['timestamp'].strftime("%Y-%m-%d")
            if day_key not in costs_by_day:
                costs_by_day[day_key] = {'total': 0.0, 'by_provider': {}}

            provider = record['provider']
            cost = record['cost']
            costs_by_day[day_key]['total'] += cost
            costs_by_day[day_key]['by_provider'][provider] = (
                costs_by_day[day_key]['by_provider'].get(provider, 0.0) + cost
            )

        # Calculate trends
        trends = []
        sorted_days = sorted(costs_by_day.keys())

        for i, day_key in enumerate(sorted_days):
            day_data = costs_by_day[day_key]
            total_cost = day_data['total']

            # Calculate trend percent
            if i > 0:
                prev_total = costs_by_day[sorted_days[i-1]]['total']
                trend_percent = ((total_cost - prev_total) / max(prev_total, 0.01)) * 100
            else:
                trend_percent = 0.0

            trends.append(CostTrend(
                date=datetime.strptime(day_key, "%Y-%m-%d"),
                total_cost=round(total_cost, 2),
                by_provider=day_data['by_provider'],
                trend_percent=round(trend_percent, 1)
            ))

        return trends

    async def check_budget_alerts(self) -> List[Alert]:
        """Check if any budget thresholds have been exceeded"""
        alerts = []
        cost_breakdown = await self.get_cost_breakdown()

        for cost_type, budget in self.monthly_budgets.items():
            actual = cost_breakdown.by_type.get(cost_type, 0.0)
            if actual > budget:
                percent_over = ((actual - budget) / budget) * 100
                alerts.append(Alert(
                    alert_id=f"budget_{cost_type}",
                    severity=AlertSeverity.WARNING if percent_over < 20 else AlertSeverity.CRITICAL,
                    category=MetricCategory.COST,
                    title=f"Budget exceeded for {cost_type}",
                    description=f"Spent ${actual:.2f} out of ${budget:.2f} budget ({percent_over:.1f}% over)",
                    created_at=datetime.now(),
                    metrics={'actual': actual, 'budget': budget, 'percent_over': percent_over},
                    recommended_action=f"Review and optimize {cost_type} usage"
                ))

        return alerts


class MonitoringService:
    """
    Main monitoring service
    Orchestrates RAG effectiveness, pattern tracking, and cost monitoring
    """

    def __init__(self):
        self.rag_monitor = RAGEffectivenessMonitor()
        self.pattern_tracker = PatternSuccessTracker()
        self.cost_monitor = CostMonitor()
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []

    async def get_health_status(self) -> HealthStatus:
        """
        Get overall system health status

        Returns:
            Current health status
        """
        # Check RAG effectiveness
        effectiveness = await self.rag_monitor.update_metrics()
        rag_healthy = effectiveness.effectiveness_score >= 0.75

        # Check pattern discovery
        top_patterns = await self.pattern_tracker.get_top_patterns()
        pattern_healthy = len(top_patterns) > 0 and sum(1 for p in top_patterns if p.success_rate >= 0.7) > 0

        # Check cost monitoring
        cost_breakdown = await self.cost_monitor.get_cost_breakdown()
        cost_healthy = cost_breakdown.total_cost < 500  # Assuming monthly budget

        # Check performance
        performance_healthy = effectiveness.retrieval_quality.latency_ms < 1000

        # Check error rate
        error_rate = effectiveness.failed_queries / max(effectiveness.total_queries, 1)
        error_healthy = error_rate < 0.1  # Less than 10% error rate

        # Determine overall health
        healthy_checks = sum([rag_healthy, pattern_healthy, cost_healthy, performance_healthy, error_healthy])
        if healthy_checks == 5:
            overall = 'healthy'
        elif healthy_checks >= 3:
            overall = 'degraded'
        else:
            overall = 'critical'

        # Count critical alerts
        critical_count = sum(1 for alert in self.active_alerts.values() if alert.severity == AlertSeverity.CRITICAL)

        return HealthStatus(
            timestamp=datetime.now(),
            overall_health=overall,
            rag_effectiveness_healthy=rag_healthy,
            pattern_discovery_healthy=pattern_healthy,
            cost_monitoring_healthy=cost_healthy,
            performance_healthy=performance_healthy,
            error_rate_healthy=error_healthy,
            active_alerts=len(self.active_alerts),
            critical_alerts=critical_count
        )

    async def get_all_metrics(self) -> SystemMetrics:
        """
        Get all system metrics

        Returns:
            Comprehensive system metrics
        """
        rag_effectiveness = await self.rag_monitor.update_metrics()
        top_patterns = await self.pattern_tracker.get_top_patterns(limit=5)
        health_status = await self.get_health_status()
        cost_metrics = await self.cost_monitor.get_cost_breakdown()
        active_alerts = list(self.active_alerts.values())

        return SystemMetrics(
            timestamp=datetime.now(),
            rag_effectiveness=rag_effectiveness,
            top_patterns=top_patterns,
            health_status=health_status,
            cost_metrics=cost_metrics,
            active_alerts=active_alerts
        )

    async def get_alerts(self, severity: Optional[AlertSeverity] = None, limit: int = 10) -> List[Alert]:
        """
        Get active alerts

        Args:
            severity: Filter by severity level
            limit: Maximum number of alerts to return

        Returns:
            List of active alerts
        """
        alerts = list(self.active_alerts.values())

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        # Sort by creation time, newest first
        alerts.sort(key=lambda a: a.created_at, reverse=True)

        return alerts[:limit]

    async def check_and_create_alerts(self) -> List[Alert]:
        """
        Check system metrics and create alerts if needed

        Returns:
            List of newly created alerts
        """
        new_alerts = []

        # Get current metrics
        rag_metrics = await self.rag_monitor.update_metrics()
        cost_breakdown = await self.cost_monitor.get_cost_breakdown()
        budget_alerts = await self.cost_monitor.check_budget_alerts()

        # Check RAG effectiveness
        if rag_metrics.effectiveness_score < 0.7:
            alert = Alert(
                alert_id=f"rag_low_effectiveness_{datetime.now().timestamp()}",
                severity=AlertSeverity.WARNING,
                category=MetricCategory.RAG_EFFECTIVENESS,
                title="RAG effectiveness below threshold",
                description=f"Effectiveness score is {rag_metrics.effectiveness_score:.2f}, below target of 0.75",
                created_at=datetime.now(),
                metrics={'score': rag_metrics.effectiveness_score},
                recommended_action="Review RAG patterns and retrieval quality"
            )
            new_alerts.append(alert)
            self.active_alerts[alert.alert_id] = alert

        # Check retrieval quality
        if rag_metrics.retrieval_quality.success_rate < 0.9:
            alert = Alert(
                alert_id=f"retrieval_quality_low_{datetime.now().timestamp()}",
                severity=AlertSeverity.WARNING,
                category=MetricCategory.RAG_EFFECTIVENESS,
                title="Retrieval success rate low",
                description=f"Success rate is {rag_metrics.retrieval_quality.success_rate:.1%}, below target of 90%",
                created_at=datetime.now(),
                metrics={'success_rate': rag_metrics.retrieval_quality.success_rate},
                recommended_action="Investigate failed retrievals"
            )
            new_alerts.append(alert)
            self.active_alerts[alert.alert_id] = alert

        # Check latency
        if rag_metrics.retrieval_quality.latency_ms > 500:
            alert = Alert(
                alert_id=f"high_latency_{datetime.now().timestamp()}",
                severity=AlertSeverity.WARNING,
                category=MetricCategory.PERFORMANCE,
                title="High retrieval latency detected",
                description=f"Average latency is {rag_metrics.retrieval_quality.latency_ms:.0f}ms, exceeds target of 200ms",
                created_at=datetime.now(),
                metrics={'latency_ms': rag_metrics.retrieval_quality.latency_ms},
                recommended_action="Check vector DB performance and network latency"
            )
            new_alerts.append(alert)
            self.active_alerts[alert.alert_id] = alert

        # Add budget alerts
        for budget_alert in budget_alerts:
            if budget_alert.alert_id not in self.active_alerts:
                new_alerts.append(budget_alert)
                self.active_alerts[budget_alert.alert_id] = budget_alert

        # Track alert history
        self.alert_history.extend(new_alerts)

        logger.info(f"Created {len(new_alerts)} new alerts")

        return new_alerts


# Singleton instance
_monitoring_service: Optional[MonitoringService] = None


def get_monitoring_service() -> MonitoringService:
    """Get or create the singleton MonitoringService"""
    global _monitoring_service
    if _monitoring_service is None:
        _monitoring_service = MonitoringService()
    return _monitoring_service
