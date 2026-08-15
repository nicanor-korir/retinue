"""
Multi-Agent Chat Models

Database models for multi-agent conversation features including:
- Agent invitations and joining
- Agent presence tracking
- Turn management for coordinated responses
- Enhanced participant tracking
"""

from sqlalchemy import Column, String, Text, Integer, Boolean, TIMESTAMP, ForeignKey, DECIMAL
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid
import enum

from app.db.database import Base


# Enums (using str enum for Python type hints, storing as VARCHAR in database)
class InvitationStatus(str, enum.Enum):
    """Status of agent invitation."""
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class InvitationType(str, enum.Enum):
    """Type of agent invitation."""
    MANUAL = "manual"  # User manually invites
    SUGGESTED = "suggested"  # System suggests, user approves
    AUTO = "auto"  # System auto-invites based on high confidence


class InvitedByType(str, enum.Enum):
    """Who invited the agent."""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


class AgentPresenceStatus(str, enum.Enum):
    """Real-time agent presence status."""
    ACTIVE = "active"  # Actively participating
    IDLE = "idle"  # Joined but inactive
    THINKING = "thinking"  # Processing/analyzing
    TYPING = "typing"  # Composing response
    AWAY = "away"  # Temporarily unavailable


class TurnStatus(str, enum.Enum):
    """Status of conversation turn."""
    ACTIVE = "active"  # Turn in progress
    COMPLETED = "completed"  # All agents responded
    EXPIRED = "expired"  # Timeout reached
    CANCELLED = "cancelled"  # Turn cancelled


class TurnType(str, enum.Enum):
    """Type of turn coordination."""
    SINGLE = "single"  # Single agent responds
    PARALLEL = "parallel"  # Multiple agents respond simultaneously
    SEQUENTIAL = "sequential"  # Agents respond in order


class CoordinationStrategy(str, enum.Enum):
    """How to coordinate agent responses."""
    PARALLEL = "parallel"  # All respond at once
    SEQUENTIAL = "sequential"  # One after another
    PRIORITY = "priority"  # Highest priority responds first


