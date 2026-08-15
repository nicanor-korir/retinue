"""Conversation orchestrator for routing messages and managing conversation flow."""
import logging
from typing import Dict, Any, Optional, AsyncIterator, List
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.conversation_models import (
    Conversation,
    ConversationMessage,
    SenderType,
    ContentType,
)
from app.db.models import Agent
from app.services.message_handler import MessageHandler
from app.services.conversation_service import ConversationService
from app.services.context_intelligence_service import ContextIntelligenceService
from app.services.dynamic_prompt_builder import DynamicPromptBuilder
from app.services.user_activity_tracker import UserActivityTracker
from app.services.event_bus import EventBus, EventType, Event
from anthropic import AsyncAnthropic
import os

logger = logging.getLogger(__name__)


class ConversationOrchestrator:
    """Orchestrates conversation flow between users and agents."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        """Initialize orchestrator."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")
        self.client = AsyncAnthropic(api_key=api_key)

        # Context intelligence services (Phase 1)
        self.context_service = ContextIntelligenceService()
        self.prompt_builder = DynamicPromptBuilder()
        self.activity_tracker = UserActivityTracker()
        self.event_bus = event_bus  # Optional for now to maintain backwards compatibility

    async def process_user_message(
        self,
        session: AsyncSession,
        conversation_id: UUID,
        user_id: str,
        message_content: str,
    ) -> ConversationMessage:
        """
        Process a message from the user.

        1. Create user message record
        2. Get conversation context
        3. Route to appropriate agent
        4. Generate agent response
        5. Create agent message record
        6. Return agent response
        """
        # Get conversation
        conversation = await ConversationService.get_conversation(session, conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Create user message
        user_message = await MessageHandler.create_message(
            session=session,
            conversation_id=conversation_id,
            sender_type=SenderType.USER,
            sender_id=user_id,
            content=message_content,
            sender_name="User",
        )

        logger.info(
            f"Processing user message in conversation {conversation_id} "
            f"with agent {conversation.primary_agent_id}"
        )

        # Context Intelligence Integration (Phase 1)
        try:
            # Extract quick context for immediate use
            quick_context = await self.context_service.extract_quick_context(
                user_message, session
            )
            logger.info(f"Extracted quick context: {quick_context.get('intent')} intent")

            # Log user activity
            await self.activity_tracker.log_activity(
                user_id=user_id,
                activity_type="message_sent",
                context={
                    "conversation_id": str(conversation_id),
                    "message_id": str(user_message.message_id),
                    "message_content": message_content[:100],  # Truncate for privacy
                    "entities": quick_context.get("entities", {})
                },
                db=session
            )

            # Publish event for background context enrichment
            if self.event_bus:
                await self.event_bus.publish(
                    Event(
                        event_type=EventType.CONVERSATION_MESSAGE_CREATED,
                        data={
                            "message_id": str(user_message.message_id),
                            "conversation_id": str(conversation_id),
                            "sender_id": user_id,
                            "sender_type": "user"
                        },
                        source="conversation_orchestrator"
                    )
                )

        except Exception as e:
            # Context extraction should not fail the main flow
            logger.error(f"Error in context intelligence: {e}", exc_info=True)

        return user_message

    async def generate_agent_response(
        self,
        session: AsyncSession,
        conversation_id: UUID,
        agent_id: str,
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Generate streaming agent response.

        Yields chunks of the response as they are generated.
        """
        # Get conversation and agent
        conversation = await ConversationService.get_conversation(session, conversation_id)
        if not conversation:
            raise ValueError(f"Conversation {conversation_id} not found")

        # Get agent from database
        from sqlalchemy import select
        result = await session.execute(
            select(Agent).where(Agent.agent_id == agent_id)
        )
        agent = result.scalar_one_or_none()
        if not agent:
            raise ValueError(f"Agent {agent_id} not found")

        # Get conversation context
        context = await MessageHandler.get_conversation_context(
            session,
            conversation_id,
            max_messages=20,
        )

        # Build messages for Claude
        messages = []
        for ctx in context:
            messages.append({
                "role": ctx["role"],
                "content": ctx["content"],
            })

        # Context Intelligence: Extract context from latest message (Phase 1)
        extracted_context = {}
        if context:
            try:
                # Get the latest user message for context extraction
                latest_messages = await session.execute(
                    select(ConversationMessage).where(
                        ConversationMessage.conversation_id == conversation_id
                    ).order_by(ConversationMessage.created_at.desc()).limit(1)
                )
                from sqlalchemy import select as sql_select
                latest_message = latest_messages.scalar_one_or_none()

                if latest_message:
                    extracted_context = await self.context_service.extract_quick_context(
                        latest_message, session
                    )
                    logger.info(f"Using extracted context for prompt building: {extracted_context.get('intent')}")

            except Exception as e:
                logger.error(f"Error extracting context for prompt: {e}")
                extracted_context = {}

        # Context Intelligence: Build enhanced system prompt (Phase 1)
        try:
            system_prompt = await self.prompt_builder.build_enhanced_prompt(
                agent=agent,
                conversation_id=str(conversation_id),
                extracted_context=extracted_context,
                db=session
            )
            logger.info(f"Built enhanced prompt with context intelligence (length: {len(system_prompt)})")
        except Exception as e:
            # Fallback to agent's base system prompt if prompt building fails
            logger.error(f"Error building enhanced prompt: {e}", exc_info=True)
            system_prompt = agent.system_prompt or "You are a helpful AI assistant."

        # Generate response with streaming
        full_content = ""
        thinking_content = ""

        # Use the latest Claude model
        model_name = "claude-sonnet-4-20250514"

        # Fallback: if agent has a model specified and it's valid, use it
        if agent.llm_model and "claude-sonnet-4" in agent.llm_model:
            model_name = agent.llm_model

        try:
            logger.info(f"Starting to stream response from agent {agent_id} using model {model_name}")

            async with self.client.messages.stream(
                model=model_name,
                max_tokens=4096,
                system=system_prompt,  # Using enhanced prompt
                messages=messages,
            ) as stream:
                async for text in stream.text_stream:
                    full_content += text

                    # Yield chunk immediately
                    chunk = {
                        "type": "agent_message_chunk",
                        "content": text,
                        "is_complete": False,
                    }
                    logger.debug(f"Yielding chunk: {text[:50]}...")
                    yield chunk

            logger.info(f"Streaming complete. Total content length: {len(full_content)}")

            # After streaming is complete, create the message record
            agent_message = await MessageHandler.create_message(
                session=session,
                conversation_id=conversation_id,
                sender_type=SenderType.AGENT,
                sender_id=agent_id,
                content=full_content,
                sender_name=agent.name,
            )

            # Yield completion message
            completion = {
                "type": "agent_message_complete",
                "message_id": str(agent_message.message_id),
                "content": full_content,
                "is_complete": True,
                "agent_id": agent_id,
                "agent_name": agent.name,
                "sender_name": agent.name,
            }
            yield completion

            logger.info(
                f"Generated response from agent {agent_id} "
                f"for conversation {conversation_id} - {len(full_content)} chars"
            )

        except Exception as e:
            logger.error(f"Error generating agent response: {e}", exc_info=True)
            yield {
                "type": "error",
                "error": str(e),
                "is_complete": True,
            }

    async def detect_project_intent(
        self,
        session: AsyncSession,
        conversation_id: UUID,
    ) -> Optional[Dict[str, Any]]:
        """
        Detect if the conversation should lead to project creation.

        Analyzes conversation context to determine if user intent
        suggests creating a project.
        """
        # Get conversation context
        context = await MessageHandler.get_conversation_context(
            session,
            conversation_id,
            max_messages=10,
        )

        # Check for project-related keywords
        project_keywords = [
            "build", "create", "develop", "design", "make",
            "project", "website", "app", "application", "system"
        ]

        recent_messages = [ctx["content"].lower() for ctx in context[-5:]]
        keyword_matches = sum(
            1 for msg in recent_messages
            for keyword in project_keywords
            if keyword in msg
        )

        # If multiple project keywords found, suggest project creation
        if keyword_matches >= 3:
            return {
                "should_suggest": True,
                "confidence": min(keyword_matches / 5.0, 1.0),
                "keywords_found": keyword_matches,
            }

        return None

    async def suggest_agents_for_project(
        self,
        session: AsyncSession,
        project_description: str,
    ) -> List[str]:
        """
        Suggest appropriate agents for a project based on description.
        """
        # Simple keyword-based agent selection
        # In production, this could use more sophisticated NLP

        suggested_agents = ["ceo_001"]  # CEO always included

        description_lower = project_description.lower()

        if any(word in description_lower for word in ["website", "web", "frontend", "ui", "interface"]):
            suggested_agents.extend(["frontend_001", "designer_001"])

        if any(word in description_lower for word in ["backend", "api", "server", "database"]):
            suggested_agents.append("backend_001")

        if any(word in description_lower for word in ["design", "ui", "ux", "mockup", "prototype"]):
            if "designer_001" not in suggested_agents:
                suggested_agents.append("designer_001")

        # Always add PM for coordination
        suggested_agents.append("pm_001")

        # Add CTO for technical oversight
        suggested_agents.append("cto_001")

        return suggested_agents
