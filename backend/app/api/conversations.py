"""API endpoints for conversation management."""
import logging
from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import and_
from pydantic import BaseModel, Field
from datetime import datetime

from app.db.database import get_session
from app.db.conversation_models import (
    Conversation,
    ConversationType,
    ConversationStatus,
    SenderType,
    ContentType,
    MessageTypeConversation,
)
from app.services.conversation_service import ConversationService
from app.services.message_handler import MessageHandler
from app.services.multi_agent_message_handler import MultiAgentMessageHandler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/conversations", tags=["Conversations"])


# Pydantic schemas
class CreateConversationRequest(BaseModel):
    """Request to create a new conversation."""
    conversation_type: ConversationType
    primary_agent_id: Optional[str] = None
    project_id: Optional[UUID] = None
    title: Optional[str] = None
    description: Optional[str] = None
    user_id: str = Field(default="user_1")


class ConversationResponse(BaseModel):
    """Conversation response model."""
    conversation_id: UUID
    conversation_type: ConversationType
    title: Optional[str]
    description: Optional[str]
    primary_agent_id: Optional[str]
    project_id: Optional[UUID]
    created_by_user_id: str
    status: ConversationStatus
    is_pinned: bool
    participant_count: int
    message_count: int
    created_at: datetime
    updated_at: datetime
    last_message_at: Optional[datetime]
    last_message_preview: Optional[str] = None

    class Config:
        from_attributes = True


class CreateMessageRequest(BaseModel):
    """Request to create a new message."""
    content: str
    sender_id: str = Field(default="user_1")
    sender_name: Optional[str] = "User"
    content_type: ContentType = ContentType.TEXT
    reply_to_message_id: Optional[UUID] = None


class MessageResponse(BaseModel):
    """Message response model."""
    message_id: UUID
    conversation_id: UUID
    sender_type: SenderType
    sender_id: str
    sender_name: Optional[str]
    content: str
    content_type: ContentType
    message_type: MessageTypeConversation
    agent_thinking: Optional[str]
    created_at: datetime
    is_edited: bool
    is_deleted: bool

    class Config:
        from_attributes = True


class UpdateConversationRequest(BaseModel):
    """Request to update conversation."""
    title: Optional[str] = None
    description: Optional[str] = None
    is_pinned: Optional[bool] = None
    status: Optional[ConversationStatus] = None


