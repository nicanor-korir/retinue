"""SQLAlchemy database models for conversations and chat feature."""
from sqlalchemy import Column, String, Text, Integer, Boolean, TIMESTAMP, ForeignKey, Enum as SQLEnum, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from app.db.database import Base


# Enums
class ConversationType(str, enum.Enum):
    """Type of conversation."""
    AGENT_CHAT = "agent_chat"
    PROJECT_DISCUSSION = "project_discussion"
    BRAINSTORM = "brainstorm"


class ConversationStatus(str, enum.Enum):
    """Status of conversation."""
    ACTIVE = "active"
    ARCHIVED = "archived"
    CONVERTED_TO_PROJECT = "converted_to_project"


class SenderType(str, enum.Enum):
    """Type of message sender."""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class ContentType(str, enum.Enum):
    """Type of message content."""
    TEXT = "text"
    CODE = "code"
    MARKDOWN = "markdown"
    STRUCTURED = "structured"


class MessageTypeConversation(str, enum.Enum):
    """Type of conversation message."""
    MESSAGE = "message"
    SYSTEM = "system"
    PROJECT_SUGGESTION = "project_suggestion"
    QUESTION = "question"


class ParticipantType(str, enum.Enum):
    """Type of conversation participant."""
    USER = "user"
    AGENT = "agent"


class ParticipantRole(str, enum.Enum):
    """Role of participant in conversation."""
    OWNER = "owner"
    PARTICIPANT = "participant"
    OBSERVER = "observer"
    AGENT = "agent"


class ProjectIntentStatus(str, enum.Enum):
    """Status of project creation intent."""
    SUGGESTED = "suggested"
    GATHERING_DETAILS = "gathering_details"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    CREATED = "created"


class UserResponse(str, enum.Enum):
    """User response to project suggestion."""
    INTERESTED = "interested"
    DECLINED = "declined"
    NEEDS_MORE_INFO = "needs_more_info"


# Models
class Conversation(Base):
    """Conversation model for chat and brainstorming sessions."""
    __tablename__ = "conversations"

    conversation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_type = Column(SQLEnum(ConversationType), nullable=False)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # Context References
    primary_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=True)
    created_by_user_id = Column(String(100), nullable=False, default="user_1")

    # Status & Metadata
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.ACTIVE)
    is_pinned = Column(Boolean, default=False)
    tags = Column(JSONB, default=[])

    # RAG Integration
    embedding_id = Column(String(255), nullable=True)
    rag_indexed_at = Column(TIMESTAMP, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    last_message_at = Column(TIMESTAMP, nullable=True)
    archived_at = Column(TIMESTAMP, nullable=True)

    # Metadata
    participant_count = Column(Integer, default=1)
    message_count = Column(Integer, default=0)
    meta_data = Column(JSONB, default={})

    # Context Intelligence (Phase 1)
    context_summary = Column(JSONB, default={})
    active_entities = Column(JSONB, default={})


class ConversationMessage(Base):
    """Message in a conversation."""
    __tablename__ = "conversation_messages"

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False
    )

    # Sender Information
    sender_type = Column(SQLEnum(SenderType), nullable=False)
    sender_id = Column(String(100), nullable=False)
    sender_name = Column(String(255), nullable=True)

    # Message Content
    content = Column(Text, nullable=False)
    content_type = Column(SQLEnum(ContentType), default=ContentType.TEXT)
    message_type = Column(SQLEnum(MessageTypeConversation), default=MessageTypeConversation.MESSAGE)

    # Message Context
    reply_to_message_id = Column(UUID(as_uuid=True), ForeignKey("conversation_messages.message_id"), nullable=True)
    mentioned_users = Column(JSONB, default=[])
    mentioned_agents = Column(JSONB, default=[])

    # Agent-Specific Fields
    agent_thinking = Column(Text, nullable=True)
    agent_confidence = Column(DECIMAL(3, 2), nullable=True)
    tools_used = Column(JSONB, default=[])

    # Structured Data
    attachments = Column(JSONB, default=[])
    message_metadata = Column(JSONB, default={})

    # Project Creation Context
    suggested_project_data = Column(JSONB, nullable=True)

    # RAG Integration
    embedding_id = Column(String(255), nullable=True)
    rag_contexts = Column(JSONB, default=[])

    # Context Intelligence (Phase 1)
    extracted_entities = Column(JSONB, default={})
    intent_classification = Column(String(50), nullable=True)
    semantic_summary = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now())
    edited_at = Column(TIMESTAMP, nullable=True)
    deleted_at = Column(TIMESTAMP, nullable=True)

    # Status
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)
    read_by = Column(JSONB, default=[])


