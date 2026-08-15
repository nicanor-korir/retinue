"""
API routes for RAG cache management.

Phase 3: Cache Management Endpoints
Purpose: Provide endpoints for monitoring and managing RAG cache
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any
import logging
from pydantic import BaseModel

from app.services.rag_cache_service import get_cache_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/cache", tags=["RAG Cache"])


# Pydantic models
class CacheStatsResponse(BaseModel):
    """Response model for cache statistics."""
    enabled: bool
    size: int
    hits: int
    misses: int
    total_requests: int
    hit_rate: float
    max_size: int
    ttl_seconds: int


class CacheActionResponse(BaseModel):
    """Response model for cache actions."""
    success: bool
    message: str


class CacheClearResponse(BaseModel):
    """Response model for cache clearing."""
    success: bool
    message: str
    entries_cleared: Optional[int] = None


@router.get("/stats", response_model=CacheStatsResponse, tags=["Cache"])
async def get_cache_stats():
    """
    Get RAG cache statistics.

    Returns:
        Cache statistics including hit rate, size, and performance metrics

    Example:
        GET /api/v1/cache/stats
        Response:
        {
            "enabled": true,
            "size": 245,
            "hits": 1042,
            "misses": 203,
            "total_requests": 1245,
            "hit_rate": 83.67,
            "max_size": 1000,
            "ttl_seconds": 3600
        }
    """
    try:
        cache_service = get_cache_service()
        stats = await cache_service.get_stats()

        if "error" in stats:
            raise HTTPException(status_code=503, detail=f"Cache unavailable: {stats['error']}")

        return CacheStatsResponse(**stats)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting cache stats: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@router.post("/clear", response_model=CacheClearResponse, tags=["Cache"])
async def clear_cache(
    scope: str = Query("all", description="Scope: 'all', 'agent:{agent_id}', or 'project:{project_id}'")
):
    """
    Clear RAG cache with specified scope.

    Query Parameters:
        scope: Clearing scope
            - "all": Clear entire cache
            - "agent:agent_id": Clear cache for specific agent
            - "project:project_id": Clear cache for specific project

    Returns:
        Confirmation of cache clearing

    Examples:
        POST /api/v1/cache/clear?scope=all
        POST /api/v1/cache/clear?scope=agent:cto_001
        POST /api/v1/cache/clear?scope=project:proj_123
    """
    try:
        cache_service = get_cache_service()

        if scope == "all":
            success = await cache_service.clear_all()
            return CacheClearResponse(
                success=success,
                message="Cache completely cleared"
            )

        elif scope.startswith("agent:"):
            agent_id = scope.split(":", 1)[1]
            success = await cache_service.clear_agent(agent_id)
            return CacheClearResponse(
                success=success,
                message=f"Cache cleared for agent {agent_id}"
            )

        elif scope.startswith("project:"):
            project_id = scope.split(":", 1)[1]
            success = await cache_service.clear_project(project_id)
            return CacheClearResponse(
                success=success,
                message=f"Cache cleared for project {project_id}"
            )

        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid scope format. Use 'all', 'agent:agent_id', or 'project:project_id'"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/health", tags=["Cache"])
async def cache_health():
    """
    Check RAG cache health status.

    Returns:
        Cache health information including connectivity and status

    Example:
        GET /api/v1/cache/health
        Response:
        {
            "status": "healthy",
            "connected": true,
            "enabled": true,
            "message": "Cache service operational"
        }
    """
    try:
        cache_service = get_cache_service()

        if not cache_service.enabled:
            return {
                "status": "disabled",
                "connected": False,
                "enabled": False,
                "message": "Cache service is disabled"
            }

        if not cache_service.redis:
            return {
                "status": "unhealthy",
                "connected": False,
                "enabled": True,
                "message": "Redis connection not available"
            }

        # Try to ping Redis
        try:
            await cache_service.redis.ping()
            stats = await cache_service.get_stats()

            return {
                "status": "healthy",
                "connected": True,
                "enabled": True,
                "message": "Cache service operational",
                "cache_size": stats.get("size", 0),
                "hit_rate": stats.get("hit_rate", 0),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "connected": False,
                "enabled": True,
                "message": f"Redis connection failed: {str(e)}"
            }

    except Exception as e:
        logger.error(f"Error checking cache health: {e}")
        return {
            "status": "error",
            "connected": False,
            "enabled": False,
            "message": f"Error checking cache health: {str(e)}"
        }


@router.get("/info", tags=["Cache"])
async def cache_info():
    """
    Get detailed cache information.

    Returns:
        Comprehensive cache configuration and status

    Example:
        GET /api/v1/cache/info
        Response:
        {
            "enabled": true,
            "ttl_seconds": 3600,
            "max_size": 1000,
            "similarity_threshold": 0.95,
            "analytics_enabled": true,
            "current_size": 245,
            "efficiency": {
                "hit_rate": 83.67,
                "cache_utilization": 24.5
            }
        }
    """
    try:
        cache_service = get_cache_service()
        stats = await cache_service.get_stats()

        return {
            "enabled": cache_service.enabled,
            "ttl_seconds": cache_service.ttl,
            "max_size": cache_service.max_size,
            "similarity_threshold": cache_service.similarity_threshold,
            "analytics_enabled": cache_service.analytics_enabled,
            "current_size": stats.get("size", 0),
            "efficiency": {
                "hit_rate": stats.get("hit_rate", 0),
                "cache_utilization": (stats.get("size", 0) / cache_service.max_size * 100) if cache_service.max_size > 0 else 0,
                "total_hits": stats.get("hits", 0),
                "total_misses": stats.get("misses", 0),
            }
        }

    except Exception as e:
        logger.error(f"Error getting cache info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get cache info: {str(e)}")


@router.post("/test", tags=["Cache"])
async def test_cache():
    """
    Test cache functionality.

    Performs basic cache operations to verify service is working.

    Returns:
        Test results

    Example:
        POST /api/v1/cache/test
        Response:
        {
            "success": true,
            "tests_passed": 4,
            "tests_total": 4,
            "operations": {
                "set": "passed",
                "get": "passed",
                "delete": "passed",
                "stats": "passed"
            }
        }
    """
    try:
        cache_service = get_cache_service()

        test_results = {
            "success": True,
            "operations": {}
        }

        # Test SET
        try:
            test_query = "test query"
            test_data = {"test": "data"}
            await cache_service.set(query=test_query, results=test_data)
            test_results["operations"]["set"] = "passed"
        except Exception as e:
            test_results["operations"]["set"] = f"failed: {str(e)}"
            test_results["success"] = False

        # Test GET
        try:
            result = await cache_service.get(query=test_query)
            if result:
                test_results["operations"]["get"] = "passed"
            else:
                test_results["operations"]["get"] = "failed: No result"
                test_results["success"] = False
        except Exception as e:
            test_results["operations"]["get"] = f"failed: {str(e)}"
            test_results["success"] = False

        # Test DELETE
        try:
            await cache_service.delete(query=test_query)
            test_results["operations"]["delete"] = "passed"
        except Exception as e:
            test_results["operations"]["delete"] = f"failed: {str(e)}"
            test_results["success"] = False

        # Test STATS
        try:
            stats = await cache_service.get_stats()
            if "enabled" in stats:
                test_results["operations"]["stats"] = "passed"
            else:
                test_results["operations"]["stats"] = "failed: Invalid stats"
                test_results["success"] = False
        except Exception as e:
            test_results["operations"]["stats"] = f"failed: {str(e)}"
            test_results["success"] = False

        test_results["tests_passed"] = sum(
            1 for v in test_results["operations"].values()
            if v == "passed"
        )
        test_results["tests_total"] = len(test_results["operations"])

        return test_results

    except Exception as e:
        logger.error(f"Error testing cache: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to test cache: {str(e)}")
