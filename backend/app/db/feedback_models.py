"""SQLAlchemy models for user feedback and context management."""
from sqlalchemy import Column, String, Text, Integer, Boolean, TIMESTAMP, ForeignKey, Enum as SQLEnum, Float
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from app.db.database import Base


class FeedbackType(str, enum.Enum):
    """Types of feedback that can be provided."""
    GENERAL = "general"  # General comments
    QUALITY = "quality"  # Quality assessment
    CORRECTNESS = "correctness"  # Correctness of output
    COMPLETENESS = "completeness"  # Completeness of work
    DIRECTION = "direction"  # Strategic direction feedback
    IMPLEMENTATION = "implementation"  # Implementation approach
    BLOCKING_ISSUE = "blocking_issue"  # Something is blocking progress
    ENHANCEMENT = "enhancement"  # Enhancement suggestion
    BUG_REPORT = "bug_report"  # Bug or error found
    PERFORMANCE = "performance"  # Performance feedback


class FeedbackSource(str, enum.Enum):
    """Who or what provided the feedback."""
    USER = "user"  # Direct user input
    SYSTEM = "system"  # System generated
    AGENT_REVIEW = "agent_review"  # Agent peer review
    AUTOMATED = "automated"  # Automated analysis


class FeedbackStatus(str, enum.Enum):
    """Status of feedback processing."""
    PENDING = "pending"  # Not yet processed
    ACKNOWLEDGED = "acknowledged"  # Reviewed by system
    IN_PROGRESS = "in_progress"  # Being acted upon
    IMPLEMENTED = "implemented"  # Changes made based on feedback
    RESOLVED = "resolved"  # Feedback fully addressed
    REJECTED = "rejected"  # Feedback rejected with reason
    ARCHIVED = "archived"  # Old feedback


class ProjectFeedback(Base):
    """User feedback on projects."""
    __tablename__ = "project_feedback"

    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)

    # Feedback metadata
    feedback_type = Column(SQLEnum(FeedbackType), nullable=False)
    source = Column(SQLEnum(FeedbackSource), default=FeedbackSource.USER, nullable=False)
    status = Column(SQLEnum(FeedbackStatus), default=FeedbackStatus.PENDING, nullable=False)

    # Content
    title = Column(String(255), nullable=False)  # Brief feedback title
    description = Column(Text, nullable=False)  # Detailed feedback/context
    context = Column(JSONB, default={})  # Additional context (what was being done, etc.)

    # Ratings
    quality_rating = Column(Integer, nullable=True)  # 1-5 scale
    satisfaction_rating = Column(Integer, nullable=True)  # 1-5 scale
    confidence_level = Column(Integer, nullable=True)  # 1-5 scale in feedback accuracy

    # Suggested actions
    suggested_actions = Column(JSONB, default=[])  # Array of suggested next steps
    priority = Column(String(20), default="medium")  # low, medium, high, critical

    # Addressing the feedback
    assigned_to_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)
    implementation_notes = Column(Text, nullable=True)
    implemented_changes = Column(JSONB, default=[])  # What changes were made

    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    created_by_user = Column(String(255), nullable=True)  # Human user ID
    meta_data = Column(JSONB, default={})


class TaskFeedback(Base):
    """User feedback on tasks."""
    __tablename__ = "task_feedback"

    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)

    # Feedback metadata
    feedback_type = Column(SQLEnum(FeedbackType), nullable=False)
    source = Column(SQLEnum(FeedbackSource), default=FeedbackSource.USER, nullable=False)
    status = Column(SQLEnum(FeedbackStatus), default=FeedbackStatus.PENDING, nullable=False)

    # Content
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    context = Column(JSONB, default={})

    # Ratings (specific to tasks)
    output_quality = Column(Integer, nullable=True)  # 1-5
    correctness = Column(Integer, nullable=True)  # 1-5
    completeness = Column(Integer, nullable=True)  # 1-5
    implementation_quality = Column(Integer, nullable=True)  # 1-5

    # Code/implementation specific
    code_review_feedback = Column(Text, nullable=True)
    suggested_improvements = Column(JSONB, default=[])  # Array of improvement suggestions

    # Action items
    action_items = Column(JSONB, default=[])  # Specific things to do
    priority = Column(String(20), default="medium")

    # Processing
    assigned_to_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)
    implementation_plan = Column(Text, nullable=True)
    changes_made = Column(JSONB, default=[])

    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    created_by_user = Column(String(255), nullable=True)
    meta_data = Column(JSONB, default={})


