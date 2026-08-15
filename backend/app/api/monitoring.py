"""
Monitoring API Endpoints

Provides REST API endpoints for:
- Performance optimization tracking
- RAG effectiveness monitoring
- Pattern success tracking
- Cost monitoring and alerts
- System health checks
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from enum import Enum

from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.performance_optimization_service import (
    get_performance_optimization_service,
    PerformanceMetrics,
    OptimizationRecommendation
)
from app.services.monitoring_service import (
    get_monitoring_service,
    AlertSeverity,
    RAGEffectivenessMetrics,
    RetrievalQuality,
    PatternPerformance,
    CostBreakdown,
    Alert,
    HealthStatus,
    SystemMetrics
)

# Create router
router = APIRouter(prefix="/api/v1/monitoring", tags=["monitoring"])


# ============================================================================
# Pydantic Models for Requests/Responses
# ============================================================================

class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics"""
    timestamp: datetime
    avg_query_time_ms: float = Field(..., description="Average query execution time in milliseconds")
    p95_query_time_ms: float = Field(..., description="95th percentile query time")
    p99_query_time_ms: float = Field(..., description="99th percentile query time")
    db_connection_pool_utilization: float = Field(..., description="Database connection pool usage (0-1.0)")
    cache_hit_ratio: float = Field(..., description="Cache hit ratio (0-1.0)")
    vector_db_latency_ms: float = Field(..., description="Vector database latency in milliseconds")
    batch_processing_throughput: float = Field(..., description="Batch processing throughput (tasks/sec)")
    error_rate: float = Field(..., description="System error rate (0-1.0)")
    memory_usage_mb: float = Field(..., description="Memory usage in megabytes")
    cpu_usage_percent: float = Field(..., description="CPU usage percentage")


class OptimizationRecommendationResponse(BaseModel):
    """Response model for optimization recommendations"""
    rec_id: str = Field(..., description="Recommendation ID")
    category: str = Field(..., description="Category: query, index, cache, batch, cost")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    estimated_improvement_percent: float = Field(..., description="Estimated improvement percentage")
    effort_level: str = Field(..., description="Effort level: low, medium, high")
    priority: int = Field(..., description="Priority score (1-5)")
    estimated_implementation_time_hours: float = Field(..., description="Estimated implementation time")


class OptimizationApplyRequest(BaseModel):
    """Request model to apply an optimization"""
    rec_id: str = Field(..., description="Recommendation ID to apply")


class OptimizationApplyResponse(BaseModel):
    """Response model for applied optimization"""
    rec_id: str
    success: bool
    applied_at: datetime
    improvement_percent: float
    message: str


class RetrievalQualityResponse(BaseModel):
    """Response model for retrieval quality metrics"""
    timestamp: datetime
    accuracy: float = Field(..., description="Accuracy score (0-1.0)")
    relevance: float = Field(..., description="Relevance score (0-1.0)")
    diversity: float = Field(..., description="Diversity score (0-1.0)")
    latency_ms: float = Field(..., description="Latency in milliseconds")
    success_rate: float = Field(..., description="Success rate (0-1.0)")


class RAGEffectivenessResponse(BaseModel):
    """Response model for RAG effectiveness metrics"""
    timestamp: datetime
    effectiveness_score: float = Field(..., description="Overall effectiveness score (0-1.0)")
    retrieval_quality: RetrievalQualityResponse
    pattern_accuracy: float = Field(..., description="Pattern accuracy score (0-1.0)")
    recommendation_acceptance_rate: float = Field(..., description="User acceptance rate (0-1.0)")
    total_queries: int
    successful_queries: int
    failed_queries: int
    avg_query_latency_ms: float


class PatternPerformanceResponse(BaseModel):
    """Response model for pattern performance metrics"""
    pattern_id: str
    pattern_name: str
    usage_count: int
    success_count: int
    failure_count: int
    success_rate: float = Field(..., description="Success rate (0-1.0)")
    last_used: datetime
    trend: float = Field(..., description="Trend score (-1.0 to 1.0)")
    avg_improvement_percent: float
    total_value_added: float


