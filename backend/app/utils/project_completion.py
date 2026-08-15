"""Utility functions for checking and managing project completion."""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import Dict, Any
import logging

from app.db.models import Project, Task, AgentStatus, Message, ProjectStatus, TaskStatus
from app.utils.notifications import (
    create_project_completed_notification,
    create_project_failed_notification,
)

logger = logging.getLogger(__name__)


async def check_and_complete_project(
    session: AsyncSession,
    project_id: str,
) -> Dict[str, Any]:
    """
    Check if a project should be marked as complete and update it if so.

    A project is considered complete when:
    1. ALL tasks are in a terminal state (COMPLETED, CANCELLED, FAILED)
    2. NO agents are currently working on tasks for this project
    3. NO pending approvals or escalations for this project

    Returns:
        Dict with completion status and reasoning
    """
    try:
        # Get the project
        project_result = await session.execute(
            select(Project).where(Project.project_id == project_id)
        )
        project = project_result.scalar_one_or_none()

        if not project:
            return {
                "completed": False,
                "reason": "Project not found"
            }

        # If already completed or cancelled, no need to check
        if project.status in [ProjectStatus.COMPLETED, ProjectStatus.CANCELLED]:
            return {
                "completed": True,
                "reason": f"Project already {project.status.value}"
            }

        # Get all tasks for this project
        tasks_result = await session.execute(
            select(Task).where(Task.project_id == project_id)
        )
        tasks = tasks_result.scalars().all()

        if not tasks or len(tasks) == 0:
            # No tasks yet - project still being evaluated
            return {
                "completed": False,
                "reason": "Project has no tasks yet (still being evaluated)"
            }

        # Check task statuses
        task_statuses = {}
        terminal_statuses = [TaskStatus.COMPLETED, TaskStatus.CANCELLED, TaskStatus.FAILED]
        active_statuses = [TaskStatus.IN_PROGRESS, TaskStatus.PENDING, TaskStatus.REVIEW]

        for task in tasks:
            status = task.status
            task_statuses[status.value] = task_statuses.get(status.value, 0) + 1

        # Count tasks by category
        total_tasks = len(tasks)
        completed_tasks = task_statuses.get(TaskStatus.COMPLETED.value, 0)
        cancelled_tasks = task_statuses.get(TaskStatus.CANCELLED.value, 0)
        failed_tasks = task_statuses.get(TaskStatus.FAILED.value, 0)
        in_progress_tasks = task_statuses.get(TaskStatus.IN_PROGRESS.value, 0)
        pending_tasks = task_statuses.get(TaskStatus.PENDING.value, 0)
        review_tasks = task_statuses.get(TaskStatus.REVIEW.value, 0)
        blocked_tasks = task_statuses.get(TaskStatus.BLOCKED.value, 0)

        terminal_count = completed_tasks + cancelled_tasks + failed_tasks
        active_count = in_progress_tasks + pending_tasks + review_tasks + blocked_tasks

        logger.info(
            f"Project {project_id} task breakdown: "
            f"{completed_tasks} completed, {cancelled_tasks} cancelled, "
            f"{failed_tasks} failed, {in_progress_tasks} in progress, "
            f"{pending_tasks} pending, {review_tasks} in review, "
            f"{blocked_tasks} blocked"
        )

        # Check if all tasks are in terminal state
        if terminal_count != total_tasks:
            return {
                "completed": False,
                "reason": f"{active_count} tasks still active out of {total_tasks} total",
                "stats": task_statuses
            }

        # Check if any agent is currently working on tasks from this project
        task_ids = [str(task.task_id) for task in tasks]
        agents_result = await session.execute(
            select(AgentStatus).where(
                AgentStatus.current_task_id.in_(task_ids)
            )
        )
        working_agents = agents_result.scalars().all()

        if working_agents:
            agent_names = [agent.agent_id for agent in working_agents]
            return {
                "completed": False,
                "reason": f"Agents still working: {', '.join(agent_names)}",
                "stats": task_statuses
            }

        # Check for pending messages/approvals related to this project
        pending_messages_result = await session.execute(
            select(Message).where(
                Message.related_project_id == project_id,
                Message.read_status == False,
                Message.message_type.in_(["approval", "request"])
            )
        )
        pending_messages = pending_messages_result.scalars().all()

        if pending_messages:
            return {
                "completed": False,
                "reason": f"{len(pending_messages)} pending approvals/requests",
                "stats": task_statuses
            }

        # All conditions met - mark project as complete!
        final_status = ProjectStatus.COMPLETED

        # If all tasks were cancelled or failed, mark project as failed
        if completed_tasks == 0 and (cancelled_tasks > 0 or failed_tasks > 0):
            final_status = ProjectStatus.FAILED

        # Update project status
        stmt = (
            update(Project)
            .where(Project.project_id == project_id)
            .values(
                status=final_status,
                completed_at=func.now()
            )
        )
        await session.execute(stmt)
        await session.commit()

        logger.info(
            f"✅ Project {project_id} marked as {final_status.value}: "
            f"{completed_tasks}/{total_tasks} tasks completed"
        )

        # Create notification for project completion/failure
        if final_status == ProjectStatus.COMPLETED:
            await create_project_completed_notification(
                session=session,
                project_id=project.project_id,
                project_name=project.name,
                agent_id=project.owner_agent_id
            )
        elif final_status == ProjectStatus.FAILED:
            reason = f"{failed_tasks} task(s) failed, {cancelled_tasks} cancelled"
            await create_project_failed_notification(
                session=session,
                project_id=project.project_id,
                project_name=project.name,
                reason=reason,
                agent_id=project.owner_agent_id
            )

        return {
            "completed": True,
            "reason": f"All {total_tasks} tasks in terminal state",
            "final_status": final_status.value,
            "stats": task_statuses
        }

    except Exception as e:
        logger.error(f"Error checking project completion for {project_id}: {e}", exc_info=True)
        return {
            "completed": False,
            "reason": f"Error: {str(e)}"
        }


