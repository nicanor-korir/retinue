"""
Performance monitoring API endpoints.

Provides REST endpoints for:
- Aggregated performance statistics
- Agent and project-specific metrics
- Performance trends and anomalies
- Metrics export
"""

from typing import Optional
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel, Field

from app.services.rag_performance_monitor import (
    get_performance_monitor,
    MetricType,
    AnomalyLevel,
)

router = APIRouter(
    prefix="/api/v1/performance",
    tags=["rag-performance"],
    responses={404: {"description": "Not found"}},
)


class StatsResponse(BaseModel):
    """Response with aggregated statistics."""
    period: str
    total_retrievals: int
    latency: dict = Field(..., description="Latency percentiles (ms)")
    quality: dict = Field(..., description="Quality score statistics")
    cache: dict = Field(..., description="Cache hit/miss rates")
    optimization: dict = Field(..., description="Optimization metrics")
    errors: dict = Field(..., description="Error tracking")
    enhancement: dict = Field(..., description="Query enhancement metrics")
    anomalies: dict = Field(..., description="Anomaly counts")


class AgentStatsResponse(BaseModel):
    """Response with agent-specific statistics."""
    agent_id: str
    total_retrievals: int
    avg_latency_ms: float
    cache_hit_rate: float
    avg_quality_score: float
    error_count: int


class ProjectStatsResponse(BaseModel):
    """Response with project-specific statistics."""
    project_id: str
    total_retrievals: int
    avg_latency_ms: float
    cache_hit_rate: float
    total_tokens_used: int


class TrendResponse(BaseModel):
    """Response with performance trend data."""
    metric: str
    period: str
    timestamps: list = Field(..., description="Time bucket timestamps")
    values: list = Field(..., description="Metric values per bucket")


class AnomalyResponse(BaseModel):
    """Single anomaly record."""
    timestamp: str
    level: str
    message: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    metrics_recorded: int
    latest_retrieval: Optional[str] = None


@router.get("/stats", response_model=StatsResponse)
async def get_stats(period: str = Query("all", description="Time period: all, 1h, 24h, 7d")):
    """
    Get aggregated performance statistics.

    Query Parameters:
    - period: Time period for statistics (all, 1h, 24h, 7d)

    Returns:
    - Latency percentiles (mean, median, p95, p99)
    - Quality scores (mean, median, min, max)
    - Cache hit rates
    - Optimization metrics
    - Error rates
    - Anomaly counts
    """
    monitor = get_performance_monitor()
    stats = monitor.get_stats(period=period)

    if "error" in stats:
        raise HTTPException(status_code=400, detail=stats["error"])

    return StatsResponse(**stats)


@router.get("/agents/{agent_id}/stats", response_model=AgentStatsResponse)
async def get_agent_stats(agent_id: str):
    """
    Get statistics for a specific agent.

    Parameters:
    - agent_id: Identifier of the agent

    Returns:
    - Total retrievals performed
    - Average latency
    - Cache hit rate
    - Average quality score
    - Error count
    """
    monitor = get_performance_monitor()
    stats = monitor.get_agent_stats(agent_id)

    if "message" in stats:
        raise HTTPException(status_code=404, detail=stats["message"])

    return AgentStatsResponse(**stats)


@router.get("/projects/{project_id}/stats", response_model=ProjectStatsResponse)
async def get_project_stats(project_id: str):
    """
    Get statistics for a specific project.

    Parameters:
    - project_id: Identifier of the project

    Returns:
    - Total retrievals in project
    - Average retrieval latency
    - Cache hit rate
    - Total tokens used
    """
    monitor = get_performance_monitor()
    stats = monitor.get_project_stats(project_id)

    if "message" in stats:
        raise HTTPException(status_code=404, detail=stats["message"])

    return ProjectStatsResponse(**stats)


@router.get("/queries/top", response_model=dict)
async def get_top_queries(limit: int = Query(10, ge=1, le=100)):
    """
    Get most frequently executed queries.

    Query Parameters:
    - limit: Number of top queries to return (1-100)

    Returns:
    List of (query, frequency) tuples sorted by frequency.
    """
    monitor = get_performance_monitor()
    top_queries = monitor.get_top_queries(limit=limit)

    return {
        "limit": limit,
        "queries": [
            {"query": q, "frequency": count}
            for q, count in top_queries
        ]
    }


