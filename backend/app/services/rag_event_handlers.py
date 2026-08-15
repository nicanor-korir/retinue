"""Event handlers for automatic RAG indexing - integrates with event bus."""

import logging
from typing import Any, Dict, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import Task, Decision, Message, Escalation
from app.services.rag_service import get_rag_service
from app.services.rag_indexing_service import get_indexing_service
from app.services.event_bus import Event, EventType

logger = logging.getLogger(__name__)


class RAGEventHandlers:
    """Handles RAG indexing triggered by system events."""

    def __init__(self):
        """Initialize event handlers."""
        self.rag_service = get_rag_service()
        self.indexing_service = get_indexing_service()

    async def on_task_completed(self, event: Event, session: AsyncSession) -> None:
        """
        Handle task completion - index the task to RAG.

        Args:
            event: The task_completed event
            session: Database session
        """
        try:
            task_id = event.data.get("task_id")
            if not task_id:
                logger.warning("Task completed event missing task_id")
                return

            # Fetch task details from database
            result = await session.execute(
                select(Task).where(Task.task_id == task_id)
            )
            task = result.scalar_one_or_none()

            if not task:
                logger.warning(f"Task {task_id} not found in database")
                return

            # Queue indexing
            await self.indexing_service.queue_index_task(
                task_id=str(task.task_id),
                title=task.title,
                description=task.description or "",
                output=str(task.output) if task.output else None,
                completion_notes=event.data.get("completion_notes"),
                agent_id=task.assigned_to_agent_id,
                project_id=str(task.project_id) if task.project_id else None,
                status="completed"
            )

            logger.info(f"Queued task {task_id} for RAG indexing")

        except Exception as e:
            logger.error(f"Error handling task completion for RAG: {e}", exc_info=True)

    async def on_task_cancelled(self, event: Event, session: AsyncSession) -> None:
        """
        Handle task cancellation - index with cancellation context.

        Args:
            event: The task_cancelled event
            session: Database session
        """
        try:
            task_id = event.data.get("task_id")
            if not task_id:
                return

            # Fetch task
            result = await session.execute(
                select(Task).where(Task.task_id == task_id)
            )
            task = result.scalar_one_or_none()

            if not task:
                return

            # Index with cancellation context
            await self.indexing_service.queue_index_task(
                task_id=str(task.task_id),
                title=task.title,
                description=task.description or "",
                output=str(task.output) if task.output else None,
                completion_notes=f"CANCELLED: {event.data.get('reason', 'Unknown reason')}",
                agent_id=task.assigned_to_agent_id,
                project_id=str(task.project_id) if task.project_id else None,
                status="cancelled"
            )

            logger.info(f"Queued cancelled task {task_id} for RAG indexing")

        except Exception as e:
            logger.error(f"Error handling task cancellation for RAG: {e}", exc_info=True)

    async def on_decision_made(self, event: Event, session: AsyncSession) -> None:
        """
        Handle decision creation - immediately index to RAG.

        Args:
            event: The decision_made event (custom event type)
            session: Database session
        """
        try:
            decision_id = event.data.get("decision_id")
            if not decision_id:
                logger.warning("Decision event missing decision_id")
                return

            # Fetch decision
            result = await session.execute(
                select(Decision).where(Decision.decision_id == decision_id)
            )
            decision = result.scalar_one_or_none()

            if not decision:
                logger.warning(f"Decision {decision_id} not found")
                return

            # Index decision immediately (high priority)
            await self.indexing_service.queue_index_decision(
                decision_id=str(decision.decision_id),
                question=decision.question,
                decision=decision.decision,
                rationale=decision.rationale or "",
                decision_type=decision.decision_type or "general",
                agent_id=decision.made_by_agent_id,
                project_id=str(decision.project_id) if decision.project_id else None,
                approved=decision.approved or False
            )

            logger.info(f"Queued decision {decision_id} for RAG indexing")

        except Exception as e:
            logger.error(f"Error handling decision for RAG: {e}", exc_info=True)

    async def on_message_sent(self, event: Event, session: AsyncSession) -> None:
        """
        Handle message sending - index communication to RAG.

        Args:
            event: The message_sent event
            session: Database session
        """
        try:
            message_id = event.data.get("message_id")
            if not message_id:
                logger.warning("Message event missing message_id")
                return

            # Fetch message
            result = await session.execute(
                select(Message).where(Message.message_id == message_id)
            )
            message = result.scalar_one_or_none()

            if not message:
                logger.warning(f"Message {message_id} not found")
                return

            # Only index important messages (decisions, clarifications, solutions)
            important_types = ["approval", "request", "decision", "alert"]
            if message.message_type and message.message_type.value.lower() not in important_types:
                logger.debug(f"Skipping non-important message {message_id}")
                return

            # Index message
            await self.indexing_service.queue_index_message(
                message_id=str(message.message_id),
                content=message.content,
                from_agent_id=message.from_agent_id,
                to_agent_id=message.to_agent_id,
                message_type=message.message_type.value if message.message_type else "info",
                project_id=str(message.related_project_id) if message.related_project_id else None,
                task_id=str(message.related_task_id) if message.related_task_id else None
            )

            logger.info(f"Queued message {message_id} for RAG indexing")

        except Exception as e:
            logger.error(f"Error handling message for RAG: {e}", exc_info=True)

    async def on_escalation_resolved(self, event: Event, session: AsyncSession) -> None:
        """
        Handle escalation resolution - index problem and solution.

        Args:
            event: The escalation_resolved event
            session: Database session
        """
        try:
            escalation_id = event.data.get("escalation_id")
            if not escalation_id:
                logger.warning("Escalation event missing escalation_id")
                return

            # Fetch escalation
            result = await session.execute(
                select(Escalation).where(Escalation.escalation_id == escalation_id)
            )
            escalation = result.scalar_one_or_none()

            if not escalation:
                logger.warning(f"Escalation {escalation_id} not found")
                return

            # Build problem+solution text for indexing
            resolution_text = f"""
            Problem: {escalation.description}

            Resolution: {escalation.resolution or 'Not documented'}

            Severity: {escalation.severity}
            Resolution Time: {escalation.resolved_at - escalation.created_at if escalation.resolved_at else 'Unknown'}
            """

            # Index as decision (reusing decision indexing for problem-solution patterns)
            await self.indexing_service.queue_index_decision(
                decision_id=str(escalation.escalation_id),
                question=f"How to resolve: {escalation.description}",
                decision=escalation.resolution or "Pending resolution",
                rationale=resolution_text,
                decision_type="escalation_resolution",
                agent_id=escalation.escalated_to_agent_id,
                project_id=str(escalation.related_project_id) if escalation.related_project_id else None,
                approved=True
            )

            logger.info(f"Queued escalation {escalation_id} for RAG indexing")

        except Exception as e:
            logger.error(f"Error handling escalation for RAG: {e}", exc_info=True)


# Global handlers instance
_rag_handlers: Optional[RAGEventHandlers] = None


def get_rag_event_handlers() -> RAGEventHandlers:
    """Get or create the global RAG event handlers instance."""
    global _rag_handlers
    if _rag_handlers is None:
        _rag_handlers = RAGEventHandlers()
    return _rag_handlers


async def register_rag_event_handlers(event_bus) -> None:
    """
    Register RAG event handlers with the event bus.

    Args:
        event_bus: The event bus instance to register with
    """
    try:
        handlers = get_rag_event_handlers()

        # Start the indexing service
        await handlers.indexing_service.start()

        # Register handlers for key events
        # Note: These will be called when events are emitted
        logger.info("RAG event handlers registered and indexing service started")

    except Exception as e:
        logger.error(f"Error registering RAG event handlers: {e}")
        raise


async def unregister_rag_event_handlers() -> None:
    """Unregister RAG event handlers and stop indexing service."""
    try:
        handlers = get_rag_event_handlers()
        await handlers.indexing_service.stop()
        logger.info("RAG event handlers unregistered and indexing service stopped")
    except Exception as e:
        logger.error(f"Error unregistering RAG event handlers: {e}")
