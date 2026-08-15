"""Utility functions for creating and managing notifications."""
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Notification, NotificationType, Priority


async def create_notification(
    session: AsyncSession,
    notification_type: NotificationType,
    title: str,
    message: str,
    priority: Priority = Priority.MEDIUM,
    related_entity_type: str = None,
    related_entity_id: uuid.UUID = None,
    agent_id: str = None,
    meta_data: dict = None
) -> Notification:
    """
    Create a new notification.

    Args:
        session: Database session
        notification_type: Type of notification
        title: Notification title
        message: Notification message
        priority: Priority level
        related_entity_type: Type of related entity (project, task, etc.)
        related_entity_id: ID of related entity
        agent_id: ID of agent who triggered the notification
        meta_data: Additional metadata

    Returns:
        Created notification instance
    """
    notification = Notification(
        notification_id=uuid.uuid4(),
        type=notification_type,
        title=title,
        message=message,
        priority=priority,
        related_entity_type=related_entity_type,
        related_entity_id=related_entity_id,
        agent_id=agent_id,
        meta_data=meta_data or {}
    )

    session.add(notification)
    await session.commit()
    await session.refresh(notification)

    return notification


async def create_human_intervention_notification(
    session: AsyncSession,
    interaction_id: uuid.UUID,
    agent_id: str,
    agent_name: str,
    request: str,
    priority: Priority = Priority.HIGH
) -> Notification:
    """Create notification for human intervention required."""
    return await create_notification(
        session=session,
        notification_type=NotificationType.HUMAN_INTERVENTION_REQUIRED,
        title=f"Human Intervention Required - {agent_name}",
        message=f"{agent_name} needs your input: {request[:200]}...",
        priority=priority,
        related_entity_type="human_interaction",
        related_entity_id=interaction_id,
        agent_id=agent_id,
        meta_data={"request": request}
    )


async def create_ceo_feedback_notification(
    session: AsyncSession,
    project_id: uuid.UUID,
    project_name: str,
    feedback: str,
    priority: Priority = Priority.HIGH
) -> Notification:
    """Create notification for CEO feedback on project."""
    return await create_notification(
        session=session,
        notification_type=NotificationType.CEO_FEEDBACK,
        title=f"CEO Feedback on '{project_name}'",
        message=f"The CEO has provided feedback on your project: {feedback[:200]}...",
        priority=priority,
        related_entity_type="project",
        related_entity_id=project_id,
        agent_id="ceo_001",
        meta_data={"feedback": feedback, "project_name": project_name}
    )


async def create_project_completed_notification(
    session: AsyncSession,
    project_id: uuid.UUID,
    project_name: str,
    agent_id: str = None
) -> Notification:
    """Create notification for project completion."""
    return await create_notification(
        session=session,
        notification_type=NotificationType.PROJECT_COMPLETED,
        title=f"Project Completed: {project_name}",
        message=f"Your project '{project_name}' has been successfully completed!",
        priority=Priority.MEDIUM,
        related_entity_type="project",
        related_entity_id=project_id,
        agent_id=agent_id,
        meta_data={"project_name": project_name}
    )


async def create_project_failed_notification(
    session: AsyncSession,
    project_id: uuid.UUID,
    project_name: str,
    reason: str,
    agent_id: str = None
) -> Notification:
    """Create notification for project failure."""
    return await create_notification(
        session=session,
        notification_type=NotificationType.PROJECT_FAILED,
        title=f"Project Failed: {project_name}",
        message=f"Project '{project_name}' has failed. Reason: {reason[:150]}...",
        priority=Priority.HIGH,
        related_entity_type="project",
        related_entity_id=project_id,
        agent_id=agent_id,
        meta_data={"project_name": project_name, "reason": reason}
    )


async def create_task_blocked_notification(
    session: AsyncSession,
    task_id: uuid.UUID,
    task_title: str,
    blocking_reason: str,
    agent_id: str = None
) -> Notification:
    """Create notification for blocked task."""
    return await create_notification(
        session=session,
        notification_type=NotificationType.TASK_BLOCKED,
        title=f"Task Blocked: {task_title}",
        message=f"Task '{task_title}' is blocked. Reason: {blocking_reason[:150]}...",
        priority=Priority.HIGH,
        related_entity_type="task",
        related_entity_id=task_id,
        agent_id=agent_id,
        meta_data={"task_title": task_title, "blocking_reason": blocking_reason}
    )


async def create_escalation_notification(
    session: AsyncSession,
    escalation_id: uuid.UUID,
    issue_type: str,
    description: str,
    agent_id: str,
    severity: Priority
) -> Notification:
    """Create notification for escalation."""
    return await create_notification(
        session=session,
        notification_type=NotificationType.ESCALATION,
        title=f"Escalation: {issue_type}",
        message=f"An issue has been escalated: {description[:200]}...",
        priority=severity,
        related_entity_type="escalation",
        related_entity_id=escalation_id,
        agent_id=agent_id,
        meta_data={"issue_type": issue_type, "description": description}
    )