class Urgency(str, enum.Enum):
    """Urgency level for invitations."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# Models
class AgentInvitation(Base):
    """
    Agent invitation to join a conversation.

    Tracks when and why agents are invited, who invited them,
    and their response status.
    """
    __tablename__ = "agent_invitations"

    invitation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Invitation Details
    agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False, index=True)
    invited_by_type = Column(String(20), nullable=False)  # user, agent, system
    invited_by_id = Column(String(100), nullable=False)
    invited_by_name = Column(String(255), nullable=True)
    invitation_reason = Column(Text, nullable=True)

    # Context for Agent
    context_summary = Column(JSONB, default={})
    specific_question = Column(Text, nullable=True)
    related_message_ids = Column(JSONB, default=[])
    conversation_context = Column(JSONB, default={})  # Briefing details

    # Status
    status = Column(String(20), default="pending", index=True)  # pending, accepted, declined, expired, cancelled
    responded_at = Column(TIMESTAMP, nullable=True)
    response_message = Column(Text, nullable=True)

    # Metadata
    prediction_score = Column(DECIMAL(3, 2), nullable=True)  # From knowledge base (0.00-1.00)
    invitation_type = Column(String(20), default="manual")  # manual, suggested, auto
    urgency = Column(String(20), default="normal")  # low, normal, high, urgent
    priority_score = Column(Integer, default=0)  # Higher = more important

    # Auto-join configuration
    auto_accept = Column(Boolean, default=False)  # Should agent auto-accept?
    requires_user_approval = Column(Boolean, default=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    expires_at = Column(TIMESTAMP, nullable=True)
    accepted_at = Column(TIMESTAMP, nullable=True)
    declined_at = Column(TIMESTAMP, nullable=True)

    # Outcome
    resulted_in_participation = Column(Boolean, default=False)
    participation_duration_minutes = Column(Integer, nullable=True)

    # Metadata
    meta_data = Column(JSONB, default={})


class AgentPresence(Base):
    """
    Real-time agent presence in conversations.

    Tracks what agents are doing right now in a conversation
    for showing presence indicators in the UI.
    """
    __tablename__ = "agent_presence"

    presence_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False, index=True)

    # Presence Status
    status = Column(String(20), default="active", index=True)  # active, idle, thinking, typing, away
    activity = Column(String(100), nullable=True)  # Human-readable activity
    activity_details = Column(JSONB, default={})  # Structured activity data

    # Timestamps
    joined_at = Column(TIMESTAMP, server_default=func.now())
    last_active_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    last_message_at = Column(TIMESTAMP, nullable=True)
    last_status_change_at = Column(TIMESTAMP, server_default=func.now())

    # Metrics
    response_count = Column(Integer, default=0)
    average_response_time_seconds = Column(DECIMAL(10, 2), nullable=True)
    total_active_time_minutes = Column(Integer, default=0)

    # Current State
    is_online = Column(Boolean, default=True)
    current_turn_id = Column(UUID(as_uuid=True), nullable=True)  # Turn agent is responding to

    # Metadata
    meta_data = Column(JSONB, default={})


class ConversationTurn(Base):
    """
    Manages turn-taking in multi-agent conversations.

    Coordinates which agents should respond, in what order,
    and tracks completion status.
    """
    __tablename__ = "conversation_turns"

    turn_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Turn Details
    turn_number = Column(Integer, nullable=False)  # Sequential turn number
    triggered_by_message_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversation_messages.message_id"),
        nullable=True
    )

    # Agent Assignment
    assigned_agents = Column(JSONB, default=[])  # Array of agent IDs expected to respond
    completed_agents = Column(JSONB, default=[])  # Agents that have responded
    pending_agents = Column(JSONB, default=[])  # Agents yet to respond
    skipped_agents = Column(JSONB, default=[])  # Agents that skipped their turn

    # Response Messages
    response_message_ids = Column(JSONB, default=[])  # Messages sent during this turn

    # Status
    status = Column(String(20), default="active", index=True)  # active, completed, expired, cancelled
    turn_type = Column(String(20), default="parallel")  # single, parallel, sequential

    # Timing
    started_at = Column(TIMESTAMP, server_default=func.now())
    expected_completion_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    expired_at = Column(TIMESTAMP, nullable=True)

    # Coordination
    coordination_strategy = Column(String(20), default="parallel")  # parallel, sequential, priority
    max_response_time_seconds = Column(Integer, default=120)  # 2 minutes default
    allow_parallel_responses = Column(Boolean, default=True)

    # Priority & Ordering
    agent_response_order = Column(JSONB, default=[])  # For sequential turns
    current_agent_index = Column(Integer, default=0)  # For sequential turns

    # Metadata
    turn_context = Column(JSONB, default={})  # Additional context for this turn
    meta_data = Column(JSONB, default={})


class AgentCollaborationSession(Base):
    """
    Tracks collaboration sessions between multiple agents.

    When agents work together on a complex task, this tracks
    their collaboration metrics and outcomes.
    """
    __tablename__ = "agent_collaboration_sessions"

    session_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Participants
    participating_agents = Column(JSONB, default=[])  # Agent IDs
    primary_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)
    supporting_agents = Column(JSONB, default=[])

    # Session Details
    session_purpose = Column(String(500), nullable=True)
    expertise_areas_combined = Column(JSONB, default=[])
    collaboration_type = Column(String(50), nullable=True)  # parallel, sequential, hierarchical

    # Outcomes
    task_completed = Column(Boolean, default=False)
    user_satisfaction = Column(Integer, nullable=True)  # 1-5 rating
    collaboration_quality_score = Column(DECIMAL(3, 2), nullable=True)

    # Metrics
    total_messages = Column(Integer, default=0)
    total_duration_minutes = Column(Integer, nullable=True)
    turn_count = Column(Integer, default=0)

    # Timestamps
    started_at = Column(TIMESTAMP, server_default=func.now())
    ended_at = Column(TIMESTAMP, nullable=True)

    # Analysis
    effectiveness_analysis = Column(JSONB, default={})  # Post-session analysis
    learnings_extracted = Column(JSONB, default=[])  # What worked well

    # Metadata
    meta_data = Column(JSONB, default={})


class AgentExpertiseTag(Base):
    """
    Tags defining agent expertise areas for better matching.

    Helps the system understand which agents to invite for
    specific types of questions or tasks.
    """
    __tablename__ = "agent_expertise_tags"

    tag_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False, index=True)

    # Tag Details
    expertise_area = Column(String(100), nullable=False, index=True)
    proficiency_level = Column(Integer, default=5)  # 1-10 scale
    confidence_score = Column(DECIMAL(3, 2), default=0.8)  # How confident in this expertise

    # Evidence
    demonstrated_count = Column(Integer, default=0)  # Times demonstrated this expertise
    success_rate = Column(DECIMAL(3, 2), nullable=True)  # Success rate when using this
    last_used_at = Column(TIMESTAMP, nullable=True)

    # Keywords
    related_keywords = Column(JSONB, default=[])
    domain_specific_terms = Column(JSONB, default=[])

    # Learning
    learned_from_knowledge_base = Column(Boolean, default=False)
    manually_assigned = Column(Boolean, default=False)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    # Metadata
    meta_data = Column(JSONB, default={})


class ConversationAgentSuggestion(Base):
    """
    Stores agent suggestions for conversations.

    Tracks which agents were suggested by the system and
    whether suggestions were accepted.
    """
    __tablename__ = "conversation_agent_suggestions"

    suggestion_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(
        UUID(as_uuid=True),
        ForeignKey("conversations.conversation_id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Suggestion Details
    agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False, index=True)
    relevance_score = Column(DECIMAL(3, 2), nullable=False)  # 0.00-1.00
    reasoning = Column(Text, nullable=True)

    # Prediction Factors
    expertise_match_score = Column(DECIMAL(3, 2), nullable=True)
    historical_success_score = Column(DECIMAL(3, 2), nullable=True)
    user_preference_score = Column(DECIMAL(3, 2), nullable=True)
    context_fit_score = Column(DECIMAL(3, 2), nullable=True)

    # Matching Details
    matched_keywords = Column(JSONB, default=[])
    matched_expertise_areas = Column(JSONB, default=[])
    triggering_message_id = Column(UUID(as_uuid=True), nullable=True)

    # User Interaction
    shown_to_user = Column(Boolean, default=False)
    shown_at = Column(TIMESTAMP, nullable=True)
    user_action = Column(String(50), nullable=True)  # accepted, declined, ignored
    user_action_at = Column(TIMESTAMP, nullable=True)

    # Outcome
    resulted_in_invitation = Column(Boolean, default=False)
    invitation_id = Column(UUID(as_uuid=True), ForeignKey("agent_invitations.invitation_id"), nullable=True)

    # Learning
    feedback_collected = Column(Boolean, default=False)
    suggestion_helpful = Column(Boolean, nullable=True)

    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)

    # Metadata
    meta_data = Column(JSONB, default={})