class CostBreakdownResponse(BaseModel):
    """Response model for cost breakdown"""
    timestamp: datetime
    total_cost: float = Field(..., description="Total cost in dollars")
    by_provider: Dict[str, float] = Field(..., description="Cost by provider")
    by_type: Dict[str, float] = Field(..., description="Cost by API type")
    monthly_projection: float = Field(..., description="Projected monthly cost")
    cost_per_query: float = Field(..., description="Average cost per query")
    cost_per_pattern_discovery: float = Field(..., description="Average cost per pattern discovery")


class AlertResponse(BaseModel):
    """Response model for alerts"""
    alert_id: str
    severity: str = Field(..., description="Severity level: info, warning, critical")
    category: str = Field(..., description="Alert category")
    title: str
    description: str
    created_at: datetime
    resolved_at: Optional[datetime] = None
    metrics: Dict[str, float] = Field(default_factory=dict)
    recommended_action: str


class HealthStatusResponse(BaseModel):
    """Response model for system health status"""
    timestamp: datetime
    overall_health: str = Field(..., description="Overall health: healthy, degraded, critical")
    rag_effectiveness_healthy: bool
    pattern_discovery_healthy: bool
    cost_monitoring_healthy: bool
    performance_healthy: bool
    error_rate_healthy: bool
    active_alerts: int
    critical_alerts: int


class SystemMetricsResponse(BaseModel):
    """Response model for all system metrics"""
    timestamp: datetime
    rag_effectiveness: RAGEffectivenessResponse
    top_patterns: List[PatternPerformanceResponse]
    health_status: HealthStatusResponse
    cost_metrics: CostBreakdownResponse
    active_alerts: List[AlertResponse]


# ============================================================================
# Performance Endpoints
# ============================================================================

@router.get("/performance", response_model=PerformanceMetricsResponse)
async def get_performance_metrics() -> Dict[str, Any]:
    """
    Get current system performance metrics

    Returns:
        Current performance metrics including query times, cache ratios, and throughput
    """
    service = get_performance_optimization_service()
    metrics = await service.get_performance_metrics()

    return {
        "timestamp": metrics.timestamp,
        "avg_query_time_ms": metrics.avg_query_time_ms,
        "p95_query_time_ms": metrics.p95_query_time_ms,
        "p99_query_time_ms": metrics.p99_query_time_ms,
        "db_connection_pool_utilization": metrics.db_connection_pool_utilization,
        "cache_hit_ratio": metrics.cache_hit_ratio,
        "vector_db_latency_ms": metrics.vector_db_latency_ms,
        "batch_processing_throughput": metrics.batch_processing_throughput,
        "error_rate": metrics.error_rate,
        "memory_usage_mb": metrics.memory_usage_mb,
        "cpu_usage_percent": metrics.cpu_usage_percent
    }


@router.get("/performance/recommendations", response_model=List[OptimizationRecommendationResponse])
async def get_performance_recommendations() -> List[Dict[str, Any]]:
    """
    Get performance optimization recommendations

    Returns:
        List of recommended optimizations ranked by priority
    """
    service = get_performance_optimization_service()
    recommendations = await service.get_optimization_recommendations()

    return [
        {
            "rec_id": rec.rec_id,
            "category": rec.category,
            "title": rec.title,
            "description": rec.description,
            "estimated_improvement_percent": rec.estimated_improvement_percent,
            "effort_level": rec.effort_level,
            "priority": rec.priority,
            "estimated_implementation_time_hours": rec.estimated_implementation_time_hours
        }
        for rec in recommendations
    ]


