"""
Advanced Escalation Management Models for Retinue.

This module defines the complete data model for the escalations management system
including escalations, timeline events, comments, and statistics tracking.
"""
from sqlalchemy import Column, String, Text, Integer, Boolean, TIMESTAMP, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid
import enum

from app.db.database import Base


# Enums for Escalation System
class EscalationType(str, enum.Enum):
    """Types of escalations that can occur in the system."""
    TECHNICAL_DECISION = "technical_decision"
    BUDGET_THRESHOLD = "budget_threshold"
    AGENT_MALFUNCTION = "agent_malfunction"
    RESOURCE_ALLOCATION = "resource_allocation"
    CROSS_DEPT_CONFLICT = "cross_dept_conflict"
    DEADLINE_RISK = "deadline_risk"
    SCOPE_CHANGE = "scope_change"
    STRATEGIC_DIRECTION = "strategic_direction"
    RESOURCE_CONFLICT = "resource_conflict"
    PRIORITY_CONFLICT = "priority_conflict"
    BLOCKED_TASK = "blocked_task"
    SCOPE_CREEP = "scope_creep"


class EscalationPriority(str, enum.Enum):
    """Priority levels for escalations."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"


class EscalationStatus(str, enum.Enum):
    """Current status of an escalation."""
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_AGENT = "pending_agent"
    PENDING_HUMAN = "pending_human"
    BLOCKED = "blocked"
    RESOLVED = "resolved"
    ESCALATED = "escalated"
    CLOSED = "closed"


class EscalationLevel(str, enum.Enum):
    """Hierarchical level of escalation."""
    DEPARTMENT = "department"
    EXECUTIVE = "executive"
    HUMAN = "human"


class ResolutionType(str, enum.Enum):
    """How the escalation was resolved."""
    AUTO_RESOLVED = "auto_resolved"
    HUMAN_DECISION = "human_decision"
    AGENT_COLLABORATION = "agent_collaboration"
    ESCALATED_RESOLVED = "escalated_resolved"


class ImpactLevel(str, enum.Enum):
    """Impact assessment of the escalation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class UrgencyLevel(str, enum.Enum):
    """Urgency level of the escalation."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EscalationEventType(str, enum.Enum):
    """Types of timeline events for escalations."""
    CREATED = "created"
    ASSIGNED = "assigned"
    STATUS_CHANGED = "status_changed"
    PRIORITY_CHANGED = "priority_changed"
    RESOLVED = "resolved"
    ESCALATED_TO_HIGHER_LEVEL = "escalated_to_higher_level"
    CONFLICT_DETECTED = "conflict_detected"
    SLA_BREACH_WARNING = "sla_breach_warning"
    AUTO_RESOLVED = "auto_resolved"
    HUMAN_INTERVENTION_REQUIRED = "human_intervention_required"
    AGENT_COLLABORATION_STARTED = "agent_collaboration_started"
    COMMENT_ADDED = "comment_added"
    REASSIGNED = "reassigned"
    REOPENED = "reopened"
    CLOSED = "closed"


# Models
class AdvancedEscalation(Base):
    """
    Advanced escalation model with comprehensive tracking and management features.
    Replaces the simple Escalation model with full-featured escalation management.
    """
    __tablename__ = "advanced_escalations"

    # Primary identification
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escalation_number = Column(String(50), unique=True, nullable=False)  # ESC-2024-001
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Classification
    escalation_type = Column(SQLEnum(EscalationType), nullable=False)
    priority = Column(SQLEnum(EscalationPriority), nullable=False)
    status = Column(SQLEnum(EscalationStatus), nullable=False, default=EscalationStatus.OPEN)
    level = Column(SQLEnum(EscalationLevel), nullable=False, default=EscalationLevel.DEPARTMENT)
    
    # Assignment and ownership
    created_by_type = Column(String(20), nullable=False)  # 'agent' or 'user'
    created_by_id = Column(String(100), nullable=False)  # agent_id or user_id
    assigned_to_type = Column(String(20), nullable=True)  # 'agent' or 'user'
    assigned_to_id = Column(String(100), nullable=True)  # Current assignee
    assigned_at = Column(TIMESTAMP, nullable=True)
    escalation_path = Column(JSONB, default=list)  # History of assignments
    
    # Related entities
    related_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=True)
    related_project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=True)
    related_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)
    conflict_parties = Column(JSONB, default=list)  # List of involved parties
    
    # Timing and SLA
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    resolved_at = Column(TIMESTAMP, nullable=True)
    closed_at = Column(TIMESTAMP, nullable=True)
    due_date = Column(TIMESTAMP, nullable=True)
    sla_deadline = Column(TIMESTAMP, nullable=False)
    time_to_first_response = Column(Integer, nullable=True)  # Minutes
    time_to_resolution = Column(Integer, nullable=True)  # Minutes
    
    # Resolution details
    resolution_notes = Column(Text, nullable=True)
    resolution_type = Column(SQLEnum(ResolutionType), nullable=True)
    auto_resolution_attempts = Column(Integer, default=0)
    resolved_by_type = Column(String(20), nullable=True)  # 'agent' or 'user'
    resolved_by_id = Column(String(100), nullable=True)
    
    # Assessment
    impact_assessment = Column(SQLEnum(ImpactLevel), nullable=False)
    urgency = Column(SQLEnum(UrgencyLevel), nullable=False)
    department = Column(String(100), nullable=True)
    
    # Metadata
    tags = Column(ARRAY(String), default=list)
    meta_data = Column(JSONB, default=dict)
    
    # Soft delete
    deleted_at = Column(TIMESTAMP, nullable=True)
    
    # Relationships (will be set up after all models are defined)
    # timeline = relationship("EscalationTimelineEvent", back_populates="escalation")
    # comments = relationship("EscalationComment", back_populates="escalation")


class EscalationTimelineEvent(Base):
    """
    Timeline events for tracking all changes and actions on an escalation.
    Provides complete audit trail and history.
    """
    __tablename__ = "escalation_timeline_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escalation_id = Column(UUID(as_uuid=True), ForeignKey("advanced_escalations.id", ondelete="CASCADE"), nullable=False)
    
    # Event details
    event_type = Column(SQLEnum(EscalationEventType), nullable=False)
    actor_type = Column(String(20), nullable=False)  # 'agent', 'user', or 'system'
    actor_id = Column(String(100), nullable=False)
    timestamp = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    
    # Event data
    description = Column(Text, nullable=False)
    details = Column(JSONB, default=dict)
    previous_state = Column(JSONB, nullable=True)
    new_state = Column(JSONB, nullable=True)
    
    # Metadata
    meta_data = Column(JSONB, default=dict)
    
    # Relationship
    # escalation = relationship("AdvancedEscalation", back_populates="timeline")


class EscalationComment(Base):
    """
    Comments and discussion on escalations.
    Supports threaded conversations and attachments.
    """
    __tablename__ = "escalation_comments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escalation_id = Column(UUID(as_uuid=True), ForeignKey("advanced_escalations.id", ondelete="CASCADE"), nullable=False)
    
    # Author details
    author_type = Column(String(20), nullable=False)  # 'agent' or 'user'
    author_id = Column(String(100), nullable=False)
    
    # Comment content
    content = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Visibility and organization
    is_internal = Column(Boolean, default=False)  # Hidden from certain viewers
    parent_comment_id = Column(UUID(as_uuid=True), ForeignKey("escalation_comments.id"), nullable=True)  # For threading
    
    # Attachments and metadata
    attachments = Column(JSONB, default=list)  # List of file references
    mentions = Column(JSONB, default=list)  # List of @mentioned users/agents
    meta_data = Column(JSONB, default=dict)
    
    # Soft delete
    deleted_at = Column(TIMESTAMP, nullable=True)
    
    # Relationship
    # escalation = relationship("AdvancedEscalation", back_populates="comments")


class EscalationNotification(Base):
    """
    Notification tracking for escalation-related events.
    Multi-channel notification management.
    """
    __tablename__ = "escalation_notifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escalation_id = Column(UUID(as_uuid=True), ForeignKey("advanced_escalations.id", ondelete="CASCADE"), nullable=False)
    
    # Recipient
    recipient_type = Column(String(20), nullable=False)  # 'agent' or 'user'
    recipient_id = Column(String(100), nullable=False)
    
    # Notification details
    notification_type = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    priority = Column(SQLEnum(EscalationPriority), nullable=False)
    
    # Channels
    channels = Column(JSONB, default=list)  # ['in_app', 'email', 'slack', 'sms']
    
    # Delivery status
    sent_at = Column(TIMESTAMP, nullable=True)
    delivered_at = Column(TIMESTAMP, nullable=True)
    read_at = Column(TIMESTAMP, nullable=True)
    failed_at = Column(TIMESTAMP, nullable=True)
    failure_reason = Column(Text, nullable=True)
    
    # Reminders
    reminder_count = Column(Integer, default=0)
    next_reminder_at = Column(TIMESTAMP, nullable=True)
    
    # Action tracking
    action_taken = Column(Boolean, default=False)
    action_taken_at = Column(TIMESTAMP, nullable=True)
    
    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    meta_data = Column(JSONB, default=dict)


class EscalationCollaboration(Base):
    """
    Agent collaboration sessions for resolving escalations.
    Tracks multi-agent discussions and consensus building.
    """
    __tablename__ = "escalation_collaborations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escalation_id = Column(UUID(as_uuid=True), ForeignKey("advanced_escalations.id", ondelete="CASCADE"), nullable=False)
    
    # Collaboration details
    lead_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False)
    participating_agents = Column(JSONB, default=list)  # List of agent IDs
    
    # Status
    status = Column(String(50), nullable=False, default="active")  # active, completed, failed
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    completed_at = Column(TIMESTAMP, nullable=True)
    
    # Results
    consensus_reached = Column(Boolean, default=False)
    votes = Column(JSONB, default=dict)  # agent_id -> vote/decision
    final_decision = Column(Text, nullable=True)
    disagreements = Column(JSONB, default=list)
    
    # Metadata
    conversation_log = Column(JSONB, default=list)
    meta_data = Column(JSONB, default=dict)


class EscalationSLAConfig(Base):
    """
    SLA configuration for different escalation types.
    Defines time limits and warning thresholds.
    """
    __tablename__ = "escalation_sla_configs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    escalation_type = Column(SQLEnum(EscalationType), nullable=False)
    priority = Column(SQLEnum(EscalationPriority), nullable=False)
    
    # Time limits (in minutes)
    time_to_first_response = Column(Integer, nullable=False)  # How quickly must be acknowledged
    time_to_resolution = Column(Integer, nullable=False)  # How quickly must be resolved
    
    # Warning thresholds (percentage of time consumed)
    warning_threshold_percent = Column(Integer, default=75)  # Alert at 75% of SLA
    critical_threshold_percent = Column(Integer, default=90)  # Critical alert at 90%
    
    # Escalation rules
    auto_escalate_on_breach = Column(Boolean, default=True)
    escalate_to_level = Column(SQLEnum(EscalationLevel), nullable=True)
    
    # Active status
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)


class EscalationTemplate(Base):
    """
    Pre-defined templates for common escalation scenarios.
    Speeds up escalation creation with best practices.
    """
    __tablename__ = "escalation_templates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Template configuration
    escalation_type = Column(SQLEnum(EscalationType), nullable=False)
    default_priority = Column(SQLEnum(EscalationPriority), nullable=False)
    default_impact = Column(SQLEnum(ImpactLevel), nullable=False)
    default_urgency = Column(SQLEnum(UrgencyLevel), nullable=False)
    
    # Template content
    title_template = Column(String(255), nullable=False)
    description_template = Column(Text, nullable=False)
    suggested_tags = Column(JSONB, default=list)
    
    # Auto-assignment rules
    auto_assign_to = Column(String(100), nullable=True)  # agent_id or role
    auto_assign_level = Column(SQLEnum(EscalationLevel), nullable=True)
    
    # Usage tracking
    usage_count = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_by_type = Column(String(20), nullable=False)
    created_by_id = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    meta_data = Column(JSONB, default=dict)


class EscalationPlaybook(Base):
    """
    Step-by-step playbooks for handling specific escalation types.
    Guides users and agents through resolution process.
    """
    __tablename__ = "escalation_playbooks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    
    # Applicability
    escalation_type = Column(SQLEnum(EscalationType), nullable=False)
    applies_to_levels = Column(JSONB, default=list)  # Which levels this playbook applies to
    
    # Playbook content
    steps = Column(JSONB, nullable=False)  # Ordered list of steps with instructions
    best_practices = Column(JSONB, default=list)
    common_pitfalls = Column(JSONB, default=list)
    success_criteria = Column(JSONB, default=list)
    
    # Resources
    related_knowledge_base_ids = Column(JSONB, default=list)
    related_templates = Column(JSONB, default=list)
    
    # Usage and effectiveness
    usage_count = Column(Integer, default=0)
    success_rate = Column(Float, nullable=True)  # Percentage of successful resolutions
    is_active = Column(Boolean, default=True)
    
    # Metadata
    created_by_type = Column(String(20), nullable=False)
    created_by_id = Column(String(100), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
    meta_data = Column(JSONB, default=dict)


class EscalationWatchlist(Base):
    """
    User/agent watchlist for following specific escalations.
    Enables custom notification subscriptions.
    """
    __tablename__ = "escalation_watchlist"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    escalation_id = Column(UUID(as_uuid=True), ForeignKey("advanced_escalations.id", ondelete="CASCADE"), nullable=False)
    
    # Watcher details
    watcher_type = Column(String(20), nullable=False)  # 'agent' or 'user'
    watcher_id = Column(String(100), nullable=False)
    
    # Subscription preferences
    notification_preferences = Column(JSONB, default=dict)  # Custom notification settings
    
    # Tracking
    added_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    last_viewed_at = Column(TIMESTAMP, nullable=True)
    
    # Unique constraint on escalation + watcher
    __table_args__ = (
        {'extend_existing': True}
    )


class EscalationAnalytics(Base):
    """
    Aggregated analytics and metrics for escalation performance.
    Updated periodically for dashboard displays.
    """
    __tablename__ = "escalation_analytics"

    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Time period
    period_start = Column(TIMESTAMP, nullable=False)
    period_end = Column(TIMESTAMP, nullable=False)
    period_type = Column(String(20), nullable=False)  # 'hourly', 'daily', 'weekly', 'monthly'
    
    # Volume metrics
    total_escalations = Column(Integer, default=0)
    escalations_created = Column(Integer, default=0)
    escalations_resolved = Column(Integer, default=0)
    escalations_closed = Column(Integer, default=0)
    open_escalations = Column(Integer, default=0)
    
    # Performance metrics
    avg_time_to_first_response = Column(Float, nullable=True)  # Minutes
    avg_time_to_resolution = Column(Float, nullable=True)  # Minutes
    median_time_to_resolution = Column(Float, nullable=True)
    
    # SLA metrics
    sla_compliance_rate = Column(Float, nullable=True)  # Percentage
    sla_breaches = Column(Integer, default=0)
    
    # Resolution metrics
    auto_resolution_count = Column(Integer, default=0)
    auto_resolution_success_rate = Column(Float, nullable=True)
    human_intervention_count = Column(Integer, default=0)
    human_intervention_rate = Column(Float, nullable=True)
    
    # By type/priority
    by_type = Column(JSONB, default=dict)  # Breakdown by escalation type
    by_priority = Column(JSONB, default=dict)  # Breakdown by priority
    by_level = Column(JSONB, default=dict)  # Breakdown by escalation level
    by_department = Column(JSONB, default=dict)
    
    # Agent performance
    by_agent = Column(JSONB, default=dict)  # Performance per agent
    
    # Trend indicators
    trend_vs_previous_period = Column(Float, nullable=True)  # Percentage change
    
    # Metadata
    calculated_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    meta_data = Column(JSONB, default=dict)
