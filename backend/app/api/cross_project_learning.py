"""
Cross-Project Learning API Endpoints

Endpoints for:
- Cross-project pattern discovery
- Domain-specific pattern libraries
- Hybrid search functionality
- Learning graph queries
"""

from typing import List, Dict, Any, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.database import get_session
from app.services.cross_project_pattern_service import get_cross_project_pattern_service
from app.services.domain_pattern_library_service import get_domain_pattern_library_service
from app.services.hybrid_search_service import get_hybrid_search_service
from app.services.learning_graph_builder_service import get_learning_graph_builder_service

router = APIRouter(prefix="/api/v1/learning", tags=["cross-project-learning"])


# ===== Request/Response Models =====

class PatternRecommendationRequest(BaseModel):
    """Request for pattern recommendations"""
    task_title: str
    task_description: str
    project_id: UUID


class DomainSearchRequest(BaseModel):
    """Request for domain-specific pattern search"""
    domain_key: str
    query: str
    complexity_level: Optional[str] = None


class HybridSearchRequest(BaseModel):
    """Request for hybrid search"""
    query: str
    entity_types: Optional[List[str]] = None
    top_k: int = 10


class CrossProjectPatternResponse(BaseModel):
    """Response containing cross-project patterns"""
    pattern_id: str
    pattern_name: str
    category: str
    success_rate: float
    usage_count: int
    project_count: int
    difficulty_level: str
    estimated_effort_minutes: int
    best_practices: List[str]
    effectiveness_score: float


# ===== Endpoints =====

