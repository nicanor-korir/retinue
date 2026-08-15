"""API routes for user feedback and context management."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, Optional, List
from uuid import UUID
import logging

from app.db.database import get_session
from app.services.feedback_service import FeedbackService
from app.db.feedback_models import FeedbackType, FeedbackStatus
from app.exceptions import ValidationError, NotFoundError
from app.utils.api_errors import handle_api_errors
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(tags=["feedback"])


# ==================== Pydantic Models ====================

class FeedbackBase(BaseModel):
    """Base feedback model."""
    title: str
    description: str
    context: Optional[Dict[str, Any]] = None


class ProjectFeedbackCreate(FeedbackBase):
    """Create project feedback."""
    feedback_type: str
    quality_rating: Optional[int] = None  # 1-5
    satisfaction_rating: Optional[int] = None  # 1-5
    confidence_level: Optional[int] = None  # 1-5
    suggested_actions: Optional[List[str]] = None
    priority: str = "medium"


class TaskFeedbackCreate(FeedbackBase):
    """Create task feedback."""
    feedback_type: str
    output_quality: Optional[int] = None  # 1-5
    correctness: Optional[int] = None  # 1-5
    completeness: Optional[int] = None  # 1-5
    implementation_quality: Optional[int] = None  # 1-5
    code_review_feedback: Optional[str] = None
    suggested_improvements: Optional[List[str]] = None
    action_items: Optional[List[str]] = None
    priority: str = "medium"


class AgentFeedbackCreate(FeedbackBase):
    """Create agent feedback."""
    feedback_type: str
    decision_quality: Optional[int] = None  # 1-5
    execution_quality: Optional[int] = None  # 1-5
    communication_clarity: Optional[int] = None  # 1-5
    problem_solving: Optional[int] = None  # 1-5
    efficiency: Optional[int] = None  # 1-5
    behavior_observations: Optional[str] = None
    recommended_improvements: Optional[List[str]] = None
    strengths_noted: Optional[List[str]] = None
    suggested_system_prompt_updates: Optional[str] = None
    priority: str = "medium"
    related_task_id: Optional[str] = None
    related_project_id: Optional[str] = None


class ContextUpdateCreate(BaseModel):
    """Create context update."""
    title: str
    content: str
    context_tags: Optional[List[str]] = None


class FeedbackStatusUpdate(BaseModel):
    """Update feedback status."""
    status: str
    implementation_notes: Optional[str] = None


# ==================== Response Models ====================

class FeedbackResponse(BaseModel):
    """Feedback response."""
    feedback_id: str
    status: str
    priority: str
    created_at: str
    title: str
    description: str


# ==================== Dependencies ====================

async def get_feedback_service(session: AsyncSession = Depends(get_session)) -> FeedbackService:
    """Get feedback service."""
    return FeedbackService(session)


# ==================== PROJECT FEEDBACK ENDPOINTS ====================

@router.post("/projects/{project_id}/feedback", response_model=FeedbackResponse)
@handle_api_errors
async def create_project_feedback(
    project_id: UUID,
    feedback: ProjectFeedbackCreate,
    feedback_service: FeedbackService = Depends(get_feedback_service),
    user_id: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Create feedback for a project.

    Args:
        project_id: Project ID
        feedback: Feedback data
        feedback_service: Feedback service
        user_id: User creating feedback

    Returns:
        Created feedback response
    """
    # Validate feedback type
    try:
        feedback_type = FeedbackType(feedback.feedback_type)
    except ValueError:
        valid_types = [ft.value for ft in FeedbackType]
        raise ValidationError(
            message=f"Invalid feedback type '{feedback.feedback_type}'.",
            field="feedback_type",
            details={"valid_types": valid_types}
        )

    # Validate title and description
    if not feedback.title or not feedback.title.strip():
        raise ValidationError(
            message="Title is required.",
            field="title"
        )

    if not feedback.description or not feedback.description.strip():
        raise ValidationError(
            message="Description is required.",
            field="description"
        )

    created_feedback = await feedback_service.create_project_feedback(
        project_id=project_id,
        feedback_type=feedback_type,
        title=feedback.title,
        description=feedback.description,
        quality_rating=feedback.quality_rating,
        satisfaction_rating=feedback.satisfaction_rating,
        confidence_level=feedback.confidence_level,
        suggested_actions=feedback.suggested_actions,
        priority=feedback.priority,
        context=feedback.context,
        created_by_user=user_id,
    )

    return {
        "feedback_id": str(created_feedback.feedback_id),
        "status": created_feedback.status.value,
        "priority": created_feedback.priority,
        "created_at": created_feedback.created_at.isoformat(),
        "title": created_feedback.title,
        "description": created_feedback.description,
    }


