"""Export schemas - Simple, clean data models for the export API."""
from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class ExportFormat(str, Enum):
    """Supported export formats."""
    PDF = "pdf"
    MARKDOWN = "markdown"
    ZIP = "zip"


class ExportRequest(BaseModel):
    """
    Unified export request.

    Keep it simple - users just pick a format and optionally what to include.
    We auto-detect the best content based on project type.
    """
    format: ExportFormat = Field(description="Export format: pdf, markdown, or zip")

    # Simple boolean flags - that's it
    include_tasks: bool = Field(default=True, description="Include task details")
    include_content: bool = Field(default=True, description="Include generated content/files")
    include_conversations: bool = Field(default=False, description="Include agent conversations")
    include_metrics: bool = Field(default=False, description="Include analytics and metrics")

    class Config:
        use_enum_values = True


class ExportStatus(str, Enum):
    """Export job status."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class ExportJobResponse(BaseModel):
    """Response for export job status."""
    job_id: str
    status: ExportStatus
    progress: int = Field(ge=0, le=100, description="Progress percentage")
    message: Optional[str] = Field(default=None, description="Current step or error message")
    download_url: Optional[str] = Field(default=None, description="URL to download when complete")
    file_name: Optional[str] = Field(default=None, description="Name of the exported file")
    file_size: Optional[int] = Field(default=None, description="File size in bytes")

    class Config:
        use_enum_values = True


class ProjectExportInfo(BaseModel):
    """
    Info about what can be exported from a project.

    Returned when user opens export dialog so we can show relevant options.
    """
    project_id: str
    project_name: str
    project_type: str  # "software", "content", "marketing", "legal", "general"

    # What content exists
    has_tasks: bool
    has_content: bool  # Files, documents, code
    has_conversations: bool
    has_metrics: bool

    # Counts for display
    task_count: int
    content_count: int
    message_count: int

    # Recommended format based on project type
    recommended_format: ExportFormat

    class Config:
        use_enum_values = True
