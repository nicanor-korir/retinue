"""
Task RAG Event Handlers - Phase 1

Listens to task events and automatically manages RAG indexing:
- When a task completes, it's indexed to the RAG knowledge base
- When a new task is created, context from past tasks is retrieved
"""

import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.event_bus import EventBus, EventType, Event
from app.services.task_rag_integration import get_task_rag_integration
from app.db.database import get_session
from app.db.models import Task, TaskStatus
from sqlalchemy import select

logger = logging.getLogger(__name__)


class TaskRAGEventHandlers:
    """Event handlers for task RAG integration."""

    def __init__(self):
        """Initialize the event handlers."""
        self.task_rag = get_task_rag_integration()
        self.event_bus = EventBus()

    async def register_handlers(self):
        """Register event handlers with the event bus."""
        # Listen for task completion events
        self.event_bus.subscribe(
            event_type=EventType.TASK_COMPLETED,
            handler=self.on_task_completed,
        )

        # Listen for task creation events
        self.event_bus.subscribe(
            event_type=EventType.TASK_CREATED,
            handler=self.on_task_created,
        )

        logger.info("Registered Task RAG event handlers")

    async def on_task_completed(self, event: Event):
        """
        Handle task completion event.

        When a task is marked as completed, index it to the RAG knowledge base
        so it can be used as context for future similar tasks.

        Args:
            event: The TASK_COMPLETED event
        """
        try:
            task_id = event.data.get("task_id")
            if not task_id:
                logger.warning("Task completion event missing task_id")
                return

            logger.info(f"Received TASK_COMPLETED event for task {task_id}")

            # Get database session
            async with get_session() as session:
                # Parse task_id if it's a string
                try:
                    task_uuid = UUID(task_id) if isinstance(task_id, str) else task_id
                except (ValueError, TypeError):
                    logger.error(f"Invalid task_id format: {task_id}")
                    return

                # Index the task
                success = await self.task_rag.index_task_on_completion(
                    session=session,
                    task_id=task_uuid,
                )

                if success:
                    logger.info(f"Successfully indexed task {task_id}")
                else:
                    logger.warning(f"Failed to index task {task_id}")

        except Exception as e:
            logger.error(f"Error handling TASK_COMPLETED event: {e}", exc_info=True)

    async def on_task_created(self, event: Event):
        """
        Handle task creation event.

        When a new task is created, optionally retrieve context from similar past tasks
        and broadcast it to the assigned agent via WebSocket.

        Args:
            event: The TASK_CREATED event
        """
        try:
            task_id = event.data.get("task_id")
            title = event.data.get("title")
            description = event.data.get("description")
            project_id = event.data.get("project_id")
            agent_id = event.data.get("assigned_to_agent_id")

            if not task_id:
                logger.warning("Task creation event missing task_id")
                return

            logger.info(f"Received TASK_CREATED event for task {task_id}")

            # Parse task_id if needed
            try:
                task_uuid = UUID(task_id) if isinstance(task_id, str) else task_id
                proj_uuid = UUID(project_id) if isinstance(project_id, str) else project_id
            except (ValueError, TypeError):
                logger.error(f"Invalid UUID format in task creation event")
                return

            # Retrieve context (optional - depends on settings)
            from app.core.config import settings

            if not getattr(settings, "RAG_AUTO_CONTEXT_RETRIEVAL", True):
                logger.debug("Auto context retrieval disabled")
                return

            # Get context
            context_data = await self.task_rag.get_context_for_task(
                task_id=task_uuid,
                title=title or "",
                description=description or "",
                project_id=proj_uuid,
                agent_id=agent_id,
                top_k=5,  # Get top 5 similar tasks
            )

            if context_data and context_data.get("contexts"):
                # Log that context was retrieved
                logger.info(
                    f"Retrieved {len(context_data['contexts'])} contexts for "
                    f"new task {task_id}"
                )

                # Optionally broadcast context to the agent via WebSocket
                # This would be done by the calling code when it has the WebSocket connection
                logger.debug(f"Context available for task {task_id}: {len(context_data['contexts'])} items")
            else:
                logger.info(f"No similar past tasks found for task {task_id}")

        except Exception as e:
            logger.error(f"Error handling TASK_CREATED event: {e}", exc_info=True)


# Singleton instance
_task_rag_event_handlers: TaskRAGEventHandlers | None = None


async def get_task_rag_event_handlers() -> TaskRAGEventHandlers:
    """Get or create the TaskRAGEventHandlers singleton."""
    global _task_rag_event_handlers
    if _task_rag_event_handlers is None:
        _task_rag_event_handlers = TaskRAGEventHandlers()
        await _task_rag_event_handlers.register_handlers()
    return _task_rag_event_handlers


async def initialize_task_rag_handlers():
    """Initialize task RAG event handlers (called at app startup)."""
    handlers = await get_task_rag_event_handlers()
    logger.info("Task RAG event handlers initialized")
    return handlers
