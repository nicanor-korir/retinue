"""
Context Briefing Service

Generates comprehensive briefings for agents joining conversations:
- Conversation summaries
- Key entity extraction
- Project/task context
- Participant information
- Relevant message highlights
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID
from datetime import datetime
import os
from anthropic import AsyncAnthropic
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.db.models import Project, Task, Agent
from app.db.conversation_models import (
    Conversation,
    ConversationMessage,
    ConversationParticipant,
    ConversationType,
    ParticipantType
)
from app.core.config import settings

logger = logging.getLogger(__name__)


class ContextBriefingService:
    """Service for generating context briefings for agents joining conversations."""

    def __init__(self):
        """Initialize briefing service with LLM client."""
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if api_key:
            self.anthropic_client = AsyncAnthropic(api_key=api_key)
        else:
            logger.warning("ANTHROPIC_API_KEY not set, briefing service will be limited")
            self.anthropic_client = None

    async def generate_briefing(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        agent_id: str,
        specific_question: Optional[str] = None,
        max_messages: int = 20
    ) -> Dict[str, Any]:
        """
        Generate a comprehensive briefing for an agent joining a conversation.

        Args:
            db: Database session
            conversation_id: Conversation to brief on
            agent_id: Agent receiving the briefing
            specific_question: Optional specific question to address
            max_messages: Max messages to include in summary

        Returns:
            Briefing dictionary with all relevant context
        """
        logger.info(f"Generating briefing for agent {agent_id} on conversation {conversation_id}")

        # Get conversation
        conversation = await self._get_conversation(db, conversation_id)
        if not conversation:
            logger.error(f"Conversation {conversation_id} not found")
            return {}

        # Get messages
        messages = await self._get_recent_messages(db, conversation_id, limit=max_messages)

        # Get participants
        participants = await self._get_participants(db, conversation_id)

        # Get project context if applicable
        project_context = None
        if conversation.project_id:
            project_context = await self._get_project_context(db, conversation.project_id)

        # Generate conversation summary using LLM
        conversation_summary = await self.summarize_conversation(
            conversation=conversation,
            messages=messages,
            specific_question=specific_question
        )

        # Extract key entities
        key_entities = await self.extract_key_entities(messages)

        # Get current topic
        current_topic = await self._extract_current_topic(messages[-5:] if len(messages) >= 5 else messages)

        # Build comprehensive briefing
        briefing = {
            'conversation_id': str(conversation_id),
            'conversation_type': conversation.conversation_type.value,
            'conversation_title': conversation.title,
            'conversation_summary': conversation_summary,
            'current_topic': current_topic,
            'specific_question': specific_question,
            'key_entities': key_entities,
            'participant_roles': [
                {
                    'id': p.participant_id_ref,
                    'type': p.participant_type.value,
                    'role': p.participant_role.value,
                    'joined_at': p.joined_at.isoformat() if p.joined_at else None
                }
                for p in participants
            ],
            'project_context': project_context,
            'message_count': len(messages),
            'relevant_messages': [
                {
                    'sender': m.sender_name or m.sender_id,
                    'content': m.content[:200],  # Preview
                    'timestamp': m.created_at.isoformat() if m.created_at else None
                }
                for m in messages[-5:]  # Last 5 messages
            ],
            'briefing_generated_at': datetime.utcnow().isoformat()
        }

        logger.info(f"Generated briefing with {len(messages)} messages analyzed")
        return briefing

    async def summarize_conversation(
        self,
        conversation: Conversation,
        messages: List[ConversationMessage],
        specific_question: Optional[str] = None,
        max_length: int = 500
    ) -> str:
        """
        Generate a concise summary of conversation using LLM.

        Args:
            conversation: Conversation object
            messages: List of messages to summarize
            specific_question: Optional question to focus on
            max_length: Maximum summary length in characters

        Returns:
            Conversation summary
        """
        if not messages:
            return "No messages in conversation yet."

        if not self.anthropic_client:
            # Fallback to simple summary without LLM
            return self._simple_summary(messages)

        # Build context for LLM
        message_text = "\n\n".join([
            f"{m.sender_name or m.sender_type.value}: {m.content}"
            for m in messages
        ])

        prompt = f"""You are briefing an AI agent joining an ongoing conversation.
Provide a concise summary (max {max_length} characters) that captures:
1. The main topic/purpose of the conversation
2. Key points discussed
3. Current status or latest developments
4. Any open questions or decisions needed

Conversation Type: {conversation.conversation_type.value}
{"Title: " + conversation.title if conversation.title else ""}

Messages:
{message_text}

{f"Specific Question to Address: {specific_question}" if specific_question else ""}