@router.post("/performance/optimize", response_model=OptimizationApplyResponse)
async def apply_optimization(request: OptimizationApplyRequest) -> Dict[str, Any]:
    """
    Apply a performance optimization

    Args:
        request: Optimization request with recommendation ID

    Returns:
        Result of applying the optimization
    """
    service = get_performance_optimization_service()

    try:
        result = await service.apply_optimization(request.rec_id)

        return {
            "rec_id": result.rec_id,
            "success": result.success,
            "applied_at": result.applied_at,
            "improvement_percent": result.improvement_percent,
            "message": result.message
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/performance/report")
async def get_performance_report() -> Dict[str, Any]:
    """
    Get comprehensive performance report

    Returns:
        Performance report with metrics, slow queries, and recommendations
    """
    service = get_performance_optimization_service()
    report = await service.get_performance_report()
    return report


# ============================================================================
# RAG Effectiveness Monitoring Endpoints
# ============================================================================

@router.get("/rag-effectiveness", response_model=RAGEffectivenessResponse)
async def get_rag_effectiveness(period: str = Query("30d", description="Time period: 1d, 7d, 30d")) -> Dict[str, Any]:
    """
    Get RAG effectiveness metrics

    Args:
        period: Time period for metrics (1d, 7d, 30d)

    Returns:
        RAG effectiveness metrics including accuracy, relevance, and success rates
    """
    service = get_monitoring_service()
    metrics = await service.rag_monitor.update_metrics()

    return {
        "timestamp": metrics.timestamp,
        "effectiveness_score": metrics.effectiveness_score,
        "retrieval_quality": {
            "timestamp": metrics.retrieval_quality.timestamp,
            "accuracy": metrics.retrieval_quality.accuracy,
            "relevance": metrics.retrieval_quality.relevance,
            "diversity": metrics.retrieval_quality.diversity,
            "latency_ms": metrics.retrieval_quality.latency_ms,
            "success_rate": metrics.retrieval_quality.success_rate
        },
        "pattern_accuracy": metrics.pattern_accuracy,
        "recommendation_acceptance_rate": metrics.recommendation_acceptance_rate,
        "total_queries": metrics.total_queries,
        "successful_queries": metrics.successful_queries,
        "failed_queries": metrics.failed_queries,
        "avg_query_latency_ms": metrics.avg_query_latency_ms
    }


# ============================================================================
# Pattern Performance Monitoring Endpoints
# ============================================================================

@router.get("/patterns/performance", response_model=List[PatternPerformanceResponse])
async def get_pattern_performance(
    domain: Optional[str] = Query(None, description="Filter by domain"),
    limit: int = Query(10, description="Maximum number of patterns to return")
) -> List[Dict[str, Any]]:
    """
    Get pattern performance metrics

    Args:
        domain: Optional domain filter
        limit: Maximum patterns to return

    Returns:
        List of top performing patterns
    """
    service = get_monitoring_service()
    patterns = await service.pattern_tracker.get_top_patterns(limit=limit)

    # Filter by domain if provided
    if domain:
        patterns = [p for p in patterns if domain.lower() in p.pattern_name.lower()]

    return [
        {
            "pattern_id": p.pattern_id,
            "pattern_name": p.pattern_name,
            "usage_count": p.usage_count,
            "success_count": p.success_count,
            "failure_count": p.failure_count,
            "success_rate": p.success_rate,
            "last_used": p.last_used,
            "trend": p.trend,
            "avg_improvement_percent": p.avg_improvement_percent,
            "total_value_added": p.total_value_added
        }
        for p in patterns
    ]


@router.get("/patterns/{pattern_id}/trends")
async def get_pattern_trends(
    pattern_id: str = Query(..., description="Pattern ID"),
    days: int = Query(30, description="Number of days to analyze")
) -> Dict[str, Any]:
    """
    Get trend data for a specific pattern

    Args:
        pattern_id: Pattern ID to analyze
        days: Number of days to include in trend

    Returns:
        Trend data with daily usage and success rates
    """
    service = get_monitoring_service()
    trends = await service.pattern_tracker.get_pattern_trends(pattern_id, days=days)

    return {
        "pattern_id": pattern_id,
        "days": days,
        "trends": trends
    }


# ============================================================================
# Cost Monitoring Endpoints
# ============================================================================

@router.get("/costs", response_model=CostBreakdownResponse)
async def get_cost_metrics(period: str = Query("30d", description="Time period: 1d, 7d, 30d")) -> Dict[str, Any]:
    """
    Get cost metrics

    Args:
        period: Time period for analysis (1d, 7d, 30d)

    Returns:
        Cost breakdown by provider and API type
    """
    service = get_monitoring_service()

    # Parse period
    days = int(period.replace('d', ''))
    total_cost = await service.cost_monitor.get_total_cost(days=days)
    breakdown = await service.cost_monitor.get_cost_breakdown()

    return {
        "timestamp": breakdown.timestamp,
        "total_cost": breakdown.total_cost,
        "by_provider": breakdown.by_provider,
        "by_type": breakdown.by_type,
        "monthly_projection": breakdown.monthly_projection,
        "cost_per_query": breakdown.cost_per_query,
        "cost_per_pattern_discovery": breakdown.cost_per_pattern_discovery
    }


@router.get("/costs/trends")
async def get_cost_trends(days: int = Query(30, description="Number of days to analyze")) -> Dict[str, Any]:
    """
    Get cost trends over time

    Args:
        days: Number of days to analyze

    Returns:
        Daily cost trends with percentage changes
    """
    service = get_monitoring_service()
    trends = await service.cost_monitor.get_cost_trends(days=days)

    return {
        "days": days,
        "trends": [
            {
                "date": trend.date.isoformat(),
                "total_cost": trend.total_cost,
                "by_provider": trend.by_provider,
                "trend_percent": trend.trend_percent
            }
            for trend in trends
        ]
    }


# ============================================================================
# Health & Alerts Endpoints
# ============================================================================

@router.get("/health", response_model=HealthStatusResponse)
async def get_health_status() -> Dict[str, Any]:
    """
    Get system health status

    Returns:
        Current system health status and active alert count
    """
    service = get_monitoring_service()
    health = await service.get_health_status()

    return {
        "timestamp": health.timestamp,
        "overall_health": health.overall_health,
        "rag_effectiveness_healthy": health.rag_effectiveness_healthy,
        "pattern_discovery_healthy": health.pattern_discovery_healthy,
        "cost_monitoring_healthy": health.cost_monitoring_healthy,
        "performance_healthy": health.performance_healthy,
        "error_rate_healthy": health.error_rate_healthy,
        "active_alerts": health.active_alerts,
        "critical_alerts": health.critical_alerts
    }


@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: info, warning, critical"),
    limit: int = Query(10, description="Maximum alerts to return")
) -> List[Dict[str, Any]]:
    """
    Get active system alerts

    Args:
        severity: Optional severity filter
        limit: Maximum alerts to return

    Returns:
        List of active alerts
    """
    service = get_monitoring_service()

    # Parse severity filter
    severity_enum = None
    if severity:
        try:
            severity_enum = AlertSeverity[severity.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid severity: {severity}")

    alerts = await service.get_alerts(severity=severity_enum, limit=limit)

    return [
        {
            "alert_id": alert.alert_id,
            "severity": alert.severity.value,
            "category": alert.category.value,
            "title": alert.title,
            "description": alert.description,
            "created_at": alert.created_at,
            "resolved_at": alert.resolved_at,
            "metrics": alert.metrics,
            "recommended_action": alert.recommended_action
        }
        for alert in alerts
    ]


@router.post("/alerts/check")
async def check_alerts() -> Dict[str, Any]:
    """
    Manually trigger alert checking

    Returns:
        Newly created alerts
    """
    service = get_monitoring_service()
    new_alerts = await service.check_and_create_alerts()

    return {
        "timestamp": datetime.now().isoformat(),
        "new_alerts_count": len(new_alerts),
        "alerts": [
            {
                "alert_id": alert.alert_id,
                "severity": alert.severity.value,
                "title": alert.title,
                "description": alert.description
            }
            for alert in new_alerts
        ]
    }


# ============================================================================
# System Metrics Endpoints
# ============================================================================

@router.get("/metrics", response_model=SystemMetricsResponse)
async def get_all_system_metrics() -> Dict[str, Any]:
    """
    Get all system metrics (performance + monitoring)

    Returns:
        Comprehensive system metrics including RAG, patterns, costs, and health
    """
    service = get_monitoring_service()
    metrics = await service.get_all_metrics()

    return {
        "timestamp": metrics.timestamp,
        "rag_effectiveness": {
            "timestamp": metrics.rag_effectiveness.timestamp,
            "effectiveness_score": metrics.rag_effectiveness.effectiveness_score,
            "retrieval_quality": {
                "timestamp": metrics.rag_effectiveness.retrieval_quality.timestamp,
                "accuracy": metrics.rag_effectiveness.retrieval_quality.accuracy,
                "relevance": metrics.rag_effectiveness.retrieval_quality.relevance,
                "diversity": metrics.rag_effectiveness.retrieval_quality.diversity,
                "latency_ms": metrics.rag_effectiveness.retrieval_quality.latency_ms,
                "success_rate": metrics.rag_effectiveness.retrieval_quality.success_rate
            },
            "pattern_accuracy": metrics.rag_effectiveness.pattern_accuracy,
            "recommendation_acceptance_rate": metrics.rag_effectiveness.recommendation_acceptance_rate,
            "total_queries": metrics.rag_effectiveness.total_queries,
            "successful_queries": metrics.rag_effectiveness.successful_queries,
            "failed_queries": metrics.rag_effectiveness.failed_queries,
            "avg_query_latency_ms": metrics.rag_effectiveness.avg_query_latency_ms
        },
        "top_patterns": [
            {
                "pattern_id": p.pattern_id,
                "pattern_name": p.pattern_name,
                "usage_count": p.usage_count,
                "success_count": p.success_count,
                "failure_count": p.failure_count,
                "success_rate": p.success_rate,
                "last_used": p.last_used,
                "trend": p.trend,
                "avg_improvement_percent": p.avg_improvement_percent,
                "total_value_added": p.total_value_added
            }
            for p in metrics.top_patterns
        ],
        "health_status": {
            "timestamp": metrics.health_status.timestamp,
            "overall_health": metrics.health_status.overall_health,
            "rag_effectiveness_healthy": metrics.health_status.rag_effectiveness_healthy,
            "pattern_discovery_healthy": metrics.health_status.pattern_discovery_healthy,
            "cost_monitoring_healthy": metrics.health_status.cost_monitoring_healthy,
            "performance_healthy": metrics.health_status.performance_healthy,
            "error_rate_healthy": metrics.health_status.error_rate_healthy,
            "active_alerts": metrics.health_status.active_alerts,
            "critical_alerts": metrics.health_status.critical_alerts
        },
        "cost_metrics": {
            "timestamp": metrics.cost_metrics.timestamp,
            "total_cost": metrics.cost_metrics.total_cost,
            "by_provider": metrics.cost_metrics.by_provider,
            "by_type": metrics.cost_metrics.by_type,
            "monthly_projection": metrics.cost_metrics.monthly_projection,
            "cost_per_query": metrics.cost_metrics.cost_per_query,
            "cost_per_pattern_discovery": metrics.cost_metrics.cost_per_pattern_discovery
        },
        "active_alerts": [
            {
                "alert_id": a.alert_id,
                "severity": a.severity.value,
                "category": a.category.value,
                "title": a.title,
                "description": a.description,
                "created_at": a.created_at,
                "resolved_at": a.resolved_at,
                "metrics": a.metrics,
                "recommended_action": a.recommended_action
            }
            for a in metrics.active_alerts
        ]
    }


# ============================================================================
# Health Check Endpoint
# ============================================================================

@router.get("/ping")
async def health_check() -> Dict[str, str]:
    """
    Simple health check endpoint

    Returns:
        Service status
    """
    return {
        "status": "ok",
        "service": "monitoring",
        "timestamp": datetime.now().isoformat()
    }
