"""
Multi-Entity RAG Event Handlers - Phase 2

Listens to project, decision, and escalation events and automatically manages RAG indexing:
- When a project completes, it's indexed to the RAG knowledge base
- When important decisions are made, they're indexed for decision support
- When escalations are resolved, they're indexed for resolution guidance
"""

import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.event_bus import EventBus, EventType, Event
from app.services.multi_entity_rag_service import get_multi_entity_rag_service
from app.db.database import get_session

logger = logging.getLogger(__name__)


class MultiEntityRAGEventHandlers:
    """Event handlers for multi-entity RAG integration."""

    def __init__(self):
        """Initialize the event handlers."""
        self.multi_rag = get_multi_entity_rag_service()
        self.event_bus = EventBus()

    async def register_handlers(self):
        """Register event handlers with the event bus."""
        # Listen for project completion events
        self.event_bus.subscribe(
            event_type=EventType.PROJECT_COMPLETED,
            handler=self.on_project_completed,
        )

        # Listen for project creation events
        self.event_bus.subscribe(
            event_type=EventType.PROJECT_CREATED,
            handler=self.on_project_created,
        )

        # Listen for decision events
        self.event_bus.subscribe(
            event_type=EventType.DECISION_MADE,
            handler=self.on_decision_made,
        )

        # Listen for escalation resolution events
        self.event_bus.subscribe(
            event_type=EventType.ESCALATION_RESOLVED,
            handler=self.on_escalation_resolved,
        )

        logger.info("Registered Multi-Entity RAG event handlers")

    # ========================
    # PROJECT HANDLERS
    # ========================

    async def on_project_completed(self, event: Event):
        """
        Handle project completion event.

        When a project is marked as completed, index it to the RAG knowledge base
        so it can be used as context for future similar projects.

        Args:
            event: The PROJECT_COMPLETED event
        """
        try:
            project_id = event.data.get("project_id")
            if not project_id:
                logger.warning("Project completion event missing project_id")
                return

            logger.info(f"Received PROJECT_COMPLETED event for project {project_id}")

            # Get database session
            async with get_session() as session:
                # Parse project_id if it's a string
                try:
                    project_uuid = UUID(project_id) if isinstance(project_id, str) else project_id
                except (ValueError, TypeError):
                    logger.error(f"Invalid project_id format: {project_id}")
                    return

                # Index the project
                success = await self.multi_rag.index_project_on_completion(
                    session=session,
                    project_id=project_uuid,
                )

                if success:
                    logger.info(f"Successfully indexed project {project_id}")
                else:
                    logger.warning(f"Failed to index project {project_id}")

        except Exception as e:
            logger.error(f"Error handling PROJECT_COMPLETED event: {e}", exc_info=True)

    async def on_project_created(self, event: Event):
        """
        Handle project creation event.

        When a new project is created, retrieve context from similar past projects
        and make it available to the project owner.

        Args:
            event: The PROJECT_CREATED event
        """
        try:
            project_id = event.data.get("project_id")
            name = event.data.get("name")
            description = event.data.get("description")
            owner_agent_id = event.data.get("owner_agent_id")

            if not project_id:
                logger.warning("Project creation event missing project_id")
                return

            logger.info(f"Received PROJECT_CREATED event for project {project_id}")

            # Parse project_id if needed
            try:
                project_uuid = UUID(project_id) if isinstance(project_id, str) else project_id
            except (ValueError, TypeError):
                logger.error(f"Invalid project_id format: {project_id}")
                return

            # Check if auto context retrieval is enabled
            from app.core.config import settings

            if not getattr(settings, "RAG_AUTO_CONTEXT_RETRIEVAL", True):
                logger.debug("Auto context retrieval disabled")
                return

            # Get context from similar past projects
            context_data = await self.multi_rag.get_context_for_project(
                project_id=project_uuid,
                name=name or "",
                description=description or "",
                owner_agent_id=owner_agent_id,
                top_k=5,  # Get top 5 similar projects
            )

            if context_data and context_data.get("projects"):
                logger.info(
                    f"Retrieved {len(context_data['projects'])} project contexts for "
                    f"new project {project_id}"
                )
                logger.debug(f"Context available for project {project_id}: "
                           f"{len(context_data['projects'])} items")
            else:
                logger.info(f"No similar past projects found for project {project_id}")

        except Exception as e:
            logger.error(f"Error handling PROJECT_CREATED event: {e}", exc_info=True)

    # ========================
    # DECISION HANDLERS
    # ========================

    async def on_decision_made(self, event: Event):
        """
        Handle decision creation event.

        When a decision is made, index it to the RAG knowledge base for future
        decision support and guidance.

        Args:
            event: The DECISION_MADE event
        """
        try:
            decision_id = event.data.get("decision_id")
            if not decision_id:
                logger.warning("Decision creation event missing decision_id")
                return

            logger.info(f"Received DECISION_MADE event for decision {decision_id}")

            # Parse decision_id if needed
            try:
                decision_uuid = UUID(decision_id) if isinstance(decision_id, str) else decision_id
            except (ValueError, TypeError):
                logger.error(f"Invalid decision_id format: {decision_id}")
                return

            # Get database session
            async with get_session() as session:
                # Index the decision
                success = await self.multi_rag.index_decision(
                    session=session,
                    decision_id=decision_uuid,
                )

                if success:
                    logger.info(f"Successfully indexed decision {decision_id}")
                else:
                    logger.warning(f"Failed to index decision {decision_id}")

        except Exception as e:
            logger.error(f"Error handling DECISION_MADE event: {e}", exc_info=True)

    # ========================
    # ESCALATION HANDLERS
    # ========================

    async def on_escalation_resolved(self, event: Event):
        """
        Handle escalation resolution event.

        When an escalation is resolved, index it to the RAG knowledge base
        for future issue resolution guidance.

        Args:
            event: The ESCALATION_RESOLVED event
        """
        try:
            escalation_id = event.data.get("escalation_id")
            if not escalation_id:
                logger.warning("Escalation resolution event missing escalation_id")
                return

            logger.info(f"Received ESCALATION_RESOLVED event for escalation {escalation_id}")

            # Parse escalation_id if needed
            try:
                escalation_uuid = UUID(escalation_id) if isinstance(escalation_id, str) else escalation_id
            except (ValueError, TypeError):
                logger.error(f"Invalid escalation_id format: {escalation_id}")
                return

            # Get database session
            async with get_session() as session:
                # Index the escalation
                success = await self.multi_rag.index_escalation(
                    session=session,
                    escalation_id=escalation_uuid,
                )

                if success:
                    logger.info(f"Successfully indexed escalation {escalation_id}")
                else:
                    logger.warning(f"Failed to index escalation {escalation_id}")

        except Exception as e:
            logger.error(f"Error handling ESCALATION_RESOLVED event: {e}", exc_info=True)


# Singleton instance
_multi_entity_rag_event_handlers: MultiEntityRAGEventHandlers | None = None


async def get_multi_entity_rag_event_handlers() -> MultiEntityRAGEventHandlers:
    """Get or create the MultiEntityRAGEventHandlers singleton."""
    global _multi_entity_rag_event_handlers
    if _multi_entity_rag_event_handlers is None:
        _multi_entity_rag_event_handlers = MultiEntityRAGEventHandlers()
        await _multi_entity_rag_event_handlers.register_handlers()
    return _multi_entity_rag_event_handlers


async def initialize_multi_entity_rag_handlers():
    """Initialize multi-entity RAG event handlers (called at app startup)."""
    handlers = await get_multi_entity_rag_event_handlers()
    logger.info("Multi-Entity RAG event handlers initialized")
    return handlers
