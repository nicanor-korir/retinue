"""
Task Control API Endpoints - Phase 2

Provides endpoints for user control over task execution:
- Pause/Resume tasks
- Cancel tasks
- Add context/hints
- Get control status
"""

import logging
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel

from app.db.database import get_session
from app.services.task_control_service import get_task_control_service

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/tasks", tags=["task-controls"])


# Pydantic models
class PauseTaskRequest(BaseModel):
    """Request to pause a task."""
    reason: str | None = None


class AddContextRequest(BaseModel):
    """Request to add context to a task."""
    context: str


class ControlStatusResponse(BaseModel):
    """Response with task control status."""
    task_id: str
    is_paused: bool
    pause_reason: str | None
    paused_at: str | None
    user_context: str | None
    can_pause: bool
    can_resume: bool
    can_cancel: bool


class ActionResponse(BaseModel):
    """Response to control action."""
    success: bool
    message: str
    task_id: str


# Endpoints

@router.post("/{task_id}/pause")
async def pause_task(
    task_id: UUID,
    request: PauseTaskRequest,
    session: AsyncSession = Depends(get_session),
) -> ActionResponse:
    """
    Pause a running task.

    The task can be resumed later. The agent's state is preserved.

    Args:
        task_id: Task ID to pause
        request: Pause request with optional reason

    Returns:
        ActionResponse with success status
    """
    try:
        service = get_task_control_service()
        success = await service.pause_task(
            session=session,
            task_id=task_id,
            reason=request.reason,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not pause task (may be in wrong status)",
            )

        return ActionResponse(
            success=True,
            message=f"Task paused: {request.reason or 'User paused'}",
            task_id=str(task_id),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/{task_id}/resume")
async def resume_task(
    task_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> ActionResponse:
    """
    Resume a paused task.

    The task continues from where it paused. Agent state is restored.

    Args:
        task_id: Task ID to resume

    Returns:
        ActionResponse with success status
    """
    try:
        service = get_task_control_service()
        success = await service.resume_task(
            session=session,
            task_id=task_id,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not resume task (must be paused)",
            )

        return ActionResponse(
            success=True,
            message="Task resumed",
            task_id=str(task_id),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/{task_id}/cancel")
async def cancel_task(
    task_id: UUID,
    reason: str | None = Query(None),
    session: AsyncSession = Depends(get_session),
) -> ActionResponse:
    """
    Cancel a task.

    The task is stopped immediately and marked as CANCELLED.
    Cannot be resumed.

    Args:
        task_id: Task ID to cancel
        reason: Optional reason for cancellation

    Returns:
        ActionResponse with success status
    """
    try:
        service = get_task_control_service()
        success = await service.cancel_task(
            session=session,
            task_id=task_id,
            reason=reason,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not cancel task (may already be completed)",
            )

        return ActionResponse(
            success=True,
            message=f"Task cancelled: {reason or 'User cancelled'}",
            task_id=str(task_id),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling task: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.post("/{task_id}/context")
async def add_task_context(
    task_id: UUID,
    request: AddContextRequest,
    session: AsyncSession = Depends(get_session),
) -> ActionResponse:
    """
    Add user-provided context/hints to a task.

    Helps guide the agent with domain knowledge, constraints, or hints.

    Args:
        task_id: Task ID
        request: Context to add

    Returns:
        ActionResponse with success status
    """
    try:
        if not request.context.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Context cannot be empty",
            )

        service = get_task_control_service()
        success = await service.add_task_context(
            session=session,
            task_id=task_id,
            context=request.context,
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        return ActionResponse(
            success=True,
            message=f"Context added ({len(request.context)} characters)",
            task_id=str(task_id),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding context: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )


@router.get("/{task_id}/control-status")
async def get_control_status(
    task_id: UUID,
    session: AsyncSession = Depends(get_session),
) -> ControlStatusResponse:
    """
    Get the control status of a task.

    Shows:
    - Whether task is paused
    - User context if added
    - What controls are available

    Args:
        task_id: Task ID

    Returns:
        ControlStatusResponse with current status
    """
    try:
        service = get_task_control_service()
        status = await service.get_control_status(
            session=session,
            task_id=task_id,
        )

        if not status:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found",
            )

        return ControlStatusResponse(**status)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting control status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error",
        )
