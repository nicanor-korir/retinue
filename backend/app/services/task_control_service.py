"""
Task Control Service - Phase 2

Manages user controls for task execution:
- Pause/Resume tasks
- Cancel tasks with cleanup
- Add user context/hints
- Track control state changes
"""

import logging
from uuid import UUID
from datetime import datetime
from typing import Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update

from app.db.models import Task, TaskStatus
from app.services.websocket_manager import broadcast_activity
from app.services.event_bus import EventBus, Event, EventType

logger = logging.getLogger(__name__)


class TaskControlService:
    """Service for controlling task execution."""

    def __init__(self):
        """Initialize the task control service."""
        self.event_bus = EventBus()

    async def pause_task(
        self,
        session: AsyncSession,
        task_id: UUID,
        reason: Optional[str] = None,
    ) -> bool:
        """
        Pause a running task.

        When a task is paused:
        - Agent stops processing
        - Agent state is preserved
        - Task can be resumed later
        - Pause reason is logged

        Args:
            session: Database session
            task_id: Task to pause
            reason: Reason for pausing

        Returns:
            True if pause successful, False otherwise
        """
        try:
            # Fetch task
            result = await session.execute(select(Task).where(Task.task_id == task_id))
            task = result.scalar_one_or_none()

            if not task:
                logger.warning(f"Task not found: {task_id}")
                return False

            if task.status not in [TaskStatus.IN_PROGRESS]:
                logger.warning(f"Cannot pause task with status {task.status}")
                return False

            if task.is_paused:
                logger.warning(f"Task already paused: {task_id}")
                return False

            # Update task
            await session.execute(
                update(Task)
                .where(Task.task_id == task_id)
                .values(
                    is_paused=True,
                    pause_reason=reason,
                    paused_at=datetime.utcnow(),
                )
            )
            await session.commit()

            # Broadcast event
            await broadcast_activity(
                project_id=task.project_id,
                agent_id=task.assigned_to_agent_id,
                event_type="task_paused",
                data={
                    "task_id": str(task_id),
                    "reason": reason or "User paused",
                    "paused_at": datetime.utcnow().isoformat(),
                },
            )

            # Publish event for other services
            event = Event(
                event_type=EventType.TASK_BLOCKED,  # Use BLOCKED as closest match
                data={
                    "task_id": str(task_id),
                    "reason": reason or "User paused",
                    "paused": True,
                },
                project_id=str(task.project_id),
                source=task.assigned_to_agent_id,
            )
            await self.event_bus.publish(event)

            logger.info(f"Task paused: {task_id} - {reason}")
            return True

        except Exception as e:
            logger.error(f"Error pausing task {task_id}: {e}")
            await session.rollback()
            return False

    async def resume_task(
        self,
        session: AsyncSession,
        task_id: UUID,
    ) -> bool:
        """
        Resume a paused task.

        When a task is resumed:
        - Agent state is restored
        - Processing continues from where it paused
        - Pause info is preserved for history

        Args:
            session: Database session
            task_id: Task to resume

        Returns:
            True if resume successful, False otherwise
        """
        try:
            # Fetch task
            result = await session.execute(select(Task).where(Task.task_id == task_id))
            task = result.scalar_one_or_none()

            if not task:
                logger.warning(f"Task not found: {task_id}")
                return False

            if not task.is_paused:
                logger.warning(f"Task is not paused: {task_id}")
                return False

            # Update task
            await session.execute(
                update(Task)
                .where(Task.task_id == task_id)
                .values(is_paused=False)
            )
            await session.commit()

            # Broadcast event
            await broadcast_activity(
                project_id=task.project_id,
                agent_id=task.assigned_to_agent_id,
                event_type="task_resumed",
                data={
                    "task_id": str(task_id),
                    "resumed_at": datetime.utcnow().isoformat(),
                },
            )

            # Publish event
            event = Event(
                event_type=EventType.TASK_STARTED,
                data={
                    "task_id": str(task_id),
                    "resumed": True,
                },
                project_id=str(task.project_id),
                source=task.assigned_to_agent_id,
            )
            await self.event_bus.publish(event)

            logger.info(f"Task resumed: {task_id}")
            return True

        except Exception as e:
            logger.error(f"Error resuming task {task_id}: {e}")
            await session.rollback()
            return False

    async def cancel_task(
        self,
        session: AsyncSession,
        task_id: UUID,
        reason: str = "User cancelled",
    ) -> bool:
        """
        Cancel a task.

        When a task is cancelled:
        - Agent stops immediately
        - Task status set to CANCELLED
        - Reason is logged
        - Cleanup occurs (release resources, etc.)
        - Cannot be resumed

        Args:
            session: Database session
            task_id: Task to cancel
            reason: Reason for cancellation

        Returns:
            True if cancellation successful, False otherwise
        """
        try:
            # Fetch task
            result = await session.execute(select(Task).where(Task.task_id == task_id))
            task = result.scalar_one_or_none()

            if not task:
                logger.warning(f"Task not found: {task_id}")
                return False

            if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                logger.warning(f"Cannot cancel task with status {task.status}")
                return False

            # Update task
            await session.execute(
                update(Task)
                .where(Task.task_id == task_id)
                .values(
                    status=TaskStatus.CANCELLED,
                    blocking_reason=reason,
                    updated_at=datetime.utcnow(),
                )
            )
            await session.commit()

            # Broadcast event
            await broadcast_activity(
                project_id=task.project_id,
                agent_id=task.assigned_to_agent_id,
                event_type="task_cancelled",
                data={
                    "task_id": str(task_id),
                    "reason": reason,
                    "cancelled_at": datetime.utcnow().isoformat(),
                },
            )

            # Publish event
            event = Event(
                event_type=EventType.TASK_CANCELLED,
                data={
                    "task_id": str(task_id),
                    "reason": reason,
                },
                project_id=str(task.project_id),
                source=task.assigned_to_agent_id,
            )
            await self.event_bus.publish(event)

            logger.info(f"Task cancelled: {task_id} - {reason}")
            return True

        except Exception as e:
            logger.error(f"Error cancelling task {task_id}: {e}")
            await session.rollback()
            return False

    async def add_task_context(
        self,
        session: AsyncSession,
        task_id: UUID,
        context: str,
    ) -> bool:
        """
        Add user-provided context/hints to a task.

        User context helps agent by providing:
        - Guidance on approach
        - Constraints or requirements
        - Hints about problems to avoid
        - Domain-specific knowledge

        Args:
            session: Database session
            task_id: Task to add context to
            context: User-provided context

        Returns:
            True if successful, False otherwise
        """
        try:
            # Fetch task
            result = await session.execute(select(Task).where(Task.task_id == task_id))
            task = result.scalar_one_or_none()

            if not task:
                logger.warning(f"Task not found: {task_id}")
                return False

            # Update task
            await session.execute(
                update(Task)
                .where(Task.task_id == task_id)
                .values(
                    user_context=context,
                    updated_at=datetime.utcnow(),
                )
            )
            await session.commit()

            # Broadcast event
            await broadcast_activity(
                project_id=task.project_id,
                agent_id=task.assigned_to_agent_id,
                event_type="task_context_added",
                data={
                    "task_id": str(task_id),
                    "context_length": len(context),
                    "added_at": datetime.utcnow().isoformat(),
                },
            )

            logger.info(f"Context added to task {task_id} ({len(context)} chars)")
            return True

        except Exception as e:
            logger.error(f"Error adding context to task {task_id}: {e}")
            await session.rollback()
            return False

    async def get_control_status(
        self,
        session: AsyncSession,
        task_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Get the current control status of a task.

        Returns:
            {
                "task_id": "...",
                "is_paused": bool,
                "pause_reason": str | null,
                "paused_at": datetime | null,
                "user_context": str | null,
                "can_pause": bool,
                "can_resume": bool,
                "can_cancel": bool,
            }
        """
        try:
            result = await session.execute(select(Task).where(Task.task_id == task_id))
            task = result.scalar_one_or_none()

            if not task:
                return None

            return {
                "task_id": str(task_id),
                "is_paused": task.is_paused,
                "pause_reason": task.pause_reason,
                "paused_at": task.paused_at.isoformat() if task.paused_at else None,
                "user_context": task.user_context,
                "can_pause": task.status == TaskStatus.IN_PROGRESS and not task.is_paused,
                "can_resume": task.is_paused,
                "can_cancel": task.status in [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED],
            }

        except Exception as e:
            logger.error(f"Error getting control status for task {task_id}: {e}")
            return None


# Singleton instance
_task_control_service: Optional["TaskControlService"] = None


def get_task_control_service() -> TaskControlService:
    """Get or create the TaskControlService singleton."""
    global _task_control_service
    if _task_control_service is None:
        _task_control_service = TaskControlService()
    return _task_control_service
