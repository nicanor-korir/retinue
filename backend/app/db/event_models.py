"""
Real-time event tracking models for Agent Thought Stream visualization.

These models capture detailed agent activity including thoughts, LLM interactions,
decisions, and handoffs for transparent real-time visualization.
"""
from sqlalchemy import Column, String, Text, Integer, Boolean, TIMESTAMP, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from app.db.database import Base


class ActivityType(str, enum.Enum):
    """Types of agent activities."""
    THINKING = "thinking"  # Agent is analyzing/planning
    GENERATING = "generating"  # Agent is creating content
    WAITING = "waiting"  # Agent is waiting for input/approval
    DECIDING = "deciding"  # Agent is making a decision
    MESSAGING = "messaging"  # Agent is communicating
    EXECUTING = "executing"  # Agent is executing code/actions
    REVIEWING = "reviewing"  # Agent is reviewing work
    COMPLETED = "completed"  # Agent finished task
    ERROR = "error"  # Agent encountered error


class ThoughtType(str, enum.Enum):
    """Types of agent thoughts."""
    ANALYSIS = "analysis"  # Analyzing requirements
    PLANNING = "planning"  # Planning approach
    REASONING = "reasoning"  # Internal reasoning
    EVALUATION = "evaluation"  # Evaluating options
    REFLECTION = "reflection"  # Reflecting on results


class LLMProvider(str, enum.Enum):
    """LLM providers."""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    LOCAL = "local"


class HandoffStatus(str, enum.Enum):
    """Handoff status."""
    INITIATED = "initiated"
    IN_TRANSIT = "in_transit"
    RECEIVED = "received"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class AgentActivity(Base):
    """
    Tracks all agent activities in real-time.
    This is the main table for the activity feed.
    """
    __tablename__ = "agent_activities"

    activity_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=True, index=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=True, index=True)
    
    # Activity details
    activity_type = Column(SQLEnum(ActivityType), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Progress tracking
    progress_percentage = Column(Integer, default=0)
    stage = Column(String(100), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    
    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    meta_data = Column(JSONB, default={})


class AgentThought(Base):
    """
    Captures agent's internal thoughts and reasoning process.
    Shows what the agent is thinking in real-time.
    """
    __tablename__ = "agent_thoughts"

    thought_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False, index=True)
    activity_id = Column(UUID(as_uuid=True), ForeignKey("agent_activities.activity_id"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=True, index=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=True)
    
    # Thought details
    thought_type = Column(SQLEnum(ThoughtType), nullable=False)
    content = Column(Text, nullable=False)
    
    # Context
    context = Column(JSONB, nullable=True)  # What the agent was considering
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    meta_data = Column(JSONB, default={})


class LLMInteraction(Base):
    """
    Tracks all LLM API calls made by agents.
    Shows prompts, responses, tokens, latency for full transparency.
    """
    __tablename__ = "llm_interactions"

    interaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False, index=True)
    activity_id = Column(UUID(as_uuid=True), ForeignKey("agent_activities.activity_id"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=True, index=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=True)
    
    # LLM details
    provider = Column(SQLEnum(LLMProvider), nullable=False)
    model = Column(String(100), nullable=False)
    
    # Request
    prompt = Column(Text, nullable=False)
    system_prompt = Column(Text, nullable=True)
    temperature = Column(Float, nullable=True)
    max_tokens = Column(Integer, nullable=True)
    
    # Response
    response = Column(Text, nullable=True)
    finish_reason = Column(String(50), nullable=True)
    
    # Metrics
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)
    
    # Status
    status = Column(String(50), default="pending")  # pending, completed, error
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    meta_data = Column(JSONB, default={})


class AgentHandoff(Base):
    """
    Tracks work handoffs between agents.
    Visualizes the flow of work through the organization.
    """
    __tablename__ = "agent_handoffs"

    handoff_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False, index=True)
    to_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=False, index=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=True)
    
    # Handoff details
    handoff_type = Column(String(50), nullable=False)  # task_assignment, approval_request, collaboration
    message = Column(Text, nullable=False)
    
    # Attachments
    attachments = Column(JSONB, default=[])  # Files, documents, context
    
    # Status tracking
    status = Column(SQLEnum(HandoffStatus), nullable=False, default=HandoffStatus.INITIATED)
    
    # Timestamps
    initiated_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    received_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    
    # Response
    response = Column(Text, nullable=True)
    meta_data = Column(JSONB, default={})


