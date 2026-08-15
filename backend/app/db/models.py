"""SQLAlchemy database models for the AI Agent Company platform."""
from sqlalchemy import Column, String, Text, Integer, Boolean, TIMESTAMP, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from app.db.database import Base


# Enums
class ProjectStatus(str, enum.Enum):
    PLANNING = "PLANNING"
    IN_PROGRESS = "IN_PROGRESS"
    REVIEW = "REVIEW"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    ON_HOLD = "ON_HOLD"
    FAILED = "FAILED"


class TaskStatus(str, enum.Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    REVIEW = "REVIEW"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"
    FAILED = "FAILED"


class Priority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    URGENT = "urgent"


class MessageType(str, enum.Enum):
    INFO = "info"
    REQUEST = "request"
    APPROVAL = "approval"
    ALERT = "alert"


class MessageStatus(str, enum.Enum):
    """Status of agent-to-agent messages."""
    SENT = "sent"                    # Message sent, not yet received
    RECEIVED = "received"            # Message received by agent
    READ = "read"                    # Message read by agent
    IN_PROGRESS = "in_progress"      # Agent is working on the request/issue
    RESOLVED = "resolved"            # Issue resolved, message closed
    ESCALATED = "escalated"          # Message escalated to another agent
    CANCELLED = "cancelled"          # Message cancelled/no longer relevant


class Availability(str, enum.Enum):
    AVAILABLE = "available"
    BUSY = "busy"
    BLOCKED = "blocked"
    OFFLINE = "offline"


# Phase 1 RAG-Related Enums
class TaskRAGStatus(str, enum.Enum):
    """Status of RAG indexing for a task."""
    NOT_INDEXED = "not_indexed"
    INDEXING = "indexing"
    INDEXED = "indexed"
    FAILED = "failed"


class RelevanceLevel(str, enum.Enum):
    """Relevance level of retrieved context."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


# Models
class Agent(Base):
    """Agent model representing an AI agent in the system."""
    __tablename__ = "agents"

    agent_id = Column(String(100), primary_key=True)
    name = Column(String(100), nullable=False)
    role = Column(String(100), nullable=False)
    department = Column(String(50), nullable=False)  # Legacy: kept for backwards compatibility
    departments = Column(JSONB, nullable=True)  # New: array of departments
    reports_to = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)
    permissions = Column(JSONB, nullable=False)
    status = Column(String(50), default="active")
    llm_model = Column(String(100), default="claude-3-5-sonnet-20241022")
    system_prompt = Column(Text, nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    meta_data = Column(JSONB, default={})

    # Phase 0: Business Operations Expansion
    output_types = Column(JSONB, nullable=False, server_default="[\"text\"]")  # What this agent can produce
    specializations = Column(JSONB, nullable=False, server_default="[]")  # Skills/expertise areas
    required_for_types = Column(JSONB, nullable=False, server_default="[]")  # Which deliverable types require this agent

    @property
    def all_departments(self) -> list:
        """Get all departments for this agent (supports both legacy and new format)."""
        if self.departments:
            return self.departments
        # Fallback to legacy single department
        return [self.department] if self.department else []

    @property
    def primary_department(self) -> str:
        """Get the primary (first) department for this agent."""
        depts = self.all_departments
        return depts[0] if depts else "unknown"


class AgentStatus(Base):
    """Real-time status of agents."""
    __tablename__ = "agent_status"

    agent_id = Column(String(100), ForeignKey("agents.agent_id", ondelete="CASCADE"), primary_key=True)
    current_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=True)
    availability = Column(SQLEnum(Availability), nullable=False)
    last_active = Column(TIMESTAMP, server_default=func.now())
    last_check_time = Column(TIMESTAMP, server_default=func.now())
    pending_approvals_count = Column(Integer, default=0)
    current_context = Column(JSONB, default={})
    health_status = Column(String(50), default="healthy")
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class Project(Base):
    """Project model representing a complete project/request."""
    __tablename__ = "projects"

    project_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(ProjectStatus), nullable=False)
    priority = Column(SQLEnum(Priority), nullable=False)
    owner_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False)
    requester_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    deadline = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)
    agent_days_elapsed = Column(Integer, default=0)
    version = Column(Integer, default=1)
    parent_project_id = Column(UUID(as_uuid=True), nullable=True)
    deleted_at = Column(TIMESTAMP, nullable=True)
    meta_data = Column(JSONB, default={})

    # Phase 2 RAG Integration Fields
    embedding_id = Column(String(255), nullable=True)  # ChromaDB embedding ID
    rag_status = Column(SQLEnum(TaskRAGStatus), default=TaskRAGStatus.NOT_INDEXED)  # Indexing status
    rag_indexed_at = Column(TIMESTAMP, nullable=True)  # When project was indexed
    rag_similarity_score = Column(Integer, nullable=True)  # Quality score (0-100) for retrieval relevance

    # Phase 0: Business Operations Expansion
    project_type = Column(String(50), nullable=False, server_default='custom')  # Type of project
    deliverable_type = Column(String(50), ForeignKey("deliverable_types.type_id"), nullable=True)  # Deliverable type
    selected_agents = Column(JSONB, nullable=False, server_default="[]")  # List of selected agent IDs


class Task(Base):
    """Task model representing individual tasks within a project."""
    __tablename__ = "tasks"

    task_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    assigned_to_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text)
    status = Column(SQLEnum(TaskStatus), nullable=False)
    dependencies = Column(JSONB, default=[])
    approval_required_from = Column(String(100), nullable=True)
    version = Column(Integer, default=1)
    parent_task_id = Column(UUID(as_uuid=True), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    estimated_hours = Column(Integer, nullable=True)
    actual_hours = Column(Integer, nullable=True)
    blocking_reason = Column(Text, nullable=True)
    deleted_at = Column(TIMESTAMP, nullable=True)
    output = Column(JSONB, nullable=True)
    review_started_at = Column(TIMESTAMP, nullable=True)

    # Phase 0: Business Operations Expansion
    output_format = Column(String(50), nullable=False, server_default='text')  # Output format type
    output_metadata = Column(JSONB, nullable=False, server_default="{}") # Format-specific metadata

    # Phase 1 RAG Integration Fields
    embedding_id = Column(String(255), nullable=True)  # ChromaDB embedding ID
    rag_status = Column(SQLEnum(TaskRAGStatus), default=TaskRAGStatus.NOT_INDEXED)  # Indexing status
    rag_indexed_at = Column(TIMESTAMP, nullable=True)  # When task was indexed
    rag_similarity_score = Column(Integer, nullable=True)  # Quality score (0-100) for retrieval relevance
    rag_contexts = Column(JSONB, default=[])  # Cached retrieved contexts: [{"task_id": "...", "score": 0.85, "excerpt": "..."}]
    rag_patterns = Column(JSONB, default=[])  # Patterns extracted from this task: [{"name": "...", "score": 0.8}]
    rag_last_context_at = Column(TIMESTAMP, nullable=True)  # When context was last retrieved

    # Phase 2 User Control Fields
    is_paused = Column(Boolean, default=False)  # Whether task is currently paused
    pause_reason = Column(Text, nullable=True)  # Why the task was paused
    paused_at = Column(TIMESTAMP, nullable=True)  # When task was paused
    user_context = Column(Text, nullable=True)  # User-provided context/hints for agent


class Message(Base):
    """Message model for agent-to-agent communication."""
    __tablename__ = "messages"

    message_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False)
    to_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)
    channel = Column(String(100), nullable=True)
    content = Column(Text, nullable=False)
    message_type = Column(SQLEnum(MessageType), nullable=True)
    priority = Column(SQLEnum(Priority), default=Priority.MEDIUM)

    # Enhanced status tracking
    status = Column(SQLEnum(MessageStatus), default=MessageStatus.SENT, nullable=False)
    read_status = Column(Boolean, default=False)  # Deprecated, kept for backward compatibility

    # Tracking fields
    received_at = Column(TIMESTAMP, nullable=True)
    read_at = Column(TIMESTAMP, nullable=True)
    read_by_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)
    resolved_at = Column(TIMESTAMP, nullable=True)
    resolved_by_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)
    resolution_note = Column(Text, nullable=True)

    related_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=True)
    related_project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=True)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    meta_data = Column(JSONB, default={})


class Decision(Base):
    """Decision log for tracking agent decisions."""
    __tablename__ = "decisions"

    decision_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=True)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=True)
    made_by_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False)
    decision_type = Column(String(50), nullable=False)
    decision_category = Column(String(50), nullable=True)
    question = Column(Text, nullable=False)
    rationale = Column(Text, nullable=False)
    decision = Column(Text, nullable=False)
    approved = Column(Boolean, nullable=True)
    approved_by = Column(String(100), nullable=True)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    meta_data = Column(JSONB, default={})

    # Phase 2 RAG Integration Fields
    embedding_id = Column(String(255), nullable=True)  # ChromaDB embedding ID
    rag_indexed_at = Column(TIMESTAMP, nullable=True)  # When decision was indexed


class KnowledgeBase(Base):
    """Knowledge base for storing documentation and learnings."""
    __tablename__ = "knowledge_base"

    document_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    category = Column(String(100), nullable=False)
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    created_by_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False)
    access_level = Column(String(50), default="public")
    version = Column(Integer, default=1)
    tags = Column(JSONB, default=[])
    created_at = Column(TIMESTAMP, server_default=func.now())
    last_updated = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    meta_data = Column(JSONB, default={})


class Escalation(Base):
    """Escalation tracking for blocked or problematic tasks."""
    __tablename__ = "escalations"

    escalation_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    issue_type = Column(String(50), nullable=False)
    severity = Column(SQLEnum(Priority), nullable=False)
    escalated_by_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False)
    escalated_to_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False)
    related_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.task_id"), nullable=True)
    related_project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id"), nullable=True)
    description = Column(Text, nullable=False)
    resolution = Column(Text, nullable=True)
    status = Column(String(50), default="open")
    created_at = Column(TIMESTAMP, server_default=func.now())
    resolved_at = Column(TIMESTAMP, nullable=True)
    meta_data = Column(JSONB, default={})

    # Phase 2 RAG Integration Fields
    embedding_id = Column(String(255), nullable=True)  # ChromaDB embedding ID
    rag_indexed_at = Column(TIMESTAMP, nullable=True)  # When escalation was indexed




class HumanInteraction(Base):
    """Track interactions requiring human input."""
    __tablename__ = "human_interactions"

    interaction_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    initiated_by_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=False)
    interaction_type = Column(String(50), nullable=False)
    related_entity_type = Column(String(50), nullable=True)
    related_entity_id = Column(UUID(as_uuid=True), nullable=True)
    request = Column(Text, nullable=False)
    human_response = Column(Text, nullable=True)
    status = Column(String(50), default="pending")
    created_at = Column(TIMESTAMP, server_default=func.now())
    responded_at = Column(TIMESTAMP, nullable=True)
    meta_data = Column(JSONB, default={})


class NotificationType(str, enum.Enum):
    HUMAN_INTERVENTION_REQUIRED = "human_intervention_required"
    CEO_FEEDBACK = "ceo_feedback"
    PROJECT_COMPLETED = "project_completed"
    PROJECT_FAILED = "project_failed"
    TASK_BLOCKED = "task_blocked"
    ESCALATION = "escalation"
    GENERAL = "general"


class Notification(Base):
    """User notifications for important events."""
    __tablename__ = "notifications"

    notification_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    type = Column(SQLEnum(NotificationType), nullable=False)
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    related_entity_type = Column(String(50), nullable=True)
    related_entity_id = Column(UUID(as_uuid=True), nullable=True)
    agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)
    priority = Column(SQLEnum(Priority), default=Priority.MEDIUM)
    read = Column(Boolean, default=False)
    read_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    meta_data = Column(JSONB, default={})


class SystemSettings(Base):
    """System-wide configuration settings (Admin only)."""
    __tablename__ = "system_settings"

    id = Column(Integer, primary_key=True, autoincrement=True)
    # LLM Configuration
    default_llm_model = Column(String(100), default="claude-3-5-sonnet-20241022")
    llm_temperature = Column(Integer, default=70)  # Stored as integer (0-200 for 0.0-2.0)
    llm_max_tokens = Column(Integer, default=4096)
    show_thinking_process = Column(Boolean, default=True)
    context_strategy = Column(String(50), default="full_history")
    
    # Agent Behavior
    default_communication_style = Column(String(50), default="professional")
    escalation_time_threshold = Column(Integer, default=60)  # minutes
    auto_retry_attempts = Column(Integer, default=3)
    agent_autonomy_level = Column(String(50), default="medium")
    
    # Performance
    request_caching_enabled = Column(Boolean, default=True)
    concurrent_agent_limit = Column(Integer, default=10)
    auto_scaling_enabled = Column(Boolean, default=False)
    
    # Logging
    log_level = Column(String(20), default="INFO")
    debug_mode = Column(Boolean, default=False)
    
    # Backup
    auto_backup_enabled = Column(Boolean, default=True)
    backup_frequency = Column(String(20), default="daily")
    
    # Additional settings stored as JSONB for flexibility
    advanced_settings = Column(JSONB, default={})
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    updated_by = Column(String(100), nullable=True)


class UserProfile(Base):
    """User profile with personal preferences."""
    __tablename__ = "user_profiles"

    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Personal Information
    full_name = Column(String(255), nullable=False)
    display_name = Column(String(100), nullable=True)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(50), nullable=True)
    job_title = Column(String(100), nullable=True)
    department = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    pronouns = Column(String(50), nullable=True)
    timezone = Column(String(100), default="UTC")
    
    # Appearance Preferences
    theme = Column(String(20), default="dark")
    display_density = Column(String(20), default="comfortable")
    font_size = Column(Integer, default=14)
    language = Column(String(10), default="en")
    animations_enabled = Column(Boolean, default=True)
    sidebar_collapsed = Column(Boolean, default=False)
    default_landing_page = Column(String(50), default="dashboard")
    
    # Notification Preferences
    email_notifications = Column(String(20), default="realtime")
    desktop_notifications = Column(Boolean, default=True)
    notification_sounds = Column(Boolean, default=True)
    notification_preferences = Column(JSONB, default={})
    
    # Privacy Settings
    show_online_status = Column(Boolean, default=True)
    show_last_active = Column(Boolean, default=True)
    show_email_in_directory = Column(Boolean, default=False)
    activity_broadcasting = Column(Boolean, default=True)
    
    # Work Preferences
    work_start_time = Column(String(10), default="09:00")
    work_end_time = Column(String(10), default="17:00")
    default_task_view = Column(String(20), default="list")
    availability_status = Column(String(20), default="available")
    
    # Connected Accounts (stored as JSONB)
    connected_accounts = Column(JSONB, default={})
    
    # Role and Permissions
    role = Column(String(50), default="member")
    is_admin = Column(Boolean, default=False)
    
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    last_login = Column(TIMESTAMP, nullable=True)
    meta_data = Column(JSONB, default={})


class SettingsAuditLog(Base):
    """Audit trail for system settings and profile changes."""
    __tablename__ = "settings_audit_log"

    log_id = Column(Integer, primary_key=True, autoincrement=True)
    entity_type = Column(String(50), nullable=False)  # 'system_settings' or 'user_profile'
    entity_id = Column(String(100), nullable=True)  # user_id for profiles, null for system settings
    changed_by_user_id = Column(UUID(as_uuid=True), nullable=True)
    changed_by_admin = Column(Boolean, default=False)
    field_name = Column(String(100), nullable=False)
    old_value = Column(Text, nullable=True)
    new_value = Column(Text, nullable=True)
    change_reason = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    meta_data = Column(JSONB, default={})


# ===== PHASE 0: BUSINESS OPERATIONS EXPANSION MODELS =====

class Department(Base):
    """Department/team organization for the business."""
    __tablename__ = "departments"

    department_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    icon = Column(String(50), nullable=True)  # For UI display (e.g., 'briefcase', 'code')
    color = Column(String(20), nullable=True)  # For UI display (e.g., '#8B4513')
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


class DeliverableType(Base):
    """Types of deliverables projects can produce."""
    __tablename__ = "deliverable_types"

    type_id = Column(String(50), primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    typical_agents = Column(JSONB, nullable=False, default=[])  # List of typical agent IDs for this type
    output_format = Column(String(50), nullable=True)  # pdf, docx, xlsx, pptx, code, etc
    template_path = Column(String(500), nullable=True)  # Path to output template (if applicable)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


class ProjectAgentAssignment(Base):
    """Links projects to their selected agents."""
    __tablename__ = "project_agent_assignments"

    assignment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    agent_id = Column(String(100), ForeignKey("agents.agent_id", ondelete="CASCADE"), nullable=False)
    role_in_project = Column(String(100), nullable=True)  # e.g., "lead", "contributor", "reviewer"
    is_active = Column(Boolean, nullable=False, default=True)
    assigned_at = Column(TIMESTAMP, server_default=func.now())


# ===== PHASE 2: ADVANCED ANALYTICS & LEARNING MODELS =====

class TaskTemplate(Base):
    """Reusable task templates for PM Agent."""
    __tablename__ = "task_templates"

    template_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    project_type = Column(String(100), nullable=False)  # software_mvp, marketing_campaign, etc
    breakdown_instructions = Column(Text, nullable=False)  # How to break down tasks
    estimated_duration_hours = Column(Integer, nullable=True)
    typical_subtasks = Column(JSONB, nullable=False, default=[])  # List of typical subtasks
    required_skills = Column(JSONB, nullable=False, default=[])  # Required capabilities
    created_by = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now())


class AgentPerformanceMetric(Base):
    """Track agent performance metrics for learning system."""
    __tablename__ = "agent_performance_metrics"

    metric_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), ForeignKey("agents.agent_id", ondelete="CASCADE"), nullable=False)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.task_id", ondelete="CASCADE"), nullable=True)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=True)

    # Performance scores
    quality_score = Column(Integer, nullable=False, default=0)  # 0-100
    speed_score = Column(Integer, nullable=False, default=0)    # 0-100 (estimation accuracy)
    reliability_score = Column(Integer, nullable=False, default=0)  # 0-100 (task completion rate)
    overall_score = Column(Integer, nullable=False, default=0)  # 0-100

    # Performance details
    actual_duration_hours = Column(Integer, nullable=True)
    estimated_duration_hours = Column(Integer, nullable=True)
    success = Column(Boolean, nullable=False, default=True)
    feedback = Column(Text, nullable=True)

    recorded_at = Column(TIMESTAMP, server_default=func.now())


class AgentSkillProgression(Base):
    """Track how agent skills improve over time."""
    __tablename__ = "agent_skill_progression"

    progression_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), ForeignKey("agents.agent_id", ondelete="CASCADE"), nullable=False)
    skill_name = Column(String(100), nullable=False)
    proficiency_level = Column(Integer, nullable=False, default=1)  # 1-10 scale
    tasks_completed = Column(Integer, nullable=False, default=0)
    average_score = Column(Integer, nullable=False, default=0)  # 0-100
    last_used = Column(TIMESTAMP, nullable=True)
    updated_at = Column(TIMESTAMP, server_default=func.now())


class ProjectMetric(Base):
    """Analytics metrics for projects."""
    __tablename__ = "project_metrics"

    metric_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)

    # Timeline metrics
    planned_completion_date = Column(TIMESTAMP, nullable=True)
    actual_completion_date = Column(TIMESTAMP, nullable=True)
    timeline_variance_percent = Column(Integer, nullable=True)  # % over/under estimate

    # Task metrics
    total_tasks = Column(Integer, nullable=False, default=0)
    completed_tasks = Column(Integer, nullable=False, default=0)
    blocked_tasks = Column(Integer, nullable=False, default=0)
    failed_tasks = Column(Integer, nullable=False, default=0)
    completion_rate = Column(Integer, nullable=False, default=0)  # 0-100%

    # Quality metrics
    quality_score = Column(Integer, nullable=False, default=0)  # 0-100
    rework_count = Column(Integer, nullable=False, default=0)
    approval_rate = Column(Integer, nullable=False, default=100)  # 0-100%

    # Resource metrics
    total_agent_hours = Column(Integer, nullable=False, default=0)
    average_team_utilization = Column(Integer, nullable=False, default=0)  # 0-100%

    last_updated = Column(TIMESTAMP, server_default=func.now())


class AuditLog(Base):
    """Comprehensive audit trail for compliance and tracking."""
    __tablename__ = "audit_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    entity_type = Column(String(100), nullable=False)  # project, task, agent, etc
    entity_id = Column(String(200), nullable=False)
    action = Column(String(100), nullable=False)  # create, update, delete, approve, reject
    actor = Column(String(100), nullable=False)  # agent_id or system
    old_value = Column(JSONB, nullable=True)
    new_value = Column(JSONB, nullable=True)
    reason = Column(Text, nullable=True)
    details = Column(JSONB, nullable=True)
    timestamp = Column(TIMESTAMP, server_default=func.now())
    ip_address = Column(String(50), nullable=True)


class WorkflowInstance(Base):
    """Instance of a workflow/task breakdown."""
    __tablename__ = "workflow_instances"

    workflow_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    template_id = Column(UUID(as_uuid=True), ForeignKey("task_templates.template_id"), nullable=True)
    name = Column(String(200), nullable=False)
    status = Column(String(50), nullable=False, default="active")  # active, completed, cancelled
    parent_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.task_id", ondelete="SET NULL"), nullable=True)
    subtasks = Column(JSONB, nullable=False, default=[])  # List of subtask IDs
    created_by = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    completed_at = Column(TIMESTAMP, nullable=True)