class ConversationParticipant(Base):
    """Participant in a conversation."""
    __tablename__ = "conversation_participants"

    participant_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False
    )

    # Participant Info
    participant_type = Column(SQLEnum(ParticipantType), nullable=False)
    participant_id_ref = Column(String(100), nullable=False)
    participant_name = Column(String(255), nullable=True)
    participant_role = Column(SQLEnum(ParticipantRole), nullable=False)

    # Participation Metadata
    joined_at = Column(TIMESTAMP, server_default=func.now())
    left_at = Column(TIMESTAMP, nullable=True)
    last_read_at = Column(TIMESTAMP, nullable=True)
    unread_count = Column(Integer, default=0)

    # Preferences
    notifications_enabled = Column(Boolean, default=True)
    is_muted = Column(Boolean, default=False)

    # Status
    is_active = Column(Boolean, default=True)
    meta_data = Column(JSONB, default={})


class ConversationTopic(Base):
    """Topic within a conversation for organization."""
    __tablename__ = "conversation_topics"

    topic_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False
    )

    topic_name = Column(String(255), nullable=False)
    topic_type = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)

    # Tracking
    message_ids = Column(JSONB, default=[])
    resolved = Column(Boolean, default=False)

    created_at = Column(TIMESTAMP, server_default=func.now())
    resolved_at = Column(TIMESTAMP, nullable=True)


class ProjectCreationIntent(Base):
    """Intent to create a project from a conversation."""
    __tablename__ = "project_creation_intents"

    intent_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.conversation_id"), nullable=False)
    message_id = Column(UUID(as_uuid=True), ForeignKey("conversation_messages.message_id"), nullable=True)

    # Intent Status
    status = Column(SQLEnum(ProjectIntentStatus), default=ProjectIntentStatus.SUGGESTED)

    # Project Data
    suggested_by_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)
    project_name = Column(String(255), nullable=True)
    project_description = Column(Text, nullable=True)
    project_type = Column(String(50), nullable=True)
    deliverable_type = Column(String(50), nullable=True)
    suggested_agents = Column(JSONB, default=[])
    priority = Column(String(50), nullable=True)

    # Extracted Context
    extracted_requirements = Column(JSONB, default=[])
    extracted_constraints = Column(JSONB, default=[])
    key_points = Column(JSONB, default=[])

    # User Interaction
    user_response = Column(SQLEnum(UserResponse), nullable=True)
    user_feedback = Column(Text, nullable=True)

    # Workflow State
    current_step = Column(String(100), nullable=True)
    workflow_data = Column(JSONB, default={})

    # Outcome
    created_project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    completed_at = Column(TIMESTAMP, nullable=True)


class ConversationAnalytics(Base):
    """Analytics for conversations."""
    __tablename__ = "conversation_analytics"

    analytics_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False
    )

    # Metrics
    total_messages = Column(Integer, default=0)
    agent_messages = Column(Integer, default=0)
    user_messages = Column(Integer, default=0)

    average_response_time_seconds = Column(DECIMAL(10, 2), nullable=True)
    conversation_duration_minutes = Column(Integer, nullable=True)

    topics_discussed = Column(JSONB, default=[])
    sentiment_score = Column(DECIMAL(3, 2), nullable=True)

    # Outcomes
    led_to_project_creation = Column(Boolean, default=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=True)
    user_satisfaction_rating = Column(Integer, nullable=True)

    # Agent Performance
    agent_accuracy = Column(DECIMAL(3, 2), nullable=True)
    tools_used_count = Column(Integer, default=0)
    rag_retrievals_count = Column(Integer, default=0)

    analyzed_at = Column(TIMESTAMP, server_default=func.now())
    meta_data = Column(JSONB, default={})


class ConversationContext(Base):
    """Context intelligence for conversations (Phase 1)."""
    __tablename__ = "conversation_context"

    context_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False
    )

    # Extracted entities
    entities = Column(JSONB, default={})  # {"projects": [], "tasks": [], "agents": []}

    # Aggregated metadata
    context_summary = Column(JSONB, default={})  # Summary of conversation topics
    dominant_intent = Column(String(50), nullable=True)  # Most common intent
    active_entities = Column(JSONB, default=[])  # Currently relevant entities

    # RAG integration
    indexed_message_count = Column(Integer, default=0)
    last_indexed_at = Column(TIMESTAMP, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class UserActivityLog(Base):
    """User activity tracking for profiling and context (Phase 1)."""
    __tablename__ = "user_activity_log"

    activity_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(100), nullable=False, index=True)

    # Activity details
    activity_type = Column(String(50), nullable=False, index=True)
    context = Column(JSONB, default={})  # Activity-specific context

    # Metadata
    timestamp = Column(TIMESTAMP, server_default=func.now(), index=True)
    session_id = Column(String(100), nullable=True)
    ip_address = Column(String(50), nullable=True)


class BusinessKnowledge(Base):
    """Business domain knowledge documents (Phase 1)."""
    __tablename__ = "business_knowledge"

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Document details
    category = Column(String(100), nullable=False, index=True)
    subcategory = Column(String(100), nullable=True)
    title = Column(String(500), nullable=False)
    content = Column(Text, nullable=False)
    summary = Column(Text, nullable=True)

    # Metadata
    tags = Column(JSONB, default=[])
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True, index=True)

    # RAG integration
    embedding_id = Column(String(100), nullable=True)
    rag_indexed_at = Column(TIMESTAMP, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    created_by_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)