Provide a clear, actionable summary for the joining agent:"""

        try:
            response = await self.anthropic_client.messages.create(
                model="claude-3-5-haiku-20241022",  # Fast model for summaries
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )

            summary = response.content[0].text
            logger.debug(f"Generated LLM summary: {len(summary)} chars")
            return summary[:max_length]

        except Exception as e:
            logger.error(f"Error generating LLM summary: {e}")
            return self._simple_summary(messages)

    async def extract_key_entities(
        self,
        messages: List[ConversationMessage]
    ) -> Dict[str, List[str]]:
        """
        Extract key entities mentioned in messages.

        Args:
            messages: Messages to analyze

        Returns:
            Dictionary of entity types to entity lists
        """
        entities = {
            'projects': set(),
            'tasks': set(),
            'agents': set(),
            'people': set(),
            'topics': set(),
            'technologies': set()
        }

        # Extract from message metadata
        for message in messages:
            if message.extracted_entities:
                for entity_type, entity_list in message.extracted_entities.items():
                    if entity_type in entities:
                        entities[entity_type].update(entity_list)

            # Extract mentioned agents
            if message.mentioned_agents:
                entities['agents'].update(message.mentioned_agents)

            # Extract mentioned users
            if message.mentioned_users:
                entities['people'].update(message.mentioned_users)

        # Convert sets to lists
        return {k: list(v) for k, v in entities.items()}

    async def get_project_context(
        self,
        db: AsyncSession,
        project_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get project context for briefing.

        Args:
            db: Database session
            project_id: Project ID

        Returns:
            Project context dictionary
        """
        return await self._get_project_context(db, project_id)

    async def get_task_context(
        self,
        db: AsyncSession,
        task_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """
        Get task context for briefing.

        Args:
            db: Database session
            task_id: Task ID

        Returns:
            Task context dictionary
        """
        result = await db.execute(
            select(Task).where(Task.task_id == task_id)
        )
        task = result.scalar_one_or_none()

        if not task:
            return None

        return {
            'task_id': str(task.task_id),
            'title': task.title,
            'description': task.description,
            'status': task.status.value,
            'priority': task.priority.value if task.priority else None,
            'assigned_to': task.assigned_to_agent_id,
            'project_id': str(task.project_id) if task.project_id else None
        }

    async def format_briefing_for_agent(
        self,
        briefing: Dict[str, Any],
        agent_id: str
    ) -> str:
        """
        Format briefing as readable text for an agent.

        Args:
            briefing: Briefing dictionary
            agent_id: Agent receiving briefing

        Returns:
            Formatted briefing text
        """
        parts = []

        # Header
        parts.append(f"=== CONVERSATION BRIEFING FOR {agent_id.upper()} ===\n")

        # Summary
        if briefing.get('conversation_summary'):
            parts.append(f"SUMMARY:\n{briefing['conversation_summary']}\n")

        # Current topic
        if briefing.get('current_topic'):
            parts.append(f"CURRENT TOPIC: {briefing['current_topic']}\n")

        # Specific question
        if briefing.get('specific_question'):
            parts.append(f"SPECIFIC QUESTION:\n{briefing['specific_question']}\n")

        # Key entities
        if briefing.get('key_entities'):
            entities_str = ", ".join([
                f"{k}: {', '.join(v)}"
                for k, v in briefing['key_entities'].items()
                if v
            ])
            if entities_str:
                parts.append(f"KEY ENTITIES: {entities_str}\n")

        # Participants
        if briefing.get('participant_roles'):
            participants_str = ", ".join([
                f"{p['id']} ({p['role']})"
                for p in briefing['participant_roles']
            ])
            parts.append(f"PARTICIPANTS: {participants_str}\n")

        # Project context
        if briefing.get('project_context'):
            pc = briefing['project_context']
            parts.append(f"PROJECT: {pc.get('name')} - {pc.get('description', 'N/A')}\n")

        # Recent messages
        if briefing.get('relevant_messages'):
            parts.append("RECENT MESSAGES:")
            for msg in briefing['relevant_messages']:
                parts.append(f"  - {msg['sender']}: {msg['content']}")
            parts.append("")

        parts.append("=== END BRIEFING ===")

        return "\n".join(parts)

    # Helper methods

    def _simple_summary(self, messages: List[ConversationMessage]) -> str:
        """Generate simple summary without LLM."""
        if not messages:
            return "No messages yet."

        first_msg = messages[0]
        last_msg = messages[-1]
        message_count = len(messages)

        return (
            f"Conversation started by {first_msg.sender_name or first_msg.sender_id}. "
            f"{message_count} messages exchanged. "
            f"Latest from {last_msg.sender_name or last_msg.sender_id}: "
            f"{last_msg.content[:100]}..."
        )

    async def _extract_current_topic(self, recent_messages: List[ConversationMessage]) -> Optional[str]:
        """Extract current topic from recent messages."""
        if not recent_messages:
            return None

        # Use intent classification from latest messages
        for msg in reversed(recent_messages):
            if msg.intent_classification:
                return msg.intent_classification

        # Fallback: use semantic summary if available
        for msg in reversed(recent_messages):
            if msg.semantic_summary:
                return msg.semantic_summary

        return None

    async def _get_conversation(
        self,
        db: AsyncSession,
        conversation_id: UUID
    ) -> Optional[Conversation]:
        """Get conversation by ID."""
        result = await db.execute(
            select(Conversation).where(Conversation.conversation_id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def _get_recent_messages(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        limit: int = 20
    ) -> List[ConversationMessage]:
        """Get recent messages."""
        result = await db.execute(
            select(ConversationMessage)
            .where(ConversationMessage.conversation_id == conversation_id)
            .order_by(ConversationMessage.created_at.desc())
            .limit(limit)
        )
        messages = list(result.scalars().all())
        messages.reverse()  # Chronological order
        return messages

    async def _get_participants(
        self,
        db: AsyncSession,
        conversation_id: UUID
    ) -> List[ConversationParticipant]:
        """Get conversation participants."""
        result = await db.execute(
            select(ConversationParticipant)
            .where(ConversationParticipant.conversation_id == conversation_id)
            .order_by(ConversationParticipant.joined_at)
        )
        return list(result.scalars().all())

    async def _get_project_context(
        self,
        db: AsyncSession,
        project_id: UUID
    ) -> Optional[Dict[str, Any]]:
        """Get project details."""
        result = await db.execute(
            select(Project).where(Project.project_id == project_id)
        )
        project = result.scalar_one_or_none()

        if not project:
            return None

        return {
            'project_id': str(project.project_id),
            'name': project.name,
            'description': project.description,
            'status': project.status.value,
            'priority': project.priority.value if project.priority else None,
            'deliverable_type': getattr(project, 'deliverable_type', None),
            'owner_agent_id': project.owner_agent_id,
            'requester_agent_id': project.requester_agent_id
        }
