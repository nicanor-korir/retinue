"""
Project Learnings API Endpoints - Phase 2 Component 3

Provides endpoints for accessing project learnings and metrics:
- Extract learnings from completed projects
- Retrieve project metrics
- Get learnings by type or tag
- Store learnings for future reference
"""

import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.database import get_session
from app.services.project_learnings_service import get_project_learnings_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/projects", tags=["project-learnings"])


# Pydantic models
class LearningItem(BaseModel):
    """A single learning extracted from a project."""
    project_id: str
    learning_type: str
    title: str
    description: str
    evidence: list
    relevance_score: float
    tags: list


class ProjectLearningsResponse(BaseModel):
    """Response with extracted learnings."""
    project_id: str
    total_learnings: int
    by_type: dict
    learnings: list[LearningItem]


class ProjectMetricsResponse(BaseModel):
    """Response with project metrics."""
    project_id: str
    timeline: dict
    tasks: dict
    decisions: dict
    escalations: dict
    success_score: float


class ExtractLearningsRequest(BaseModel):
    """Request to extract learnings from a project."""
    include_metrics: bool = True


# Endpoints

@router.post("/{project_id}/learnings/extract")
async def extract_project_learnings(
    project_id: UUID,
    request: ExtractLearningsRequest,
    session: AsyncSession = Depends(get_session),
) -> ProjectLearningsResponse:
    """
    Extract learnings from a completed project.

    Analyzes the project execution data and extracts insights including:
    - Best practices discovered
    - Patterns identified
    - Risks encountered
    - Areas for improvement

    Args:
        project_id: Project ID to extract learnings from
        request: Request parameters

    Returns:
        ProjectLearningsResponse with extracted learnings
    """
    try:
        service = get_project_learnings_service()

        # Extract learnings
        learnings = await service.extract_learnings_from_project(
            session=session,
            project_id=project_id,
        )

        # Save learnings
        result = await service.save_learnings(
            project_id=project_id,
            learnings=learnings,
        )

        # Add metrics if requested
        if request.include_metrics:
            metrics = await service.calculate_project_metrics(
                session=session,
                project_id=project_id,
            )
            result["metrics"] = metrics

        return ProjectLearningsResponse(**result)

    except Exception as e:
        logger.error(f"Error extracting learnings for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to extract learnings",
        )


@router.get("/{project_id}/learnings")
async def get_project_learnings(
    project_id: UUID,
    learning_type: str | None = None,
    tag: str | None = None,
    session: AsyncSession = Depends(get_session),
) -> ProjectLearningsResponse:
    """
    Get stored learnings for a project.

    Args:
        project_id: Project ID
        learning_type: Filter by learning type (best_practice, pattern, risk, improvement)
        tag: Filter by tag

    Returns:
        ProjectLearningsResponse with filtered learnings
    """
    try:
        service = get_project_learnings_service()

        # Get learnings
        learnings = await service.extract_learnings_from_project(
            session=session,
            project_id=project_id,
        )

        # Filter by type if specified
        if learning_type:
            learnings = [l for l in learnings if l.learning_type == learning_type]

        # Filter by tag if specified
        if tag:
            learnings = [l for l in learnings if tag in l.tags]

        # Save and return
        result = await service.save_learnings(
            project_id=project_id,
            learnings=learnings,
        )

        return ProjectLearningsResponse(**result)

    except Exception as e:
        logger.error(f"Error getting learnings for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve learnings",
        )


@router.get("/{project_id}/metrics")
async def get_project_metrics(
    project_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> ProjectMetricsResponse:
    """
    Get comprehensive metrics for a completed project.

    Returns metrics including:
    - Timeline: planned vs actual, efficiency
    - Tasks: completion rate
    - Decisions: approval rate
    - Escalations: resolution rate
    - Success score: overall project performance

    Args:
        project_id: Project ID

    Returns:
        ProjectMetricsResponse with project metrics
    """
    try:
        service = get_project_learnings_service()

        metrics = await service.calculate_project_metrics(
            session=session,
            project_id=project_id,
        )

        if "error" in metrics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=metrics["error"],
            )

        return ProjectMetricsResponse(**metrics)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to calculate metrics",
        )


@router.post("/{project_id}/learnings/apply")
async def apply_learnings_to_project(
    project_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Apply learnings from a completed project to create improvement recommendations
    for similar ongoing or future projects.

    Args:
        project_id: Completed project ID

    Returns:
        Status and recommendations
    """
    try:
        service = get_project_learnings_service()

        # Extract learnings
        learnings = await service.extract_learnings_from_project(
            session=session,
            project_id=project_id,
        )

        if not learnings:
            return {
                "status": "no_learnings",
                "message": "No significant learnings extracted from this project",
                "project_id": str(project_id),
            }

        # Group by type
        by_type = {}
        for learning in learnings:
            if learning.learning_type not in by_type:
                by_type[learning.learning_type] = []
            by_type[learning.learning_type].append(learning.to_dict())

        return {
            "status": "success",
            "project_id": str(project_id),
            "total_learnings": len(learnings),
            "learnings_by_type": by_type,
            "applied_at": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"Error applying learnings for project {project_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to apply learnings",
        )


# Helper endpoint to get learnings summary across all projects
@router.get("/learnings/summary")
async def get_learnings_summary(
    session: AsyncSession = Depends(get_session),
) -> dict:
    """
    Get a summary of all learnings across completed projects.

    Returns:
        Summary of learning types, tags, and statistics
    """
    try:
        return {
            "status": "success",
            "message": "This endpoint would aggregate learnings across all projects",
            "note": "Implementation depends on learning storage backend",
        }

    except Exception as e:
        logger.error(f"Error getting learnings summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve learnings summary",
        )


# Import datetime for timestamps
from datetime import datetime