@router.get("/projects/{project_id}/feedback")
@handle_api_errors
async def get_project_feedback(
    project_id: UUID,
    feedback_service: FeedbackService = Depends(get_feedback_service),
) -> Dict[str, Any]:
    """Get feedback for a project.

    Args:
        project_id: Project ID
        feedback_service: Feedback service

    Returns:
        List of feedback items
    """
    feedbacks = await feedback_service.get_project_feedback(project_id)

    return {
        "count": len(feedbacks),
        "feedback": [
            {
                "feedback_id": str(f.feedback_id),
                "title": f.title,
                "description": f.description,
                "type": f.feedback_type.value,
                "status": f.status.value,
                "priority": f.priority,
                "quality_rating": f.quality_rating,
                "satisfaction_rating": f.satisfaction_rating,
                "created_at": f.created_at.isoformat(),
            }
            for f in feedbacks
        ],
    }


# ==================== TASK FEEDBACK ENDPOINTS ====================

@router.post("/tasks/{task_id}/feedback", response_model=FeedbackResponse)
@handle_api_errors
async def create_task_feedback(
    task_id: UUID,
    feedback: TaskFeedbackCreate,
    feedback_service: FeedbackService = Depends(get_feedback_service),
    project_id: Optional[UUID] = Query(None),
    user_id: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Create feedback for a task.

    Args:
        task_id: Task ID
        feedback: Feedback data
        feedback_service: Feedback service
        project_id: Parent project ID (optional, will be fetched from task if not provided)
        user_id: User creating feedback

    Returns:
        Created feedback response
    """
    # Validate feedback type
    try:
        feedback_type = FeedbackType(feedback.feedback_type)
    except ValueError:
        valid_types = [ft.value for ft in FeedbackType]
        raise ValidationError(
            message=f"Invalid feedback type '{feedback.feedback_type}'.",
            field="feedback_type",
            details={"valid_types": valid_types}
        )

    # Validate title and description
    if not feedback.title or not feedback.title.strip():
        raise ValidationError(
            message="Title is required.",
            field="title"
        )

    if not feedback.description or not feedback.description.strip():
        raise ValidationError(
            message="Description is required.",
            field="description"
        )

    created_feedback = await feedback_service.create_task_feedback(
        task_id=task_id,
        project_id=project_id,
        feedback_type=feedback_type,
        title=feedback.title,
        description=feedback.description,
        output_quality=feedback.output_quality,
        correctness=feedback.correctness,
        completeness=feedback.completeness,
        implementation_quality=feedback.implementation_quality,
        code_review_feedback=feedback.code_review_feedback,
        suggested_improvements=feedback.suggested_improvements,
        action_items=feedback.action_items,
        priority=feedback.priority,
        context=feedback.context,
        created_by_user=user_id,
    )

    return {
        "feedback_id": str(created_feedback.feedback_id),
        "status": created_feedback.status.value,
        "priority": created_feedback.priority,
        "created_at": created_feedback.created_at.isoformat(),
        "title": created_feedback.title,
        "description": created_feedback.description,
    }


@router.get("/tasks/{task_id}/feedback")
@handle_api_errors
async def get_task_feedback(
    task_id: UUID,
    feedback_service: FeedbackService = Depends(get_feedback_service),
) -> Dict[str, Any]:
    """Get feedback for a task.

    Args:
        task_id: Task ID
        feedback_service: Feedback service

    Returns:
        List of feedback items
    """
    feedbacks = await feedback_service.get_task_feedback(task_id)

    return {
        "count": len(feedbacks),
        "feedback": [
            {
                "feedback_id": str(f.feedback_id),
                "title": f.title,
                "description": f.description,
                "type": f.feedback_type.value,
                "status": f.status.value,
                "priority": f.priority,
                "output_quality": f.output_quality,
                "correctness": f.correctness,
                "completeness": f.completeness,
                "implementation_quality": f.implementation_quality,
                "created_at": f.created_at.isoformat(),
            }
            for f in feedbacks
        ],
    }


# ==================== AGENT FEEDBACK ENDPOINTS ====================

@router.post("/agents/{agent_id}/feedback", response_model=FeedbackResponse)
@handle_api_errors
async def create_agent_feedback(
    agent_id: str,
    feedback: AgentFeedbackCreate,
    feedback_service: FeedbackService = Depends(get_feedback_service),
    user_id: Optional[str] = Query(None),
) -> Dict[str, Any]:
    """Create feedback for an agent.

    Args:
        agent_id: Agent ID
        feedback: Feedback data
        feedback_service: Feedback service
        user_id: User creating feedback

    Returns:
        Created feedback response
    """
    # Validate feedback type
    try:
        feedback_type = FeedbackType(feedback.feedback_type)
    except ValueError:
        valid_types = [ft.value for ft in FeedbackType]
        raise ValidationError(
            message=f"Invalid feedback type '{feedback.feedback_type}'.",
            field="feedback_type",
            details={"valid_types": valid_types}
        )

    # Validate title and description
    if not feedback.title or not feedback.title.strip():
        raise ValidationError(
            message="Title is required.",
            field="title"
        )

    if not feedback.description or not feedback.description.strip():
        raise ValidationError(
            message="Description is required.",
            field="description"
        )

    # Validate UUIDs if provided
    related_task_id = None
    if feedback.related_task_id:
        try:
            related_task_id = UUID(feedback.related_task_id)
        except ValueError:
            raise ValidationError(
                message="Invalid task ID format.",
                field="related_task_id"
            )

    related_project_id = None
    if feedback.related_project_id:
        try:
            related_project_id = UUID(feedback.related_project_id)
        except ValueError:
            raise ValidationError(
                message="Invalid project ID format.",
                field="related_project_id"
            )

    created_feedback = await feedback_service.create_agent_feedback(
        agent_id=agent_id,
        feedback_type=feedback_type,
        title=feedback.title,
        description=feedback.description,
        decision_quality=feedback.decision_quality,
        execution_quality=feedback.execution_quality,
        communication_clarity=feedback.communication_clarity,
        problem_solving=feedback.problem_solving,
        efficiency=feedback.efficiency,
        behavior_observations=feedback.behavior_observations,
        recommended_improvements=feedback.recommended_improvements,
        strengths_noted=feedback.strengths_noted,
        suggested_system_prompt_updates=feedback.suggested_system_prompt_updates,
        priority=feedback.priority,
        related_task_id=related_task_id,
        related_project_id=related_project_id,
        context=feedback.context,
        created_by_user=user_id,
    )

    return {
        "feedback_id": str(created_feedback.feedback_id),
        "status": created_feedback.status.value,
        "priority": created_feedback.priority,
        "created_at": created_feedback.created_at.isoformat(),
        "title": created_feedback.title,
        "description": created_feedback.description,
    }


@router.get("/agents/{agent_id}/feedback")
@handle_api_errors
async def get_agent_feedback(
    agent_id: str,
    feedback_service: FeedbackService = Depends(get_feedback_service),
) -> Dict[str, Any]:
    """Get feedback for an agent.

    Args:
        agent_id: Agent ID
        feedback_service: Feedback service

    Returns:
        List of feedback items
    """
    feedbacks = await feedback_service.get_agent_feedback(agent_id)

    return {
        "count": len(feedbacks),
        "feedback": [
            {
                "feedback_id": str(f.feedback_id),
                "title": f.title,
                "description": f.description,
                "type": f.feedback_type.value,
                "status": f.status.value,
                "priority": f.priority,
                "decision_quality": f.decision_quality,
                "execution_quality": f.execution_quality,
                "communication_clarity": f.communication_clarity,
                "created_at": f.created_at.isoformat(),
            }
            for f in feedbacks
        ],
    }


# ==================== CONTEXT UPDATES ENDPOINTS ====================

@router.get("/context-updates/{entity_type}/{entity_id}")
@handle_api_errors
async def get_context_updates(
    entity_type: str,
    entity_id: str,
    feedback_service: FeedbackService = Depends(get_feedback_service),
) -> Dict[str, Any]:
    """Get context updates for an entity.

    Args:
        entity_type: Type of entity (project, task, agent)
        entity_id: Entity ID
        feedback_service: Feedback service

    Returns:
        List of context updates
    """
    # Validate entity type (accept both singular and plural forms)
    valid_types = {"project": "project", "projects": "project",
                   "task": "task", "tasks": "task",
                   "agent": "agent", "agents": "agent"}

    if entity_type not in valid_types:
        raise ValidationError(
            message=f"Invalid entity type '{entity_type}'.",
            field="entity_type",
            details={"valid_types": list(set(valid_types.values()))}
        )

    # Normalize to singular form
    normalized_type = valid_types[entity_type]
    contexts = await feedback_service.get_context_updates(normalized_type, entity_id)

    return {
        "count": len(contexts),
        "contexts": [
            {
                "context_id": str(c.context_id),
                "title": c.title,
                "content": c.content,
                "tags": c.context_tags,
                "source": c.source,
                "implementation_status": c.implementation_status,
                "created_at": c.created_at.isoformat(),
            }
            for c in contexts
        ],
    }


# ==================== FEEDBACK STATUS UPDATE ====================

@router.patch("/feedback/{feedback_id}/status")
@handle_api_errors
async def update_feedback_status(
    feedback_id: UUID,
    status_update: FeedbackStatusUpdate,
    feedback_service: FeedbackService = Depends(get_feedback_service),
) -> Dict[str, Any]:
    """Update feedback status.

    Args:
        feedback_id: Feedback ID
        status_update: Status update data
        feedback_service: Feedback service

    Returns:
        Update result
    """
    # Validate status
    try:
        feedback_status = FeedbackStatus(status_update.status)
    except ValueError:
        valid_statuses = [fs.value for fs in FeedbackStatus]
        raise ValidationError(
            message=f"Invalid feedback status '{status_update.status}'.",
            field="status",
            details={"valid_statuses": valid_statuses}
        )

    success = await feedback_service.update_feedback_status(
        feedback_id=feedback_id,
        status=feedback_status,
        implementation_notes=status_update.implementation_notes,
    )

    if not success:
        raise NotFoundError(
            message=f"Feedback '{feedback_id}' not found.",
            resource_type="Feedback",
            resource_id=str(feedback_id)
        )

    return {
        "success": True,
        "feedback_id": str(feedback_id),
        "new_status": status_update.status,
    }