class AgentFeedback(Base):
    """Feedback on agent performance and decisions."""
    __tablename__ = "agent_feedback"

    feedback_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), ForeignKey("agents.agent_id", ondelete="CASCADE"), nullable=False)
    related_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=True)
    related_project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=True)

    # Feedback metadata
    feedback_type = Column(SQLEnum(FeedbackType), nullable=False)
    source = Column(SQLEnum(FeedbackSource), default=FeedbackSource.USER, nullable=False)
    status = Column(SQLEnum(FeedbackStatus), default=FeedbackStatus.PENDING, nullable=False)

    # Content
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    context = Column(JSONB, default={})

    # Agent performance metrics
    decision_quality = Column(Integer, nullable=True)  # 1-5
    execution_quality = Column(Integer, nullable=True)  # 1-5
    communication_clarity = Column(Integer, nullable=True)  # 1-5
    problem_solving = Column(Integer, nullable=True)  # 1-5
    efficiency = Column(Integer, nullable=True)  # 1-5

    # Behavioral feedback
    behavior_observations = Column(Text, nullable=True)
    recommended_improvements = Column(JSONB, default=[])  # Areas to improve
    strengths_noted = Column(JSONB, default=[])  # What the agent does well

    # Learning integration
    suggested_system_prompt_updates = Column(Text, nullable=True)
    priority = Column(String(20), default="medium")

    # Processing
    acknowledged_by_system = Column(Boolean, default=False)
    system_response = Column(Text, nullable=True)
    meta_data = Column(JSONB, default={})

    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    created_by_user = Column(String(255), nullable=True)


class ContextUpdate(Base):
    """Track context and information added to projects/tasks."""
    __tablename__ = "context_updates"

    context_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # What is being contextualized
    entity_type = Column(String(50), nullable=False)  # 'project', 'task', 'agent'
    entity_id = Column(UUID(as_uuid=True), nullable=False)

    # Context content
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    context_tags = Column(JSONB, default=[])  # Tags like ['requirements', 'architecture', 'bug', 'enhancement']

    # Source
    source = Column(String(50), default="user")  # user, system, agent
    created_by_user = Column(String(255), nullable=True)

    # Link to related feedback (if context was from feedback)
    related_feedback_id = Column(UUID(as_uuid=True), nullable=True)

    # Impact tracking
    referenced_by_count = Column(Integer, default=0)  # How many agents/tasks referenced this
    implementation_status = Column(String(50), default="pending")  # pending, in_progress, implemented
    related_agent_updates = Column(JSONB, default=[])  # List of agents that received this context

    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    meta_data = Column(JSONB, default={})


class SystemLearning(Base):
    """Track lessons learned from feedback for system improvement."""
    __tablename__ = "system_learning"

    learning_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # What was learned
    learning_type = Column(String(50), nullable=False)  # 'pattern', 'mistake', 'improvement', 'best_practice'
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)

    # Related feedback
    source_feedback_ids = Column(JSONB, default=[])  # Which feedback contributed to this learning
    affected_agent_ids = Column(JSONB, default=[])  # Which agents should know about this
    affected_task_types = Column(JSONB, default=[])  # Which task types are affected

    # Implementation
    proposed_solution = Column(Text, nullable=True)
    implementation_instructions = Column(Text, nullable=True)
    system_prompt_update = Column(Text, nullable=True)  # Suggested prompt change
    configuration_changes = Column(JSONB, default={})  # Config changes to apply

    # Effectiveness
    confidence_score = Column(Float, default=0.5)  # 0.0-1.0
    tested = Column(Boolean, default=False)
    effectiveness_notes = Column(Text, nullable=True)

    # Status
    status = Column(String(50), default="proposed")  # proposed, approved, implemented, archived
    priority = Column(String(20), default="medium")

    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    meta_data = Column(JSONB, default={})
