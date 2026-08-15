"""Service for handling conversation messages."""
import logging
from typing import List, Optional, Dict, Any, AsyncIterator
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, and_
from sqlalchemy.orm import selectinload

from app.db.conversation_models import (
    Conversation,
    ConversationMessage,
    SenderType,
    ContentType,
    MessageTypeConversation,
)

logger = logging.getLogger(__name__)


class MessageHandler:
    """Service for message operations."""

    @staticmethod
    async def create_message(
        session: AsyncSession,
        conversation_id: UUID,
        sender_type: SenderType,
        sender_id: str,
        content: str,
        sender_name: Optional[str] = None,
        content_type: ContentType = ContentType.TEXT,
        message_type: MessageTypeConversation = MessageTypeConversation.MESSAGE,
        reply_to_message_id: Optional[UUID] = None,
        agent_thinking: Optional[str] = None,
        agent_confidence: Optional[float] = None,
        tools_used: Optional[List[str]] = None,
        suggested_project_data: Optional[Dict[str, Any]] = None,
        message_metadata: Optional[Dict[str, Any]] = None,
    ) -> ConversationMessage:
        """Create a new message in a conversation."""
        message = ConversationMessage(
            conversation_id=conversation_id,
            sender_type=sender_type,
            sender_id=sender_id,
            sender_name=sender_name,
            content=content,
            content_type=content_type,
            message_type=message_type,
            reply_to_message_id=reply_to_message_id,
            agent_thinking=agent_thinking,
            agent_confidence=agent_confidence,
            tools_used=tools_used or [],
            suggested_project_data=suggested_project_data,
            message_metadata=message_metadata or {},
        )

        session.add(message)

        # Update conversation metadata
        await session.execute(
            update(Conversation)
            .where(Conversation.conversation_id == conversation_id)
            .values(
                message_count=Conversation.message_count + 1,
                last_message_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
            )
        )

        await session.commit()
        await session.refresh(message)

        logger.info(
            f"Created message {message.message_id} in conversation {conversation_id} "
            f"from {sender_type} {sender_id}"
        )

        return message

    @staticmethod
    async def get_message(
        session: AsyncSession,
        message_id: UUID,
    ) -> Optional[ConversationMessage]:
        """Get message by ID."""
        result = await session.execute(
            select(ConversationMessage).where(
                ConversationMessage.message_id == message_id
            )
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def list_messages(
        session: AsyncSession,
        conversation_id: UUID,
        limit: int = 100,
        offset: int = 0,
        include_deleted: bool = False,
    ) -> List[ConversationMessage]:
        """List messages in a conversation."""
        query = select(ConversationMessage).where(
            ConversationMessage.conversation_id == conversation_id
        )

        if not include_deleted:
            query = query.where(ConversationMessage.is_deleted == False)

        query = query.order_by(ConversationMessage.created_at.asc())
        query = query.limit(limit).offset(offset)

        result = await session.execute(query)
        return result.scalars().all()

    @staticmethod
    async def update_message(
        session: AsyncSession,
        message_id: UUID,
        content: str,
    ) -> Optional[ConversationMessage]:
        """Update message content."""
        await session.execute(
            update(ConversationMessage)
            .where(ConversationMessage.message_id == message_id)
            .values(
                content=content,
                is_edited=True,
                edited_at=datetime.utcnow(),
            )
        )
        await session.commit()

        return await MessageHandler.get_message(session, message_id)

    @staticmethod
    async def delete_message(
        session: AsyncSession,
        message_id: UUID,
        hard_delete: bool = False,
    ) -> bool:
        """Delete a message (soft delete by default)."""
        if hard_delete:
            await session.execute(
                select(ConversationMessage).where(
                    ConversationMessage.message_id == message_id
                )
            )
            await session.commit()
        else:
            await session.execute(
                update(ConversationMessage)
                .where(ConversationMessage.message_id == message_id)
                .values(
                    is_deleted=True,
                    deleted_at=datetime.utcnow(),
                )
            )
            await session.commit()

        logger.info(f"Deleted message {message_id} (hard={hard_delete})")
        return True

    @staticmethod
    async def mark_as_read(
        session: AsyncSession,
        message_id: UUID,
        user_id: str,
    ) -> None:
        """Mark message as read by user."""
        message = await MessageHandler.get_message(session, message_id)
        if not message:
            return

        read_by = message.read_by or []
        if user_id not in read_by:
            read_by.append(user_id)

            await session.execute(
                update(ConversationMessage)
                .where(ConversationMessage.message_id == message_id)
                .values(read_by=read_by)
            )
            await session.commit()

    @staticmethod
    async def get_conversation_context(
        session: AsyncSession,
        conversation_id: UUID,
        max_messages: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get conversation context for agent processing."""
        messages = await MessageHandler.list_messages(
            session,
            conversation_id,
            limit=max_messages,
        )

        context = []
        for msg in messages:
            context.append({
                "role": "user" if msg.sender_type == SenderType.USER else "assistant",
                "content": msg.content,
                "timestamp": msg.created_at.isoformat() if msg.created_at else None,
                "sender_name": msg.sender_name,
                "agent_thinking": msg.agent_thinking if msg.sender_type == SenderType.AGENT else None,
            })

        return context
