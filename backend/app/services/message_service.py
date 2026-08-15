"""Service for managing agent-to-agent messages with enhanced status tracking."""
import logging
from datetime import datetime
from typing import Optional, List
from uuid import UUID

from sqlalchemy import select, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Message, MessageStatus, MessageType, Priority

logger = logging.getLogger(__name__)


class MessageService:
    """Service for managing message lifecycle and status transitions."""

    @staticmethod
    async def mark_as_received(
        session: AsyncSession,
        message_id: UUID,
        agent_id: str,
    ) -> Optional[Message]:
        """
        Mark a message as received by the agent.

        Args:
            session: Database session
            message_id: ID of the message
            agent_id: ID of the agent receiving the message

        Returns:
            Updated message or None if not found
        """
        result = await session.execute(
            select(Message).where(Message.message_id == message_id)
        )
        message = result.scalar_one_or_none()

        if not message:
            return None

        if message.to_agent_id != agent_id:
            logger.warning(
                f"Agent {agent_id} attempted to mark message {message_id} "
                f"as received, but it's addressed to {message.to_agent_id}"
            )
            return None

        message.status = MessageStatus.RECEIVED
        message.received_at = datetime.utcnow()
        await session.commit()
        await session.refresh(message)

        logger.info(f"Message {message_id} marked as RECEIVED by {agent_id}")
        return message

    @staticmethod
    async def mark_as_read(
        session: AsyncSession,
        message_id: UUID,
        agent_id: str,
    ) -> Optional[Message]:
        """
        Mark a message as read by the agent.

        Args:
            session: Database session
            message_id: ID of the message
            agent_id: ID of the agent reading the message

        Returns:
            Updated message or None if not found
        """
        result = await session.execute(
            select(Message).where(Message.message_id == message_id)
        )
        message = result.scalar_one_or_none()

        if not message:
            return None

        if message.to_agent_id != agent_id:
            logger.warning(
                f"Agent {agent_id} attempted to mark message {message_id} "
                f"as read, but it's addressed to {message.to_agent_id}"
            )
            return None

        message.status = MessageStatus.READ
        message.read_status = True  # Update deprecated field for compatibility
        message.read_at = datetime.utcnow()
        message.read_by_agent_id = agent_id
        await session.commit()
        await session.refresh(message)

        logger.info(f"Message {message_id} marked as READ by {agent_id}")
        return message

    @staticmethod
    async def mark_as_in_progress(
        session: AsyncSession,
        message_id: UUID,
        agent_id: str,
    ) -> Optional[Message]:
        """
        Mark a message as in-progress (agent is working on it).

        Args:
            session: Database session
            message_id: ID of the message
            agent_id: ID of the agent working on the message

        Returns:
            Updated message or None if not found
        """
        result = await session.execute(
            select(Message).where(Message.message_id == message_id)
        )
        message = result.scalar_one_or_none()

        if not message:
            return None

        if message.to_agent_id != agent_id:
            logger.warning(
                f"Agent {agent_id} attempted to mark message {message_id} "
                f"as in-progress, but it's addressed to {message.to_agent_id}"
            )
            return None

        message.status = MessageStatus.IN_PROGRESS
        await session.commit()
        await session.refresh(message)

        logger.info(f"Message {message_id} marked as IN_PROGRESS by {agent_id}")
        return message

    @staticmethod
    async def resolve_message(
        session: AsyncSession,
        message_id: UUID,
        agent_id: str,
        resolution_note: Optional[str] = None,
    ) -> Optional[Message]:
        """
        Mark a message as resolved.

        Args:
            session: Database session
            message_id: ID of the message
            agent_id: ID of the agent resolving the message
            resolution_note: Optional note about the resolution

        Returns:
            Updated message or None if not found
        """
        result = await session.execute(
            select(Message).where(Message.message_id == message_id)
        )
        message = result.scalar_one_or_none()

        if not message:
            return None

        if message.to_agent_id != agent_id:
            logger.warning(
                f"Agent {agent_id} attempted to resolve message {message_id}, "
                f"but it's addressed to {message.to_agent_id}"
            )
            return None

        message.status = MessageStatus.RESOLVED
        message.resolved_at = datetime.utcnow()
        message.resolved_by_agent_id = agent_id
        message.resolution_note = resolution_note
        await session.commit()
        await session.refresh(message)

        logger.info(f"Message {message_id} marked as RESOLVED by {agent_id}")
        return message

    @staticmethod
    async def get_agent_messages(
        session: AsyncSession,
        agent_id: str,
        status: Optional[MessageStatus] = None,
        limit: int = 50,
    ) -> List[Message]:
        """
        Get messages for an agent, optionally filtered by status.

        Args:
            session: Database session
            agent_id: ID of the agent
            status: Optional status filter
            limit: Maximum number of messages to return

        Returns:
            List of messages
        """
        query = select(Message).where(Message.to_agent_id == agent_id)

        if status:
            query = query.where(Message.status == status)

        query = query.order_by(Message.timestamp.desc()).limit(limit)

        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def get_unresolved_messages(
        session: AsyncSession,
        agent_id: str,
    ) -> List[Message]:
        """
        Get all unresolved messages for an agent.

        Args:
            session: Database session
            agent_id: ID of the agent

        Returns:
            List of unresolved messages
        """
        result = await session.execute(
            select(Message).where(
                and_(
                    Message.to_agent_id == agent_id,
                    Message.status.in_([
                        MessageStatus.SENT,
                        MessageStatus.RECEIVED,
                        MessageStatus.READ,
                        MessageStatus.IN_PROGRESS,
                    ])
                )
            ).order_by(Message.priority.desc(), Message.timestamp.desc())
        )
        return result.scalars().all()