@router.get("/anomalies", response_model=dict)
async def get_anomalies(
    level: Optional[str] = Query(None, description="Filter by level: warning, critical"),
    limit: int = Query(10, ge=1, le=100),
):
    """
    Get recent anomalies detected in system performance.

    Query Parameters:
    - level: Filter by severity (warning, critical) - optional
    - limit: Number of anomalies to return (1-100)

    Returns:
    List of anomalies with timestamp, level, and description.
    """
    monitor = get_performance_monitor()

    # Parse level filter
    level_enum = None
    if level:
        try:
            level_enum = AnomalyLevel(level.lower())
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid level: {level}. Must be 'warning' or 'critical'"
            )

    anomalies = monitor.get_anomalies(level=level_enum, limit=limit)

    return {
        "limit": limit,
        "level_filter": level,
        "anomalies": [
            {
                "timestamp": str(timestamp),
                "level": level_str,
                "message": message
            }
            for timestamp, level_str, message in anomalies
        ]
    }


@router.get("/trends/{metric}", response_model=TrendResponse)
async def get_performance_trend(
    metric: str = "latency",
    period: str = Query("24h", description="Time period: 1h, 24h, 7d"),
    bucket_size: int = Query(15, ge=1, le=60, description="Bucket size in minutes"),
):
    """
    Get performance trend for a specific metric over time.

    Path Parameters:
    - metric: Metric to track (latency, quality, cache_hit, compression, token_count, error)

    Query Parameters:
    - period: Time period (1h, 24h, 7d)
    - bucket_size: Time bucket size in minutes (1-60)

    Returns:
    - Timestamps of buckets
    - Average metric values per bucket
    """
    monitor = get_performance_monitor()

    # Map metric name to enum
    metric_map = {
        "latency": MetricType.RETRIEVAL_LATENCY,
        "quality": MetricType.QUALITY_SCORE,
        "cache_hit": MetricType.CACHE_HIT_RATE,
        "compression": MetricType.COMPRESSION_RATIO,
        "token_count": MetricType.TOKEN_COUNT,
        "error": MetricType.ERROR_RATE,
    }

    if metric not in metric_map:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown metric: {metric}. Must be one of: {', '.join(metric_map.keys())}"
        )

    trend = monitor.get_performance_trend(
        metric=metric_map[metric],
        period=period,
        bucket_size_minutes=bucket_size,
    )

    if "error" in trend:
        raise HTTPException(status_code=400, detail=trend["error"])

    return TrendResponse(**trend)


@router.get("/export", response_model=dict)
async def export_metrics(format: str = Query("json", description="Export format: json, csv")):
    """
    Export all performance metrics.

    Query Parameters:
    - format: Export format (json, csv)

    Returns:
    - Metrics in requested format
    - Includes timestamp of export
    """
    monitor = get_performance_monitor()

    if format not in ["json", "csv"]:
        raise HTTPException(
            status_code=400,
            detail="Format must be 'json' or 'csv'"
        )

    exported = monitor.export_metrics(format=format)

    return {
        "format": format,
        "size_bytes": len(exported),
        "data": exported,
    }


@router.post("/reset")
async def reset_metrics():
    """
    Reset all collected performance metrics.

    WARNING: This operation is irreversible.

    Returns:
    - Confirmation message
    """
    monitor = get_performance_monitor()
    monitor.reset_metrics()

    return {
        "status": "success",
        "message": "All performance metrics have been reset"
    }


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check for performance monitoring service.

    Returns:
    - Service status
    - Number of metrics recorded
    - Latest retrieval timestamp
    """
    monitor = get_performance_monitor()

    latest_retrieval = None
    if monitor.metrics:
        latest = max(monitor.metrics, key=lambda m: m.timestamp)
        latest_retrieval = latest.timestamp.isoformat()

    return HealthResponse(
        status="healthy",
        metrics_recorded=len(monitor.metrics),
        latest_retrieval=latest_retrieval,
    )


@router.get("/info", response_model=dict)
async def get_monitoring_info():
    """
    Get performance monitoring configuration and status.

    Returns:
    - Monitoring configuration
    - Alert thresholds
    - History size
    - Currently tracked entities
    """
    monitor = get_performance_monitor()

    return {
        "status": "active",
        "history_size": monitor.history_size,
        "current_metrics_count": len(monitor.metrics),
        "thresholds": {
            "latency_ms": monitor.latency_threshold_ms,
            "quality_score_min": monitor.quality_threshold,
            "error_rate_max": monitor.error_threshold,
            "cache_hit_rate_min": monitor.cache_hit_threshold,
        },
        "tracked_agents": len(monitor.agent_stats),
        "tracked_projects": len(monitor.project_stats),
        "unique_queries": len(monitor.query_frequency),
        "anomalies_detected": len(monitor.anomalies),
    }
