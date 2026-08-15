"""
Immediate Task Dependency Resolution Service

Automatically resolves task dependencies the moment a task is completed,
enabling instant unblocking of dependent tasks with zero wait time.
"""

import logging
from typing import List, Optional, Set
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.event_bus import get_event_bus, EventType, Event
from app.db.models import Task, TaskStatus
from app.db.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class DependencyResolver:
    """
    Monitors task completion events and immediately resolves dependencies.

    Flow:
    1. Task A completes
    2. Event fired instantly
    3. DependencyResolver receives event (<100ms)
    4. Checks all tasks depending on Task A
    5. If all dependencies met, unblocks dependent tasks immediately
    6. Notifies assigned agents instantly
    """

    def __init__(self):
        self.event_bus = get_event_bus()
        self._subscribed = False

    def start_listening(self):
        """Start listening for task completion events"""
        if self._subscribed:
            logger.warning("DependencyResolver already subscribed")
            return

        # Subscribe to task completion events
        self.event_bus.subscribe(
            event_type=EventType.TASK_COMPLETED,
            callback=self._on_task_completed,
        )

        self._subscribed = True
        logger.info("✅ DependencyResolver: Listening for task completions")

    async def _on_task_completed(self, event: Event):
        """Handle task completion event"""
        task_id = event.data.get("task_id")
        project_id = event.data.get("project_id")

        if not task_id or not project_id:
            logger.error("Task completion event missing task_id or project_id")
            return

        logger.info(
            f"🔗 DependencyResolver: Task {task_id} completed, "
            f"checking dependencies"
        )

        # Resolve dependencies immediately
        await self.resolve_dependencies(task_id, project_id)

    async def resolve_dependencies(
        self,
        completed_task_id: str,
        project_id: str,
    ):
        """
        Resolve dependencies for a completed task.

        Finds all tasks that depend on the completed task and checks if they
        can now proceed. Unblocks and notifies agents immediately.

        Args:
            completed_task_id: ID of the task that just completed
            project_id: Project ID
        """
        async with AsyncSessionLocal() as session:
            try:
                # Find all tasks in this project that have dependencies
                result = await session.execute(
                    select(Task).where(
                        Task.project_id == project_id,
                        Task.status.in_([TaskStatus.PENDING, TaskStatus.BLOCKED]),
                    )
                )
                potential_dependent_tasks = result.scalars().all()

                unblocked_count = 0

                for task in potential_dependent_tasks:
                    # Check if this task depends on the completed task
                    if not task.dependencies:
                        continue

                    if completed_task_id not in task.dependencies:
                        continue

                    # This task depends on the completed task
                    logger.debug(
                        f"Task {task.id} depends on completed task {completed_task_id}"
                    )

                    # Check if ALL dependencies are now met
                    all_dependencies_met = await self._check_all_dependencies(
                        session, task.dependencies
                    )

                    if all_dependencies_met:
                        # Unblock the task immediately
                        await self._unblock_task(session, task)
                        unblocked_count += 1

                        logger.info(
                            f"✅ DependencyResolver: Unblocked task {task.task_id} "
                            f"(all dependencies met)"
                        )
                    else:
                        logger.debug(
                            f"Task {task.task_id} still has unmet dependencies"
                        )

                if unblocked_count > 0:
                    logger.info(
                        f"🚀 DependencyResolver: Unblocked {unblocked_count} task(s) "
                        f"after completing {completed_task_id}"
                    )

            except Exception as e:
                logger.error(
                    f"Error resolving dependencies: {e}",
                    exc_info=True
                )

    async def _check_all_dependencies(
        self,
        session: AsyncSession,
        dependency_ids: List[str],
    ) -> bool:
        """
        Check if all dependency tasks are completed.

        Args:
            session: Database session
            dependency_ids: List of task IDs that are dependencies

        Returns:
            True if all dependencies are completed, False otherwise
        """
        for dep_id in dependency_ids:
            result = await session.execute(
                select(Task).where(Task.task_id == dep_id)
            )
            dep_task = result.scalar_one_or_none()

            if not dep_task:
                logger.warning(f"Dependency task {dep_id} not found")
                return False

            if dep_task.status != TaskStatus.COMPLETED:
                return False

        return True

    async def _unblock_task(
        self,
        session: AsyncSession,
        task: Task,
    ):
        """
        Unblock a task and notify the assigned agent immediately.

        Args:
            session: Database session
            task: Task to unblock
        """
        # Update task status
        old_status = task.status
        task.status = TaskStatus.PENDING
        task.updated_at = datetime.utcnow()

        await session.commit()

        # Publish unblock event
        await self.event_bus.publish(
            event_type=EventType.TASK_DEPENDENCY_RESOLVED,
            data={
                "task_id": task.id,
                "project_id": task.project_id,
                "old_status": old_status.value,
                "new_status": task.status.value,
            },
            project_id=task.project_id,
            priority=1,  # High priority
        )

        # If task is assigned, notify the agent immediately
        if task.assigned_to_agent_id:
            await self.event_bus.publish(
                event_type=EventType.TASK_ASSIGNED,
                data={
                    "task_id": task.task_id,
                    "project_id": task.project_id,
                    "title": task.title,
                    "description": task.description,
                    "assigned_to": task.assigned_to_agent_id,
                    "status": task.status.value,
                    "message": "All dependencies resolved - you can start work immediately!",
                },
                source="dependency_resolver",
                target=task.assigned_to_agent_id,
                project_id=task.project_id,
                priority=1,
            )

            logger.info(
                f"📨 DependencyResolver: Notified {task.assigned_to_agent_id} "
                f"that task {task.task_id} is ready"
            )

    async def check_task_dependencies(
        self,
        task_id: str,
    ) -> dict:
        """
        Check dependency status for a specific task.

        Args:
            task_id: Task ID to check

        Returns:
            Dictionary with dependency information
        """
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(Task).where(Task.task_id == task_id)
                )
                task = result.scalar_one_or_none()

                if not task:
                    return {"error": "Task not found"}

                if not task.dependencies:
                    return {
                        "task_id": task_id,
                        "has_dependencies": False,
                        "ready_to_start": True,
                    }

                # Check each dependency
                dependency_status = []
                all_met = True

                for dep_id in task.dependencies:
                    dep_result = await session.execute(
                        select(Task).where(Task.task_id == dep_id)
                    )
                    dep_task = dep_result.scalar_one_or_none()

                    if not dep_task:
                        dependency_status.append({
                            "dependency_id": dep_id,
                            "status": "not_found",
                            "met": False,
                        })
                        all_met = False
                    else:
                        is_met = dep_task.status == TaskStatus.COMPLETED
                        dependency_status.append({
                            "dependency_id": dep_id,
                            "title": dep_task.title,
                            "status": dep_task.status.value,
                            "met": is_met,
                        })
                        if not is_met:
                            all_met = False

                return {
                    "task_id": task_id,
                    "has_dependencies": True,
                    "total_dependencies": len(task.dependencies),
                    "dependencies_met": sum(1 for d in dependency_status if d["met"]),
                    "ready_to_start": all_met,
                    "dependency_details": dependency_status,
                }

            except Exception as e:
                logger.error(f"Error checking dependencies: {e}", exc_info=True)
                return {"error": str(e)}

    async def get_blocked_tasks(
        self,
        project_id: Optional[str] = None,
    ) -> List[dict]:
        """
        Get all blocked tasks and their dependency status.

        Args:
            project_id: Optional project ID to filter by

        Returns:
            List of blocked tasks with dependency information
        """
        async with AsyncSessionLocal() as session:
            try:
                query = select(Task).where(
                    Task.status.in_([TaskStatus.BLOCKED, TaskStatus.PENDING])
                )

                if project_id:
                    query = query.where(Task.project_id == project_id)

                result = await session.execute(query)
                tasks = result.scalars().all()

                blocked_tasks = []

                for task in tasks:
                    if not task.dependencies:
                        continue

                    dep_info = await self.check_task_dependencies(task.task_id)
                    if not dep_info.get("ready_to_start"):
                        blocked_tasks.append({
                            "task_id": task.task_id,
                            "title": task.title,
                            "assigned_to": task.assigned_to_agent_id,
                            "project_id": task.project_id,
                            "dependency_info": dep_info,
                        })

                return blocked_tasks

            except Exception as e:
                logger.error(f"Error getting blocked tasks: {e}", exc_info=True)
                return []

    async def visualize_dependency_graph(
        self,
        project_id: str,
    ) -> dict:
        """
        Create a dependency graph visualization for a project.

        Args:
            project_id: Project ID

        Returns:
            Dependency graph data structure
        """
        async with AsyncSessionLocal() as session:
            try:
                result = await session.execute(
                    select(Task).where(Task.project_id == project_id)
                )
                tasks = result.scalars().all()

                nodes = []
                edges = []

                for task in tasks:
                    nodes.append({
                        "id": task.task_id,
                        "title": task.title,
                        "status": task.status.value,
                        "assigned_to": task.assigned_to_agent_id,
                        "has_dependencies": bool(task.dependencies),
                    })

                    if task.dependencies:
                        for dep_id in task.dependencies:
                            edges.append({
                                "from": dep_id,
                                "to": task.task_id,
                                "type": "dependency",
                            })

                return {
                    "project_id": project_id,
                    "nodes": nodes,
                    "edges": edges,
                    "total_tasks": len(nodes),
                    "total_dependencies": len(edges),
                }

            except Exception as e:
                logger.error(f"Error creating dependency graph: {e}", exc_info=True)
                return {"error": str(e)}


# Global instance
_dependency_resolver: Optional[DependencyResolver] = None


def get_dependency_resolver() -> DependencyResolver:
    """Get the global dependency resolver instance"""
    global _dependency_resolver
    if _dependency_resolver is None:
        _dependency_resolver = DependencyResolver()
    return _dependency_resolver


def start_dependency_resolution():
    """Start the global dependency resolver"""
    resolver = get_dependency_resolver()
    resolver.start_listening()
    logger.info("Global dependency resolver started")
