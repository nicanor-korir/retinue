"""Service for managing conversations."""
import logging
from typing import List, Optional, Dict, Any
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload

from app.db.conversation_models import (
    Conversation,
    ConversationMessage,
    ConversationParticipant,
    ConversationType,
    ConversationStatus,
    SenderType,
    ParticipantType,
    ParticipantRole,
)
from app.db.models import Agent
from app.agents import AgentRegistry

logger = logging.getLogger(__name__)


class ConversationService:
    """Service for conversation CRUD operations."""

    @staticmethod
    async def ensure_agent_exists(
        session: AsyncSession,
        agent_id: str,
    ) -> bool:
        """
        Ensure an agent exists in the database.

        If the agent is defined in AgentRegistry but not in the database,
        create a minimal database record for it.

        Args:
            session: Database session
            agent_id: The agent ID to check/create

        Returns:
            True if agent exists or was created, False if agent is not in registry
        """
        # Check if agent exists in database
        result = await session.execute(
            select(Agent).where(Agent.agent_id == agent_id)
        )
        existing_agent = result.scalar_one_or_none()

        if existing_agent:
            return True

        # Check if agent is in registry
        config = AgentRegistry.get_agent_config(agent_id)
        if not config:
            logger.warning(f"Agent {agent_id} not found in AgentRegistry")
            return False

        # Create agent from registry config
        # Get departments - handle both single and multi-department
        agent_departments = config.get("departments") or [config.get("department")]
        dept_values = []
        for d in agent_departments:
            if d is not None:
                dept_values.append(d.value if hasattr(d, "value") else str(d))

        primary_dept = dept_values[0] if dept_values else "general"

        # Get specializations
        specializations = []
        for spec in config.get("specializations", []):
            if hasattr(spec, "value"):
                specializations.append(spec.value)
            else:
                specializations.append(str(spec))

        # Get output types
        output_types = []
        for ot in config.get("output_types", []):
            if hasattr(ot, "value"):
                output_types.append(ot.value)
            else:
                output_types.append(str(ot))

        agent = Agent(
            agent_id=agent_id,
            name=config.get("name", agent_id),
            role=config.get("role", "Agent"),
            department=primary_dept,
            departments=dept_values,
            permissions={"chat": True, "view_projects": True},
            system_prompt=f"You are {config.get('name', agent_id)}, a {config.get('role', 'Agent')}. {config.get('description', '')}",
            status="active",
            meta_data={
                "specializations": specializations,
                "output_types": output_types,
                "description": config.get("description", ""),
                "required_for_types": config.get("required_for_types", []),
                "always_active": config.get("always_active", False),
                "cost_per_hour": config.get("cost_per_hour", 0),
            },
        )

        session.add(agent)
        await session.flush()

        logger.info(f"Created agent {agent_id} in database from registry")
        return True

    @staticmethod
    async def create_conversation(
        session: AsyncSession,
        conversation_type: ConversationType,
        created_by_user_id: str = "user_1",
        primary_agent_id: Optional[str] = None,
        project_id: Optional[UUID] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Conversation:
        """Create a new conversation."""
        # Ensure agent exists in database if specified
        if primary_agent_id:
            agent_exists = await ConversationService.ensure_agent_exists(
                session, primary_agent_id
            )
            if not agent_exists:
                raise ValueError(f"Agent {primary_agent_id} not found in registry")

        conversation = Conversation(
            conversation_type=conversation_type,
            created_by_user_id=created_by_user_id,
            primary_agent_id=primary_agent_id,
            project_id=project_id,
            title=title,
            description=description,
        )

        session.add(conversation)
        await session.flush()

        # Create participant record for creator
        participant = ConversationParticipant(
            conversation_id=conversation.conversation_id,
            participant_type=ParticipantType.USER,
            participant_id_ref=created_by_user_id,
            participant_role=ParticipantRole.OWNER,
        )
        session.add(participant)

        # If agent is specified, add as participant
        if primary_agent_id:
            agent_participant = ConversationParticipant(
                conversation_id=conversation.conversation_id,
                participant_type=ParticipantType.AGENT,
                participant_id_ref=primary_agent_id,
                participant_role=ParticipantRole.AGENT,
            )
            session.add(agent_participant)
            conversation.participant_count = 2

        await session.commit()
        await session.refresh(conversation)

        logger.info(
            f"Created conversation {conversation.conversation_id} "
            f"of type {conversation_type} with agent {primary_agent_id}"
        )

        return conversation

    @staticmethod
    async def get_conversation(
        session: AsyncSession,
        conversation_id: UUID,
    ) -> Optional[Conversation]:
        """Get conversation by ID."""
        result = await session.execute(
            select(Conversation).where(Conversation.conversation_id == conversation_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_conversations(
        session: AsyncSession,
        user_id: str = "user_1",
        agent_id: Optional[str] = None,
        project_id: Optional[UUID] = None,
        conversation_type: Optional[ConversationType] = None,
        status: Optional[ConversationStatus] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """List conversations with filters and last message preview."""
        query = select(Conversation)

        # Filter by user participation
        query = query.join(ConversationParticipant).where(
            ConversationParticipant.participant_id_ref == user_id
        )

        # Apply additional filters
        if agent_id:
            query = query.where(Conversation.primary_agent_id == agent_id)
        if project_id:
            query = query.where(Conversation.project_id == project_id)
        if conversation_type:
            query = query.where(Conversation.conversation_type == conversation_type)
        if status:
            query = query.where(Conversation.status == status)

        # Order by last message time (most recent first)
        query = query.order_by(Conversation.last_message_at.desc().nullslast())
        query = query.limit(limit).offset(offset)

        result = await session.execute(query)
        conversations = result.scalars().all()

        # Fetch last message for each conversation
        conversations_with_preview = []
        for conv in conversations:
            # Get last message
            last_msg_query = select(ConversationMessage).where(
                ConversationMessage.conversation_id == conv.conversation_id
            ).order_by(ConversationMessage.created_at.desc()).limit(1)

            last_msg_result = await session.execute(last_msg_query)
            last_msg = last_msg_result.scalar_one_or_none()

            # Add last_message_preview attribute to conversation
            conv.last_message_preview = last_msg.content[:100] if last_msg else None
            conversations_with_preview.append(conv)

        return conversations_with_preview

    @staticmethod
    async def update_conversation(
        session: AsyncSession,
        conversation_id: UUID,
        **kwargs
    ) -> Optional[Conversation]:
        """Update conversation fields."""
        await session.execute(
            update(Conversation)
            .where(Conversation.conversation_id == conversation_id)
            .values(**kwargs, updated_at=datetime.utcnow())
        )
        await session.commit()

        return await ConversationService.get_conversation(session, conversation_id)

    @staticmethod
    async def archive_conversation(
        session: AsyncSession,
        conversation_id: UUID,
    ) -> Optional[Conversation]:
        """Archive a conversation."""
        return await ConversationService.update_conversation(
            session,
            conversation_id,
            status=ConversationStatus.ARCHIVED,
            archived_at=datetime.utcnow(),
        )

    @staticmethod
    async def add_participant(
        session: AsyncSession,
        conversation_id: UUID,
        participant_id: str,
        participant_type: ParticipantType,
        participant_role: ParticipantRole = ParticipantRole.PARTICIPANT,
    ) -> ConversationParticipant:
        """Add a participant to conversation."""
        participant = ConversationParticipant(
            conversation_id=conversation_id,
            participant_type=participant_type,
            participant_id_ref=participant_id,
            participant_role=participant_role,
        )
        session.add(participant)

        # Update participant count
        await session.execute(
            update(Conversation)
            .where(Conversation.conversation_id == conversation_id)
            .values(
                participant_count=Conversation.participant_count + 1,
                updated_at=datetime.utcnow(),
            )
        )

        await session.commit()
        await session.refresh(participant)

        logger.info(
            f"Added {participant_type} participant {participant_id} "
            f"to conversation {conversation_id}"
        )

        return participant

    @staticmethod
    async def get_participants(
        session: AsyncSession,
        conversation_id: UUID,
        active_only: bool = True,
    ) -> List[ConversationParticipant]:
        """Get conversation participants."""
        query = select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id
        )

        if active_only:
            query = query.where(ConversationParticipant.is_active == True)

        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_last_read(
        session: AsyncSession,
        conversation_id: UUID,
        user_id: str,
    ) -> None:
        """Update last read timestamp for user."""
        await session.execute(
            update(ConversationParticipant)
            .where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.participant_id_ref == user_id,
                )
            )
            .values(
                last_read_at=datetime.utcnow(),
                unread_count=0,
            )
        )
        await session.commit()

    @staticmethod
    async def add_multiple_agents(
        session: AsyncSession,
        conversation_id: UUID,
        agent_ids: List[str],
        role: ParticipantRole = ParticipantRole.AGENT,
    ) -> List[ConversationParticipant]:
        """
        Add multiple agents as participants to a conversation.

        Args:
            session: Database session
            conversation_id: ID of the conversation
            agent_ids: List of agent IDs to add
            role: Role for the agents (default: AGENT)

        Returns:
            List of created participant records
        """
        if not agent_ids:
            return []

        # Check which agents are already participants
        existing_result = await session.execute(
            select(ConversationParticipant.participant_id_ref).where(
                and_(
                    ConversationParticipant.conversation_id == conversation_id,
                    ConversationParticipant.participant_type == ParticipantType.AGENT,
                    ConversationParticipant.participant_id_ref.in_(agent_ids),
                )
            )
        )
        existing_agent_ids = {row[0] for row in existing_result.all()}

        # Filter out agents that are already participants
        new_agent_ids = [aid for aid in agent_ids if aid not in existing_agent_ids]

        if not new_agent_ids:
            logger.info(f"All agents already participants in conversation {conversation_id}")
            return []

        # Ensure all agents exist in database before adding as participants
        for agent_id in new_agent_ids:
            await ConversationService.ensure_agent_exists(session, agent_id)

        # Create participant records for new agents
        participants = []
        for agent_id in new_agent_ids:
            participant = ConversationParticipant(
                conversation_id=conversation_id,
                participant_type=ParticipantType.AGENT,
                participant_id_ref=agent_id,
                participant_role=role,
            )
            session.add(participant)
            participants.append(participant)

        # Update participant count
        await session.execute(
            update(Conversation)
            .where(Conversation.conversation_id == conversation_id)
            .values(
                participant_count=Conversation.participant_count + len(new_agent_ids),
                updated_at=datetime.utcnow(),
            )
        )

        await session.commit()

        logger.info(
            f"Added {len(new_agent_ids)} agent participants to conversation {conversation_id}: {new_agent_ids}"
        )

        return participants
