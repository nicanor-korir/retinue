"""SQLAlchemy models for export and deployment functionality."""
from sqlalchemy import Column, String, Text, Integer, Boolean, TIMESTAMP, ForeignKey, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from datetime import datetime
import uuid
import enum

from app.db.database import Base


# Enums for Export Functionality
class ExportFormat(str, enum.Enum):
    """Supported export formats."""
    PDF = "pdf"
    MARKDOWN = "markdown"
    ZIP = "zip"


class ExportType(str, enum.Enum):
    """Types of exports available."""
    PROJECT_SUMMARY = "project_summary"
    FULL_DOCUMENTATION = "full_documentation"
    TASK_REPORT = "task_report"
    AGENT_ACTIVITY_REPORT = "agent_activity_report"
    CODE_DOCUMENTATION = "code_documentation"
    ANALYTICS_METRICS = "analytics_metrics"
    CUSTOM = "custom"
    PROJECT_FILES_ZIP = "project_files_zip"  # Phase 2: ZIP Export


class ExportStatus(str, enum.Enum):
    """Status of export job."""
    PENDING = "pending"
    GATHERING_DATA = "gathering_data"
    RENDERING = "rendering"
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExportJob(Base):
    """Track export job status and metadata."""
    __tablename__ = "export_jobs"

    job_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    export_format = Column(SQLEnum(ExportFormat), nullable=False)
    export_type = Column(SQLEnum(ExportType), nullable=False)
    status = Column(SQLEnum(ExportStatus), default=ExportStatus.PENDING, nullable=False)

    # Configuration options
    options = Column(JSONB, default={}, nullable=False)  # Custom selections, styling, filters

    # File information
    file_path = Column(String(500), nullable=True)  # Path to generated file
    file_name = Column(String(255), nullable=True)  # Generated file name
    file_size_bytes = Column(Integer, nullable=True)  # Size in bytes
    download_url = Column(String(500), nullable=True)  # Signed download URL

    # Progress tracking
    progress_percentage = Column(Integer, default=0)
    current_step = Column(String(100), nullable=True)  # Current processing step
    estimated_completion_seconds = Column(Integer, nullable=True)

    # Timing
    created_at = Column(TIMESTAMP, server_default=func.now())
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)

    # Error handling
    error_message = Column(Text, nullable=True)
    error_details = Column(JSONB, nullable=True)  # Stack trace, etc.

    # Tracking
    created_by_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)
    data_hash = Column(String(64), nullable=True)  # SHA256 hash for caching
    is_cached = Column(Boolean, default=False)
    cache_expires_at = Column(TIMESTAMP, nullable=True)

    # Metadata
    meta_data = Column(JSONB, default={})


class ExportTemplate(Base):
    """Store export template configurations for reusability."""
    __tablename__ = "export_templates"

    template_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    export_type = Column(SQLEnum(ExportType), nullable=False)
    export_format = Column(SQLEnum(ExportFormat), nullable=False)

    # Template configuration
    options = Column(JSONB, nullable=False)  # Default options for this template
    styling = Column(JSONB, nullable=False)  # PDF styling, colors, fonts
    sections = Column(JSONB, nullable=False)  # Which sections to include

    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    is_default = Column(Boolean, default=False)
    usage_count = Column(Integer, default=0)
    created_by_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)
    meta_data = Column(JSONB, default={})


class ExportCache(Base):
    """Cache generated exports for performance."""
    __tablename__ = "export_cache"

    cache_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    data_hash = Column(String(64), unique=True, nullable=False)  # SHA256 of content
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)
    export_format = Column(SQLEnum(ExportFormat), nullable=False)
    export_type = Column(SQLEnum(ExportType), nullable=False)

    # Cached file information
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)

    # Cache lifecycle
    created_at = Column(TIMESTAMP, server_default=func.now())
    expires_at = Column(TIMESTAMP, nullable=False)  # Auto-delete after this time
    hit_count = Column(Integer, default=0)  # Track cache effectiveness

    # Original job reference
    original_job_id = Column(UUID(as_uuid=True), ForeignKey("export_jobs.job_id"), nullable=True)