async def get_project_completion_summary(
    session: AsyncSession,
    project_id: str,
) -> Dict[str, Any]:
    """
    Get a detailed summary of project completion status without modifying anything.
    Useful for displaying progress to users.
    """
    try:
        # Get the project
        project_result = await session.execute(
            select(Project).where(Project.project_id == project_id)
        )
        project = project_result.scalar_one_or_none()

        if not project:
            return {"error": "Project not found"}

        # Get all tasks
        tasks_result = await session.execute(
            select(Task).where(Task.project_id == project_id)
        )
        tasks = tasks_result.scalars().all()

        if not tasks:
            return {
                "project_status": project.status.value,
                "total_tasks": 0,
                "completion_percentage": 0,
                "can_complete": False,
                "reason": "No tasks created yet"
            }

        # Count by status
        total = len(tasks)
        completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
        cancelled = sum(1 for t in tasks if t.status == TaskStatus.CANCELLED)
        in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
        pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)
        review = sum(1 for t in tasks if t.status == TaskStatus.REVIEW)
        blocked = sum(1 for t in tasks if t.status == TaskStatus.BLOCKED)

        terminal = completed + failed + cancelled
        active = total - terminal

        completion_percentage = (completed / total * 100) if total > 0 else 0

        # Check if can be completed
        can_complete = (terminal == total)

        return {
            "project_status": project.status.value,
            "total_tasks": total,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "cancelled_tasks": cancelled,
            "in_progress_tasks": in_progress,
            "pending_tasks": pending,
            "review_tasks": review,
            "blocked_tasks": blocked,
            "active_tasks": active,
            "completion_percentage": round(completion_percentage, 1),
            "can_complete": can_complete,
            "reason": "All tasks complete" if can_complete else f"{active} tasks still active"
        }

    except Exception as e:
        logger.error(f"Error getting completion summary for {project_id}: {e}", exc_info=True)
        return {"error": str(e)}