class ContentGeneration(Base):
    """
    Tracks content being generated by agents in real-time.
    Allows streaming visualization of agent output.
    """
    __tablename__ = "content_generations"

    generation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False, index=True)
    activity_id = Column(UUID(as_uuid=True), ForeignKey("agent_activities.activity_id"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=True, index=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=True)
    
    # Content details
    content_type = Column(String(50), nullable=False)  # code, document, design, analysis
    title = Column(String(255), nullable=False)
    
    # Content (can be streamed)
    content = Column(Text, nullable=True)
    content_chunks = Column(JSONB, default=[])  # For streaming visualization
    
    # Progress
    is_complete = Column(Boolean, default=False)
    tokens_generated = Column(Integer, default=0)
    
    # Timestamps
    started_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    meta_data = Column(JSONB, default={})


class DecisionPoint(Base):
    """
    Tracks decision points where agents need approval or make key choices.
    Extends the existing Decision model with real-time visualization data.
    """
    __tablename__ = "decision_points"

    decision_point_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False, index=True)
    activity_id = Column(UUID(as_uuid=True), ForeignKey("agent_activities.activity_id"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=True, index=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=True)
    decision_id = Column(UUID(as_uuid=True), ForeignKey("decisions.decision_id"), nullable=True)
    
    # Decision details
    title = Column(String(255), nullable=False)
    question = Column(Text, nullable=False)
    options = Column(JSONB, nullable=True)  # Available options
    
    # Reasoning
    rationale = Column(Text, nullable=True)
    pros_cons = Column(JSONB, nullable=True)
    
    # Impact assessment
    impact = Column(Text, nullable=True)
    risk_level = Column(String(20), nullable=True)  # low, medium, high
    
    # Approval
    requires_approval = Column(Boolean, default=False)
    approved_by = Column(String(100), nullable=True)
    approval_status = Column(String(50), default="pending")  # pending, approved, rejected
    
    # Choice
    chosen_option = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    decided_at = Column(TIMESTAMP, nullable=True)
    meta_data = Column(JSONB, default={})


class AgentMetric(Base):
    """
    Tracks agent performance metrics over time.
    Used for analytics and the agent dashboard.
    """
    __tablename__ = "agent_metrics"

    metric_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False, index=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=True, index=True)
    
    # Metrics
    tasks_completed = Column(Integer, default=0)
    tasks_in_progress = Column(Integer, default=0)
    average_completion_time = Column(Float, nullable=True)  # in hours
    success_rate = Column(Float, nullable=True)  # percentage
    
    # LLM usage
    llm_calls = Column(Integer, default=0)
    total_tokens = Column(Integer, default=0)
    total_cost = Column(Float, default=0.0)
    
    # Activity
    active_time_minutes = Column(Integer, default=0)
    idle_time_minutes = Column(Integer, default=0)
    
    # Time window
    metric_date = Column(TIMESTAMP, nullable=False, index=True)
    meta_data = Column(JSONB, default={})


class EventTimeline(Base):
    """
    A simplified timeline of all events for a project.
    Used for the time travel / replay feature.
    """
    __tablename__ = "event_timeline"

    event_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=False, index=True)
    agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)
    
    # Event details
    event_type = Column(String(50), nullable=False, index=True)
    event_category = Column(String(50), nullable=True)  # milestone, activity, decision, communication
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # References
    related_activity_id = Column(UUID(as_uuid=True), nullable=True)
    related_task_id = Column(UUID(as_uuid=True), nullable=True)
    
    # Highlighting
    is_highlight = Column(Boolean, default=False)  # Important milestone
    highlight_type = Column(String(50), nullable=True)  # key_decision, novel_solution, issue, milestone
    
    # Timestamp
    event_timestamp = Column(TIMESTAMP, nullable=False, index=True)
    meta_data = Column(JSONB, default={})


# Indexes for performance
from sqlalchemy import Index

# Activity indexes for fast querying
Index('idx_agent_activities_project_created', 
      AgentActivity.project_id, AgentActivity.created_at.desc())
Index('idx_agent_activities_agent_active',
      AgentActivity.agent_id, AgentActivity.is_active)

# Thought indexes
Index('idx_agent_thoughts_project_created',
      AgentThought.project_id, AgentThought.created_at.desc())

# LLM interaction indexes
Index('idx_llm_interactions_project_started',
      LLMInteraction.project_id, LLMInteraction.started_at.desc())

# Handoff indexes
Index('idx_agent_handoffs_project_initiated',
      AgentHandoff.project_id, AgentHandoff.initiated_at.desc())
Index('idx_agent_handoffs_to_agent_status',
      AgentHandoff.to_agent_id, AgentHandoff.status)

# Timeline indexes
Index('idx_event_timeline_project_timestamp',
      EventTimeline.project_id, EventTimeline.event_timestamp.desc())
Index('idx_event_timeline_highlights',
      EventTimeline.project_id, EventTimeline.is_highlight)