@router.get("/patterns/cross-project")
async def get_cross_project_patterns(
    min_occurrences: int = Query(2, ge=1),
    min_success_rate: float = Query(0.7, ge=0, le=1),
    days_back: int = Query(90, ge=1),
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get patterns that occur across multiple projects.

    Args:
        min_occurrences: Minimum number of occurrences to consider
        min_success_rate: Minimum success rate threshold
        days_back: Only consider patterns from last N days
    """
    try:
        service = get_cross_project_pattern_service()

        patterns = await service.find_patterns_across_projects(
            session=session,
            min_occurrences=min_occurrences,
            min_success_rate=min_success_rate,
            days_back=days_back
        )

        return {
            "total_patterns": len(patterns),
            "patterns": [p.to_dict() for p in patterns],
            "timestamp": None
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/patterns/recommendations")
async def recommend_patterns_for_task(
    request: PatternRecommendationRequest,
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get pattern recommendations for a new task.

    Args:
        request: Task details and project ID

    Returns:
        List of recommended patterns with relevance scores
    """
    try:
        service = get_cross_project_pattern_service()

        recommendations = await service.recommend_patterns_for_task(
            session=session,
            task_title=request.task_title,
            task_description=request.task_description,
            project_id=request.project_id
        )

        return {
            "task_title": request.task_title,
            "project_id": str(request.project_id),
            "recommendation_count": len(recommendations),
            "recommendations": recommendations
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/patterns/statistics")
async def get_pattern_statistics(
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Get statistics about all cross-project patterns"""
    try:
        service = get_cross_project_pattern_service()
        stats = await service.get_pattern_statistics(session)
        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/domains")
async def list_all_domains(
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get all available domain pattern libraries.

    Returns:
        List of domain libraries with metadata
    """
    try:
        service = get_domain_pattern_library_service()
        libraries = await service.get_all_libraries(session)

        return {
            "domain_count": len(libraries),
            "domains": [
                {
                    "domain_key": key,
                    "domain_name": lib.domain_name,
                    "description": lib.description,
                    "pattern_count": len(lib.patterns),
                    "keywords": lib.keywords
                }
                for key, lib in libraries.items()
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/domains/{domain_key}")
async def get_domain_library(
    domain_key: str,
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get patterns for a specific domain.

    Args:
        domain_key: Key of the domain (e.g., 'ecommerce', 'saas')
    """
    try:
        service = get_domain_pattern_library_service()
        library = await service.get_library_by_domain(session, domain_key)

        if not library:
            raise HTTPException(status_code=404, detail=f"Domain not found: {domain_key}")

        return library.to_dict()

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/domains/search")
async def search_domain_patterns(
    request: DomainSearchRequest,
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Search for patterns within a specific domain.

    Args:
        request: Domain key and search query
    """
    try:
        service = get_domain_pattern_library_service()

        patterns = await service.search_patterns_in_domain(
            session=session,
            domain_key=request.domain_key,
            query=request.query
        )

        # Filter by complexity if specified
        if request.complexity_level:
            patterns = [
                p for p in patterns
                if (
                    (request.complexity_level == "Easy" and p.get("success_score", 0) >= 0.8) or
                    (request.complexity_level == "Medium" and 0.6 <= p.get("success_score", 0) < 0.8) or
                    (request.complexity_level == "Hard" and p.get("success_score", 0) < 0.6)
                )
            ]

        return {
            "domain": request.domain_key,
            "query": request.query,
            "result_count": len(patterns),
            "patterns": patterns
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/domains/{domain_key}/statistics")
async def get_domain_statistics(
    domain_key: str,
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Get statistics for a domain pattern library"""
    try:
        service = get_domain_pattern_library_service()
        stats = await service.get_library_statistics(session, domain_key)

        if not stats:
            raise HTTPException(status_code=404, detail=f"Domain not found: {domain_key}")

        return stats

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/hybrid")
async def hybrid_search(
    request: HybridSearchRequest,
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Perform hybrid search combining vector and keyword matching.

    Args:
        request: Search query and parameters
    """
    try:
        service = get_hybrid_search_service()

        results = await service.hybrid_search(
            session=session,
            query=request.query,
            entity_types=request.entity_types,
            top_k=request.top_k
        )

        return {
            "query": request.query,
            "result_count": len(results),
            "results": [r.to_dict() for r in results]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph")
async def get_learning_graph(
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get the learning graph representing cross-project relationships.

    Returns:
        Learning graph with nodes and edges
    """
    try:
        service = get_learning_graph_builder_service()
        graph = await service.get_graph(session)

        return graph.to_dict()

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/statistics")
async def get_graph_statistics(
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """Get statistics about the learning graph"""
    try:
        service = get_learning_graph_builder_service()
        stats = await service.get_node_statistics(session)

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/graph/path")
async def find_learning_path(
    start_node_id: str = Query(...),
    target_node_id: str = Query(...),
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Find a learning path between two nodes in the graph.

    Args:
        start_node_id: ID of start node
        target_node_id: ID of target node

    Returns:
        Path of nodes from start to target
    """
    try:
        service = get_learning_graph_builder_service()

        path = await service.find_learning_path(
            session=session,
            start_node_id=start_node_id,
            target_node_id=target_node_id
        )

        if not path:
            return {
                "start_node_id": start_node_id,
                "target_node_id": target_node_id,
                "path_found": False,
                "path": []
            }

        return {
            "start_node_id": start_node_id,
            "target_node_id": target_node_id,
            "path_found": True,
            "path_length": len(path),
            "path": [n.to_dict() for n in path]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/domains/recommendations")
async def recommend_domains_for_project(
    project_name: str = Query(...),
    project_description: str = Query(...),
    session: AsyncSession = Depends(get_session)
) -> Dict[str, Any]:
    """
    Get domain library recommendations for a new project.

    Args:
        project_name: Name of the project
        project_description: Description of the project
    """
    try:
        service = get_domain_pattern_library_service()

        recommendations = await service.recommend_domains_for_project(
            session=session,
            project_name=project_name,
            project_description=project_description
        )

        return {
            "project_name": project_name,
            "recommendation_count": len(recommendations),
            "recommendations": recommendations
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint for Phase 4 services"""
    return {
        "status": "healthy",
        "service": "cross-project-learning",
        "features": ["cross-project-patterns", "domain-libraries", "hybrid-search", "learning-graph"]
    }
