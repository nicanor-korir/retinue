"""Context Enrichment Worker for background context processing.

This worker:
- Subscribes to CONVERSATION_MESSAGE_CREATED events
- Performs deep context extraction (entity extraction, semantic analysis)
- Updates messages with extracted context
- Publishes CONTEXT_ENRICHED events
- Indexes messages to RAG
"""

import asyncio
import logging
from typing import Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.database import get_db
from app.db.conversation_models import ConversationMessage, ConversationContext
from app.services.context_intelligence_service import ContextIntelligenceService
from app.services.rag_service import RAGService
from app.services.event_bus import EventBus, EventType, Event

logger = logging.getLogger(__name__)


class ContextEnrichmentWorker:
    """Background worker for context enrichment."""

    def __init__(
        self,
        event_bus: EventBus,
        context_service: Optional[ContextIntelligenceService] = None,
        rag_service: Optional[RAGService] = None
    ):
        """
        Initialize context enrichment worker.

        Args:
            event_bus: Event bus instance
            context_service: Context intelligence service
            rag_service: RAG service for indexing
        """
        self.event_bus = event_bus
        self.context_service = context_service or ContextIntelligenceService()
        self.rag_service = rag_service or RAGService()
        self._running = False

    async def start(self):
        """Start the worker and subscribe to events."""
        if self._running:
            logger.warning("Context enrichment worker already running")
            return

        self._running = True
        logger.info("Starting context enrichment worker...")

        # Subscribe to message creation events
        await self.event_bus.subscribe(
            EventType.CONVERSATION_MESSAGE_CREATED,
            self.process_message_event
        )

        logger.info("Context enrichment worker started successfully")

    async def stop(self):
        """Stop the worker."""
        self._running = False
        logger.info("Context enrichment worker stopped")

    async def process_message_event(self, event: Event):
        """
        Process a message creation event.

        Args:
            event: The message creation event
        """
        try:
            message_id = event.data.get("message_id")
            conversation_id = event.data.get("conversation_id")

            if not message_id:
                logger.warning("Message event missing message_id")
                return

            logger.info(f"Processing message {message_id} for context enrichment")

            # Process message in database context
            async for db in get_db():
                try:
                    await self._process_message(message_id, conversation_id, db)
                except Exception as e:
                    logger.error(f"Error processing message {message_id}: {e}", exc_info=True)
                finally:
                    break  # Exit generator loop

        except Exception as e:
            logger.error(f"Error in process_message_event: {e}", exc_info=True)

    async def _process_message(
        self,
        message_id: str,
        conversation_id: Optional[str],
        db: AsyncSession
    ):
        """
        Process message for context enrichment.

        Steps:
        1. Load message from database
        2. Extract deep context
        3. Update message with extracted context
        4. Update conversation context
        5. Index to RAG
        6. Publish context_enriched event

        Args:
            message_id: Message ID to process
            conversation_id: Conversation ID
            db: Database session
        """
        # 1. Load message
        result = await db.execute(
            select(ConversationMessage).where(
                ConversationMessage.message_id == message_id
            )
        )
        message = result.scalar_one_or_none()

        if not message:
            logger.warning(f"Message {message_id} not found")
            return

        # Skip if already processed
        if message.extracted_entities:
            logger.info(f"Message {message_id} already has extracted entities, skipping")
            return

        # 2. Extract deep context
        logger.info(f"Extracting deep context for message {message_id}")
        context = await self.context_service.extract_deep_context(message, db)

        # 3. Update message with extracted context
        message.extracted_entities = context.get("entities", {})
        message.intent_classification = context.get("intent")

        semantic = context.get("semantic", {})
        message.semantic_summary = semantic.get("summary")

        await db.commit()
        logger.info(f"Updated message {message_id} with extracted context")

        # 4. Update conversation context
        if conversation_id:
            await self._update_conversation_context(
                conversation_id,
                context,
                db
            )

        # 5. Index to RAG
        try:
            await self._index_to_rag(message, context)
            logger.info(f"Indexed message {message_id} to RAG")
        except Exception as e:
            logger.error(f"Error indexing message {message_id} to RAG: {e}")
            # Don't fail the whole process if RAG indexing fails

        # 6. Publish context_enriched event
        await self.event_bus.publish(
            Event(
                event_type=EventType.CONTEXT_ENRICHED,
                data={
                    "message_id": str(message_id),
                    "conversation_id": str(conversation_id) if conversation_id else None,
                    "entities": context.get("entities", {}),
                    "intent": context.get("intent"),
                    "semantic_summary": semantic.get("summary")
                },
                source="context_enrichment_worker",
                project_id=None
            )
        )

        logger.info(f"Context enrichment completed for message {message_id}")

    async def _update_conversation_context(
        self,
        conversation_id: str,
        message_context: Dict,
        db: AsyncSession
    ):
        """
        Update conversation context with new message context.

        Args:
            conversation_id: Conversation ID
            message_context: Extracted context from message
            db: Database session
        """
        try:
            # Get or create conversation context
            result = await db.execute(
                select(ConversationContext).where(
                    ConversationContext.conversation_id == conversation_id
                )
            )
            conv_context = result.scalar_one_or_none()

            entities = message_context.get("entities", {})
            intent = message_context.get("intent")

            if not conv_context:
                # Create new context
                conv_context = ConversationContext(
                    conversation_id=conversation_id,
                    entities=entities,
                    dominant_intent=intent,
                    indexed_message_count=1
                )
                db.add(conv_context)
            else:
                # Update existing context
                # Merge entities
                existing_entities = conv_context.entities or {}
                for entity_type in ["projects", "tasks", "agents"]:
                    if entity_type in entities:
                        existing_set = set(existing_entities.get(entity_type, []))
                        new_set = set(entities[entity_type])
                        merged = list(existing_set.union(new_set))
                        existing_entities[entity_type] = merged

                conv_context.entities = existing_entities
                conv_context.indexed_message_count += 1

            await db.commit()
            logger.info(f"Updated conversation context for {conversation_id}")

        except Exception as e:
            logger.error(f"Error updating conversation context: {e}")
            await db.rollback()

    async def _index_to_rag(
        self,
        message: ConversationMessage,
        context: Dict
    ):
        """
        Index message to RAG vector store.

        Args:
            message: The message object
            context: Extracted context
        """
        # Index using RAG service's message indexing
        # Note: The existing index_message method in RAG service doesn't handle conversation messages yet
        # For now, use a simplified approach
        await self.rag_service.index_message(
            message_id=str(message.message_id),
            content=message.content,
            from_agent_id=message.sender_id if message.sender_type.value == "agent" else "user",
            to_agent_id=None,  # TODO: determine target agent
            message_type=message.message_type.value if message.message_type else "message",
            project_id=None,  # TODO: extract from context
            task_id=None  # TODO: extract from context
        )


# Singleton instance
_context_enrichment_worker = None


def get_context_enrichment_worker(event_bus: EventBus) -> ContextEnrichmentWorker:
    """
    Get singleton instance of context enrichment worker.

    Args:
        event_bus: Event bus instance

    Returns:
        Context enrichment worker instance
    """
    global _context_enrichment_worker
    if _context_enrichment_worker is None:
        _context_enrichment_worker = ContextEnrichmentWorker(event_bus)
    return _context_enrichment_worker


# Auto-start functionality
async def start_context_enrichment_worker(event_bus: EventBus):
    """
    Start the context enrichment worker.

    This function should be called during application startup.

    Args:
        event_bus: Event bus instance
    """
    worker = get_context_enrichment_worker(event_bus)
    await worker.start()
    logger.info("Context enrichment worker auto-started")
