"""
Project Similarity API Endpoints - Phase 2 Component 4

Provides endpoints for finding similar projects and getting recommendations:
- Find similar past projects
- Get recommendations based on learnings
- Track knowledge reuse and ROI
"""

import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.database import get_session
from app.services.project_similarity_service import get_project_similarity_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/projects", tags=["project-similarity"])


# Pydantic models
class SimilarProjectItem(BaseModel):
    """A similar project."""
    project_id: str
    name: str
    similarity_score: float
    learnings: list
    metrics: dict


class SimilarProjectsResponse(BaseModel):
    """Response with similar projects."""
    project_id: str
    similar_projects: list[SimilarProjectItem]
    total_found: int
    average_similarity: float


class RecommendationItem(BaseModel):
    """A single recommendation."""
    title: str
    description: str
    category: str
    confidence: float
    source_projects: list[str]
    evidence: list[str]
    created_at: str


class RecommendationsResponse(BaseModel):
    """Response with recommendations."""
    project_id: str
    recommendations: list[RecommendationItem]
    average_similarity: float
    total_recommendations: int


class KnowledgeReuseResponse(BaseModel):
    """Response with knowledge reuse insights."""
    project_id: str
    similar_projects_count: int
    average_similarity: float
    average_success_rate: float
    total_applicable_learnings: int
    knowledge_reuse_potential: str
    estimated_time_savings_hours: float
    estimated_cost_savings_percent: float


# Endpoints

@router.get("/{project_id}/similar")
async def find_similar_projects(
    project_id: UUID,
    top_k: int = Query(5, ge=1, le=20),
    min_similarity: float = Query(0.6, ge=0.0, le=1.0),
    session: AsyncSession = Depends(get_session),
) -> SimilarProjectsResponse:
    """
    Find similar completed projects.

    Uses vector similarity to find projects with similar characteristics,
    then retrieves learnings from those projects.

    Args:
        project_id: Current project ID
        top_k: Number of similar projects to return (1-20, default: 5)
        min_similarity: Minimum similarity score threshold (0-1, default: 0.6)
        session: Database session

    Returns:
        SimilarProjectsResponse with similar projects and their learnings
    """
    try:
        # Get current project for context
        from app.db.models import Project
        from sqlalchemy import select

        result = await session.execute(
            select(Project).where(Project.project_id == project_id)
        )
        current_project = result.scalar_one_or_none()

        if not current_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        service = get_project_similarity_service()

        # Find similar projects
        similar_projects = await service.find_similar_projects(
            session=session,
            project_id=project_id,
            name=current_project.name,
            description=current_project.description or "",
            top_k=top_k,
            min_similarity=min_similarity,
        )

        if not similar_projects:
            return SimilarProjectsResponse(
                project_id=str(project_id),
                similar_projects=[],
                total_found=0,
                average_similarity=0.0,
            )

        avg_similarity = sum(p.similarity_score for p in similar_projects) / len(
            similar_projects
        )

        return SimilarProjectsResponse(
            project_id=str(project_id),
            similar_projects=[p.to_dict() for p in similar_projects],
            total_found=len(similar_projects),
            average_similarity=round(avg_similarity, 2),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar projects for {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to find similar projects",
        )


@router.get("/{project_id}/recommendations")
async def get_project_recommendations(
    project_id: UUID,
    top_k: int = Query(5, ge=1, le=20),
    session: AsyncSession = Depends(get_session),
) -> RecommendationsResponse:
    """
    Get recommendations based on similar projects.

    Analyzes learnings from similar projects and creates actionable
    recommendations for the current project.

    Args:
        project_id: Project ID to get recommendations for
        top_k: Number of similar projects to consider (1-20, default: 5)
        session: Database session

    Returns:
        RecommendationsResponse with actionable recommendations
    """
    try:
        # Get current project for context
        from app.db.models import Project
        from sqlalchemy import select

        result = await session.execute(
            select(Project).where(Project.project_id == project_id)
        )
        current_project = result.scalar_one_or_none()

        if not current_project:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Project not found",
            )

        service = get_project_similarity_service()

        # Generate recommendations
        recommendations, avg_similarity = await service.generate_recommendations(
            session=session,
            project_id=project_id,
            name=current_project.name,
            description=current_project.description or "",
            top_k=top_k,
        )

        return RecommendationsResponse(
            project_id=str(project_id),
            recommendations=[r.to_dict() for r in recommendations],
            average_similarity=round(avg_similarity, 2),
            total_recommendations=len(recommendations),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recommendations for {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate recommendations",
        )


@router.get("/{project_id}/knowledge-reuse")
async def get_knowledge_reuse_insights(
    project_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> KnowledgeReuseResponse:
    """
    Get knowledge reuse insights and ROI from similar projects.

    Calculates potential time and cost savings from applying learnings
    from similar projects.

    Args:
        project_id: Project ID
        session: Database session

    Returns:
        KnowledgeReuseResponse with reuse metrics and savings estimates
    """
    try:
        service = get_project_similarity_service()

        insights = await service.get_knowledge_reuse_insights(
            session=session,
            project_id=project_id,
        )

        if "error" in insights:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=insights["error"],
            )

        return KnowledgeReuseResponse(**insights)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge reuse insights for {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate knowledge reuse insights",
        )