# Endpoints
@router.post("", response_model=ConversationResponse, status_code=201)
async def create_conversation(
    request: CreateConversationRequest,
    session: AsyncSession = Depends(get_session),
):
    """Create a new conversation."""
    try:
        conversation = await ConversationService.create_conversation(
            session=session,
            conversation_type=request.conversation_type,
            created_by_user_id=request.user_id,
            primary_agent_id=request.primary_agent_id,
            project_id=request.project_id,
            title=request.title,
            description=request.description,
        )
        return conversation
    except Exception as e:
        logger.error(f"Error creating conversation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("", response_model=List[ConversationResponse])
async def list_conversations(
    user_id: str = Query(default="user_1"),
    agent_id: Optional[str] = Query(default=None),
    project_id: Optional[UUID] = Query(default=None),
    conversation_type: Optional[ConversationType] = Query(default=None),
    status: Optional[ConversationStatus] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """List conversations with filters."""
    try:
        conversations = await ConversationService.list_conversations(
            session=session,
            user_id=user_id,
            agent_id=agent_id,
            project_id=project_id,
            conversation_type=conversation_type,
            status=status,
            limit=limit,
            offset=offset,
        )
        return conversations
    except Exception as e:
        logger.error(f"Error listing conversations: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get conversation by ID."""
    conversation = await ConversationService.get_conversation(session, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.patch("/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: UUID,
    request: UpdateConversationRequest,
    session: AsyncSession = Depends(get_session),
):
    """Update conversation."""
    update_data = request.dict(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    conversation = await ConversationService.update_conversation(
        session,
        conversation_id,
        **update_data
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.delete("/{conversation_id}", status_code=204)
async def archive_conversation(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Archive a conversation."""
    conversation = await ConversationService.archive_conversation(session, conversation_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return None


# Message endpoints
@router.post("/{conversation_id}/messages", status_code=201)
async def create_message(
    conversation_id: UUID,
    request: CreateMessageRequest,
    session: AsyncSession = Depends(get_session),
):
    """
    Create a new message in conversation.

    Automatically detects if the user is requesting other agents
    and invites them to join the conversation.
    """
    try:
        # Use multi-agent message handler for automatic agent detection
        multi_agent_handler = MultiAgentMessageHandler()

        result = await multi_agent_handler.create_message_with_agent_detection(
            session=session,
            conversation_id=conversation_id,
            sender_type=SenderType.USER,
            sender_id=request.sender_id,
            sender_name=request.sender_name,
            content=request.content,
            content_type=request.content_type,
            reply_to_message_id=request.reply_to_message_id,
        )

        # Return message with invitation info
        return {
            'message_id': str(result['message'].message_id),
            'conversation_id': str(result['message'].conversation_id),
            'sender_type': result['message'].sender_type.value,
            'sender_id': result['message'].sender_id,
            'sender_name': result['message'].sender_name,
            'content': result['message'].content,
            'content_type': result['message'].content_type.value,
            'message_type': result['message'].message_type.value,
            'created_at': result['message'].created_at.isoformat() if result['message'].created_at else None,
            'is_edited': result['message'].is_edited,
            'is_deleted': result['message'].is_deleted,
            # Multi-agent info
            'invited_agents': result['invited_agents'],
            'invitation_count': result['invitation_count'],
        }
    except Exception as e:
        logger.error(f"Error creating message: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/messages", response_model=List[MessageResponse])
async def list_messages(
    conversation_id: UUID,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    session: AsyncSession = Depends(get_session),
):
    """List messages in a conversation."""
    try:
        messages = await MessageHandler.list_messages(
            session=session,
            conversation_id=conversation_id,
            limit=limit,
            offset=offset,
        )
        return messages
    except Exception as e:
        logger.error(f"Error listing messages: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/messages/{message_id}", response_model=MessageResponse)
async def get_message(
    conversation_id: UUID,
    message_id: UUID,
    session: AsyncSession = Depends(get_session),
):
    """Get a specific message."""
    message = await MessageHandler.get_message(session, message_id)
    if not message or message.conversation_id != conversation_id:
        raise HTTPException(status_code=404, detail="Message not found")
    return message


@router.post("/{conversation_id}/messages/{message_id}/read", status_code=204)
async def mark_message_read(
    conversation_id: UUID,
    message_id: UUID,
    user_id: str = Query(default="user_1"),
    session: AsyncSession = Depends(get_session),
):
    """Mark message as read."""
    await MessageHandler.mark_as_read(session, message_id, user_id)
    return None


@router.post("/{conversation_id}/read-all", status_code=204)
async def mark_all_read(
    conversation_id: UUID,
    user_id: str = Query(default="user_1"),
    session: AsyncSession = Depends(get_session),
):
    """Mark all messages in conversation as read."""
    await ConversationService.update_last_read(session, conversation_id, user_id)
    return None


@router.post("/projects/{project_id}/discussion", response_model=ConversationResponse, status_code=201)
async def create_or_get_project_discussion(
    project_id: UUID,
    user_id: str = Query(default="user_1"),
    session: AsyncSession = Depends(get_session),
):
    """
    Create or get existing project discussion chat.

    This endpoint:
    - Checks if a project_discussion conversation already exists for the project
    - If exists, returns the existing conversation
    - If not, creates a new conversation with all project agents as participants
    - Adds the user and all assigned agents to the conversation

    This enables asynchronous group chat between the user and all agents working on the project.
    """
    from sqlalchemy import select
    from app.db.models import Project, Task

    try:
        # Check if project exists
        project_result = await session.execute(
            select(Project).where(Project.project_id == project_id)
        )
        project = project_result.scalar_one_or_none()

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Check if project discussion already exists (get most recent active one)
        existing_conv_result = await session.execute(
            select(Conversation).where(
                and_(
                    Conversation.project_id == project_id,
                    Conversation.conversation_type == ConversationType.PROJECT_DISCUSSION,
                    Conversation.status != ConversationStatus.ARCHIVED,
                )
            ).order_by(Conversation.created_at.desc()).limit(1)
        )
        existing_conv = existing_conv_result.scalars().first()

        if existing_conv:
            logger.info(f"Found existing project discussion {existing_conv.conversation_id} for project {project_id}")
            return existing_conv

        # Gather all agents for this project
        agent_ids = set()

        # Add owner agent
        if project.owner_agent_id:
            agent_ids.add(project.owner_agent_id)

        # Add requester agent
        if project.requester_agent_id:
            agent_ids.add(project.requester_agent_id)

        # Add selected agents
        if project.selected_agents:
            for agent_id in project.selected_agents:
                agent_ids.add(agent_id)

        # Get agents assigned to tasks in this project
        task_agents_result = await session.execute(
            select(Task.assigned_to_agent_id).where(
                Task.project_id == project_id
            ).distinct()
        )
        task_agent_ids = {row[0] for row in task_agents_result.all()}
        agent_ids.update(task_agent_ids)

        # Create conversation
        conversation_title = f"Project Discussion: {project.name}"
        conversation = await ConversationService.create_conversation(
            session=session,
            conversation_type=ConversationType.PROJECT_DISCUSSION,
            created_by_user_id=user_id,
            primary_agent_id=project.owner_agent_id,
            project_id=project_id,
            title=conversation_title,
            description=f"Group chat for {project.name} with all assigned agents",
        )

        # Add all project agents as participants
        if agent_ids:
            # Remove the primary agent since it was already added during creation
            agent_ids_to_add = list(agent_ids - {project.owner_agent_id})

            if agent_ids_to_add:
                await ConversationService.add_multiple_agents(
                    session=session,
                    conversation_id=conversation.conversation_id,
                    agent_ids=agent_ids_to_add,
                )

        logger.info(
            f"Created project discussion {conversation.conversation_id} "
            f"for project {project_id} with {len(agent_ids)} agents"
        )

        # Refresh to get updated participant count
        await session.refresh(conversation)

        return conversation

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating project discussion: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# Context Intelligence Endpoints (Phase 1)
# ============================================================================

class ConversationContextResponse(BaseModel):
    """Response model for conversation context."""
    context_id: UUID
    conversation_id: UUID
    entities: dict
    context_summary: dict
    dominant_intent: Optional[str]
    indexed_message_count: int
    last_indexed_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserActivityProfileResponse(BaseModel):
    """Response model for user activity profile."""
    user_id: str
    active_projects: List[str]
    frequent_agents: List[str]
    common_topics: List[str]
    activity_summary: dict
    preferences: dict


class MessageContextResponse(BaseModel):
    """Enhanced message response with context."""
    message_id: UUID
    conversation_id: UUID
    sender_type: SenderType
    sender_id: str
    content: str
    extracted_entities: dict
    intent_classification: Optional[str]
    semantic_summary: Optional[str]
    rag_contexts: List[dict]
    created_at: datetime

    class Config:
        from_attributes = True


@router.get("/{conversation_id}/context")
async def get_conversation_context(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Get aggregated context for a conversation.

    Returns extracted entities, dominant intent, and context summary.
    Returns empty context if none exists yet (newly created conversations).
    """
    try:
        from sqlalchemy import select
        from app.db.conversation_models import ConversationContext, Conversation

        # First verify conversation exists
        conv_result = await session.execute(
            select(Conversation).where(Conversation.conversation_id == conversation_id)
        )
        conversation = conv_result.scalar_one_or_none()

        if not conversation:
            raise HTTPException(
                status_code=404,
                detail=f"Conversation {conversation_id} not found"
            )

        # Try to get existing context
        result = await session.execute(
            select(ConversationContext).where(
                ConversationContext.conversation_id == conversation_id
            )
        )
        context = result.scalar_one_or_none()

        if context:
            return context

        # Return empty context structure for new conversations
        return {
            "conversation_id": str(conversation_id),
            "entities": {
                "projects": [],
                "tasks": [],
                "agents": [],
                "deadlines": [],
                "keywords": []
            },
            "dominant_intent": "discussion",
            "context_summary": None,
            "indexed_message_count": 0,
            "last_indexed_at": None,
            "created_at": conversation.created_at.isoformat() if conversation.created_at else None,
            "updated_at": conversation.updated_at.isoformat() if conversation.updated_at else None
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving conversation context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{conversation_id}/messages/{message_id}/context", response_model=MessageContextResponse)
async def get_message_context(
    conversation_id: UUID,
    message_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Get extracted context for a specific message.

    Returns entities, intent, semantic summary, and RAG contexts.
    """
    try:
        from sqlalchemy import select
        from app.db.conversation_models import ConversationMessage

        result = await session.execute(
            select(ConversationMessage).where(
                and_(
                    ConversationMessage.conversation_id == conversation_id,
                    ConversationMessage.message_id == message_id
                )
            )
        )
        message = result.scalar_one_or_none()

        if not message:
            raise HTTPException(
                status_code=404,
                detail=f"Message {message_id} not found"
            )

        return MessageContextResponse(
            message_id=message.message_id,
            conversation_id=message.conversation_id,
            sender_type=message.sender_type,
            sender_id=message.sender_id,
            content=message.content,
            extracted_entities=message.extracted_entities or {},
            intent_classification=message.intent_classification,
            semantic_summary=message.semantic_summary,
            rag_contexts=message.rag_contexts or [],
            created_at=message.created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving message context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/users/{user_id}/activity-profile", response_model=UserActivityProfileResponse)
async def get_user_activity_profile(
    user_id: str,
    days: int = Query(default=30, ge=1, le=365),
    session: AsyncSession = Depends(get_session)
):
    """
    Get user activity profile including preferences and patterns.

    Args:
        user_id: User identifier
        days: Number of days to look back (default: 30, max: 365)
    """
    try:
        from app.services.user_activity_tracker import get_user_activity_tracker

        tracker = get_user_activity_tracker()

        # Get user profile
        profile = await tracker.get_user_profile(user_id, session, days=days)

        # Get preferences
        preferences = await tracker.get_user_preferences(user_id, session)

        return UserActivityProfileResponse(
            user_id=user_id,
            active_projects=profile.get("active_projects", []),
            frequent_agents=profile.get("frequent_agents", []),
            common_topics=profile.get("common_topics", []),
            activity_summary=profile.get("activity_summary", {}),
            preferences=preferences
        )

    except Exception as e:
        logger.error(f"Error retrieving user activity profile: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{conversation_id}/extract-context")
async def manually_extract_context(
    conversation_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Manually trigger context extraction for all messages in a conversation.

    Useful for backfilling context on existing conversations.
    """
    try:
        from sqlalchemy import select
        from app.db.conversation_models import ConversationMessage
        from app.services.context_intelligence_service import ContextIntelligenceService

        # Get all messages in conversation
        result = await session.execute(
            select(ConversationMessage).where(
                ConversationMessage.conversation_id == conversation_id
            ).order_by(ConversationMessage.created_at)
        )
        messages = result.scalars().all()

        if not messages:
            raise HTTPException(
                status_code=404,
                detail=f"No messages found in conversation {conversation_id}"
            )

        context_service = ContextIntelligenceService()
        processed_count = 0

        for message in messages:
            # Skip if already has extracted entities
            if message.extracted_entities:
                continue

            try:
                # Extract deep context
                context = await context_service.extract_deep_context(message, session)

                # Update message
                message.extracted_entities = context.get("entities", {})
                message.intent_classification = context.get("intent")
                message.semantic_summary = context.get("semantic", {}).get("summary")

                processed_count += 1

            except Exception as e:
                logger.error(f"Error processing message {message.message_id}: {e}")
                continue

        await session.commit()

        return {
            "conversation_id": str(conversation_id),
            "total_messages": len(messages),
            "processed_count": processed_count,
            "status": "completed"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error extracting context: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))