# Enums for Deployment Functionality
class DeploymentStatus(str, enum.Enum):
    """Status of deployment."""
    PENDING = "pending"
    UPLOADING = "uploading"
    BUILDING = "building"
    DEPLOYING = "deploying"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeploymentEnvironment(str, enum.Enum):
    """Deployment environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Deployment(Base):
    """Track project deployments to various platforms."""
    __tablename__ = "deployments"

    deployment_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE"), nullable=False)

    # Platform information
    platform = Column(String(50), nullable=False)  # 'vercel', 'streamlit', 'netlify', etc.
    status = Column(SQLEnum(DeploymentStatus), default=DeploymentStatus.PENDING, nullable=False)
    environment = Column(SQLEnum(DeploymentEnvironment), default=DeploymentEnvironment.PRODUCTION)

    # Deployment details
    deployment_url = Column(String(500), nullable=True)
    build_time_seconds = Column(Integer, nullable=True)
    build_logs = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)

    # Configuration
    config = Column(JSONB, nullable=False)  # Build settings, env vars, etc.

    # Git/Version tracking
    git_commit_sha = Column(String(40), nullable=True)
    git_branch = Column(String(255), nullable=True)

    # Timing
    created_at = Column(TIMESTAMP, server_default=func.now())
    started_at = Column(TIMESTAMP, nullable=True)
    completed_at = Column(TIMESTAMP, nullable=True)

    # Tracking
    deployed_by_agent_id = Column(String(100), ForeignKey("agents.agent_id"), nullable=True)

    # For rollback capability
    previous_deployment_id = Column(UUID(as_uuid=True), ForeignKey("deployments.deployment_id"), nullable=True)
    is_rollback = Column(Boolean, default=False)

    meta_data = Column(JSONB, default={})


class PlatformConnection(Base):
    """Store OAuth connections to deployment platforms."""
    __tablename__ = "platform_connections"

    connection_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    agent_id = Column(String(100), ForeignKey("agents.agent_id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), nullable=False)  # 'vercel', 'streamlit', etc.

    # OAuth tokens (encrypted in database)
    access_token = Column(Text, nullable=False)  # Should be encrypted
    refresh_token = Column(Text, nullable=True)  # Should be encrypted
    token_expires_at = Column(TIMESTAMP, nullable=True)

    # Platform account information
    platform_user_id = Column(String(255), nullable=False)
    platform_username = Column(String(255), nullable=True)
    platform_email = Column(String(255), nullable=True)

    # Connection lifecycle
    connected_at = Column(TIMESTAMP, server_default=func.now())
    last_used_at = Column(TIMESTAMP, nullable=True)
    is_active = Column(Boolean, default=True)

    # Additional data
    scope = Column(JSONB, default=[])  # Requested permissions
    meta_data = Column(JSONB, default={})


class DeploymentLog(Base):
    """Store detailed deployment logs for debugging."""
    __tablename__ = "deployment_logs"

    log_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    deployment_id = Column(UUID(as_uuid=True), ForeignKey("deployments.deployment_id", ondelete="CASCADE"), nullable=False)

    log_level = Column(String(20), nullable=False)  # 'info', 'warning', 'error'
    message = Column(Text, nullable=False)
    timestamp = Column(TIMESTAMP, server_default=func.now())

    # Additional context
    context = Column(JSONB, nullable=True)


class ZIPExportOptions(Base):
    """Configuration and options for ZIP export (Phase 2)."""
    __tablename__ = "zip_export_options"

    option_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    job_id = Column(UUID(as_uuid=True), ForeignKey("export_jobs.job_id", ondelete="CASCADE"), nullable=False)

    # File inclusion options
    include_source_code = Column(Boolean, default=True)
    include_tests = Column(Boolean, default=True)
    include_documentation = Column(Boolean, default=True)
    include_assets = Column(Boolean, default=True)
    include_database_schema = Column(Boolean, default=True)
    include_docker_config = Column(Boolean, default=False)
    include_ci_cd_config = Column(Boolean, default=False)
    include_retinue_metadata = Column(Boolean, default=True)
    include_env_example = Column(Boolean, default=True)

    # Processing options
    format_code = Column(Boolean, default=False)  # Run prettier/black
    fix_linting_issues = Column(Boolean, default=False)  # Run linters
    documentation_level = Column(String(50), default="standard")  # minimal, standard, comprehensive
    generate_setup_script = Column(Boolean, default=True)

    # Archive options
    compression_level = Column(Integer, default=6)  # 0-9, where 9 is max compression
    file_size_estimate_bytes = Column(Integer, nullable=True)

    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    meta_data = Column(JSONB, default={})
