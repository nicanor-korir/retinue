"""Centralized Pydantic models for API requests and responses.

This module contains all data models used in API endpoints for validation
and serialization. Organized by resource type.
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Generic, TypeVar
from datetime import datetime
from enum import Enum

T = TypeVar("T")


# ===== Generic Response Models =====

class BaseResponse(BaseModel, Generic[T]):
    """Generic response wrapper for all API responses."""
    success: bool
    message: Optional[str] = None
    data: Optional[T] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Operation successful",
                "data": {}
            }
        }


# ===== Enums =====

class AgentStatusEnum(str, Enum):
    """Agent availability status."""
    AVAILABLE = "available"
    BUSY = "busy"
    IDLE = "idle"
    OFFLINE = "offline"


class TaskStatusEnum(str, Enum):
    """Task status values."""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    REVIEW = "review"
    CANCELLED = "cancelled"


class ProjectStatusEnum(str, Enum):
    """Project status values."""
    PLANNING = "planning"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"
    FAILED = "failed"
    REVIEW = "review"
    CANCELLED = "cancelled"


class PriorityEnum(str, Enum):
    """Priority levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


# ===== Agent Models =====

class AgentCapabilityInfo(BaseModel):
    """Agent capability information."""
    specialization: str
    proficiency: float = Field(default=0.8, description="0.0-1.0 proficiency level")
    category: str = Field(default="general", description="Capability category")

    class Config:
        json_schema_extra = {
            "example": {
                "specialization": "python",
                "proficiency": 0.95,
                "category": "programming_language"
            }
        }


class AgentInfoResponse(BaseModel):
    """Basic agent information."""
    agent_id: str
    name: str
    role: str
    department: str  # Legacy field - primary department
    departments: Optional[List[str]] = Field(default_factory=list, description="All departments this agent belongs to")
    is_active: bool = True
    description: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "cmo_001",
                "name": "Chief Marketing Officer",
                "role": "Marketing Director",
                "department": "marketing",
                "departments": ["marketing", "operations", "executive"],
                "is_active": True,
                "description": "Leads marketing strategy and campaigns"
            }
        }


class AgentDetailedResponse(AgentInfoResponse):
    """Detailed agent information with capabilities."""
    output_types: List[str] = Field(default_factory=list)
    specializations: List[str] = Field(default_factory=list)
    required_for_types: List[str] = Field(default_factory=list)
    always_active: bool = False
    cost_per_hour: float = Field(default=0.0, description="Cost per hour")
    capabilities: List[AgentCapabilityInfo] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "cto_001",
                "name": "Chief Technology Officer",
                "role": "CTO",
                "department": "engineering",
                "departments": ["engineering", "executive", "research"],
                "is_active": True,
                "output_types": ["code", "documentation", "decision"],
                "specializations": ["strategic_planning", "technical", "leadership"],
                "required_for_types": ["software_mvp", "api_development"],
                "always_active": False,
                "cost_per_hour": 0.0,
                "capabilities": [
                    {
                        "specialization": "python",
                        "proficiency": 0.98,
                        "category": "programming_language"
                    }
                ]
            }
        }


class AgentStatusResponse(BaseModel):
    """Agent runtime status."""
    agent_id: str
    name: str
    status: AgentStatusEnum
    last_active: Optional[datetime] = None
    current_task_id: Optional[str] = None
    health_status: str = Field(default="healthy")
    active_projects: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "ceo_001",
                "name": "Chief Executive Officer",
                "status": "available",
                "last_active": "2025-11-22T10:30:00Z",
                "current_task_id": "task-123",
                "health_status": "healthy",
                "active_projects": 3
            }
        }


# ===== Department Models =====

class DepartmentResponse(BaseModel):
    """Department information."""
    department_id: str
    name: str
    description: str
    icon: str
    color: str
    is_active: bool = True
    agent_count: int = 0

    class Config:
        json_schema_extra = {
            "example": {
                "department_id": "marketing",
                "name": "Marketing & Growth",
                "description": "Marketing campaigns and growth strategies",
                "icon": "megaphone",
                "color": "#DC2626",
                "is_active": True,
                "agent_count": 3
            }
        }


# ===== Deliverable Type Models =====

class DeliverableTypeResponse(BaseModel):
    """Deliverable type information."""
    type_id: str
    name: str
    description: str
    output_format: str
    typical_agents: List[str]
    is_active: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "type_id": "marketing_campaign",
                "name": "Marketing Campaign",
                "description": "Complete marketing campaign with assets",
                "output_format": "pdf",
                "typical_agents": ["ceo_001", "cmo_001", "designer_001"],
                "is_active": True
            }
        }


# ===== Team Validation Models =====

class TeamValidationRequest(BaseModel):
    """Request to validate team composition."""
    agent_ids: List[str]
    deliverable_type: Optional[str] = None
    project_type: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "agent_ids": ["ceo_001", "cto_001", "backend_001", "frontend_001"],
                "deliverable_type": "software_mvp",
                "project_type": "software_mvp"
            }
        }


class TeamValidationIssue(BaseModel):
    """A validation issue with team composition."""
    severity: str = Field(default="warning", description="error, warning, or info")
    code: str
    message: str
    affected_agents: List[str] = Field(default_factory=list)

    class Config:
        json_schema_extra = {
            "example": {
                "severity": "error",
                "code": "MISSING_REQUIRED_ROLE",
                "message": "Missing CEO agent in software_mvp projects",
                "affected_agents": []
            }
        }


class TeamValidationResponse(BaseModel):
    """Team validation result."""
    is_valid: bool
    issues: List[TeamValidationIssue] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    team_size: int
    required_roles_present: List[str] = Field(default_factory=list)
    optional_roles_present: List[str] = Field(default_factory=list)
    estimated_completion_time_hours: Optional[float] = None
    estimated_cost: Optional[float] = None

    class Config:
        json_schema_extra = {
            "example": {
                "is_valid": True,
                "issues": [],
                "warnings": ["No designer in team; output may lack visual assets"],
                "team_size": 4,
                "required_roles_present": ["ceo", "cto"],
                "optional_roles_present": ["backend", "frontend"],
                "estimated_completion_time_hours": 40.0,
                "estimated_cost": 6000.0
            }
        }


# ===== Project Models =====

class ProjectCreate(BaseModel):
    """Request model for creating a new project."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=10)
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM)
    project_type: str = Field(default="custom", description="Type of project")
    deliverable_type: Optional[str] = Field(
        default=None,
        description="Deliverable type (validates team)"
    )
    selected_agents: Optional[List[str]] = Field(
        default=None,
        description="Agent IDs to assign to project"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Q1 Marketing Campaign",
                "description": "Comprehensive Q1 marketing campaign with content, design, and social media strategy",
                "priority": "high",
                "project_type": "marketing_campaign",
                "deliverable_type": "marketing_campaign",
                "selected_agents": ["ceo_001", "cmo_001", "designer_001", "content_001"]
            }
        }


class ProjectResponse(BaseModel):
    """Response model for project information."""
    project_id: str
    name: str
    description: str
    status: ProjectStatusEnum
    priority: PriorityEnum
    project_type: str
    deliverable_type: Optional[str]
    selected_agents: List[str]
    owner_agent_id: str
    created_at: datetime
    updated_at: datetime
    version: int
    task_count: int = 0
    completed_tasks: int = 0
    progress_percentage: float = 0.0

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "proj-123",
                "name": "Q1 Marketing Campaign",
                "description": "Comprehensive Q1 marketing campaign",
                "status": "in_progress",
                "priority": "high",
                "project_type": "marketing_campaign",
                "deliverable_type": "marketing_campaign",
                "selected_agents": ["ceo_001", "cmo_001", "designer_001"],
                "owner_agent_id": "ceo_001",
                "created_at": "2025-11-22T10:00:00Z",
                "updated_at": "2025-11-22T10:30:00Z",
                "version": 1,
                "task_count": 5,
                "completed_tasks": 2,
                "progress_percentage": 40.0
            }
        }


class ProjectDetailedResponse(ProjectResponse):
    """Detailed project response with team information."""
    team_members: List[AgentInfoResponse] = Field(default_factory=list)
    team_validation: Optional[TeamValidationResponse] = None

    class Config:
        json_schema_extra = {
            "example": {
                "project_id": "proj-123",
                "name": "Q1 Marketing Campaign",
                "selected_agents": ["ceo_001", "cmo_001"],
                "team_members": [
                    {
                        "agent_id": "ceo_001",
                        "name": "Chief Executive Officer",
                        "role": "Executive",
                        "department": "executive",
                        "is_active": True
                    }
                ],
                "team_validation": {
                    "is_valid": True,
                    "issues": [],
                    "team_size": 2
                }
            }
        }


class ProjectUpdateTeam(BaseModel):
    """Request to update project team."""
    selected_agents: List[str] = Field(..., min_items=1)
    reason: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "selected_agents": ["ceo_001", "cmo_001", "designer_001"],
                "reason": "Adding designer for better visual output"
            }
        }


# ===== Task Models =====

class TaskCreate(BaseModel):
    """Request model for creating a task."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    assigned_to_agent_id: Optional[str] = None
    priority: PriorityEnum = Field(default=PriorityEnum.MEDIUM)
    required_skills: Optional[List[str]] = None
    required_output_type: Optional[str] = None
    output_format: Optional[str] = Field(default="text")
    output_metadata: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "title": "Create marketing strategy",
                "description": "Develop comprehensive Q1 marketing strategy",
                "priority": "high",
                "required_skills": ["marketing_strategy", "content_planning"],
                "required_output_type": "document",
                "output_format": "pdf"
            }
        }


class TaskResponse(BaseModel):
    """Response model for task information."""
    task_id: str
    project_id: str
    title: str
    description: Optional[str]
    status: TaskStatusEnum
    priority: PriorityEnum
    assigned_to_agent_id: Optional[str]
    assigned_agent_name: Optional[str]
    created_at: datetime
    updated_at: datetime
    output_format: Optional[str]
    required_skills: List[str] = Field(default_factory=list)
    skill_match_score: Optional[float] = None
    assigned_agent_capabilities: Optional[Dict[str, Any]] = None

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task-456",
                "project_id": "proj-123",
                "title": "Create marketing strategy",
                "status": "in_progress",
                "priority": "high",
                "assigned_to_agent_id": "cmo_001",
                "assigned_agent_name": "Chief Marketing Officer",
                "output_format": "pdf",
                "required_skills": ["marketing_strategy"],
                "skill_match_score": 0.95,
                "assigned_agent_capabilities": {
                    "marketing_strategy": 0.95,
                    "content_planning": 0.90
                }
            }
        }


class TaskAssignmentSuggestion(BaseModel):
    """Suggestion for task assignment."""
    agent_id: str
    agent_name: str
    match_score: float = Field(..., ge=0.0, le=1.0)
    matching_skills: List[str]
    missing_skills: List[str]
    reason: str

    class Config:
        json_schema_extra = {
            "example": {
                "agent_id": "cmo_001",
                "agent_name": "Chief Marketing Officer",
                "match_score": 0.95,
                "matching_skills": ["marketing_strategy", "content_planning"],
                "missing_skills": [],
                "reason": "Excellent match - expert in both required skills"
            }
        }


class TaskCapableAgentsResponse(BaseModel):
    """List of agents capable of performing a task."""
    task_id: str
    task_title: str
    required_skills: List[str]
    capable_agents: List[TaskAssignmentSuggestion]
    total_capable: int

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task-456",
                "task_title": "Create marketing strategy",
                "required_skills": ["marketing_strategy", "content_planning"],
                "capable_agents": [
                    {
                        "agent_id": "cmo_001",
                        "agent_name": "Chief Marketing Officer",
                        "match_score": 0.95,
                        "matching_skills": ["marketing_strategy", "content_planning"],
                        "missing_skills": []
                    }
                ],
                "total_capable": 1
            }
        }


# ===== Output Models =====

class OutputFormatInfo(BaseModel):
    """Information about a supported output format."""
    format_id: str
    name: str
    description: str
    mime_type: str
    file_extension: str
    is_active: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "format_id": "pdf",
                "name": "PDF Document",
                "description": "Portable Document Format",
                "mime_type": "application/pdf",
                "file_extension": ".pdf",
                "is_active": True
            }
        }


class TaskOutputResponse(BaseModel):
    """Task output information."""
    task_id: str
    output_format: str
    output_url: Optional[str] = None
    output_content: Optional[str] = None
    output_metadata: Optional[Dict[str, Any]] = None
    created_at: datetime
    file_size_bytes: Optional[int] = None

    class Config:
        json_schema_extra = {
            "example": {
                "task_id": "task-456",
                "output_format": "pdf",
                "output_url": "/api/v1/tasks/task-456/output/download",
                "output_metadata": {
                    "document_type": "marketing_strategy",
                    "pages": 10
                },
                "created_at": "2025-11-22T12:00:00Z",
                "file_size_bytes": 245000
            }
        }


# ===== Pagination =====

class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: str = Field(default="desc", description="asc or desc")

    class Config:
        json_schema_extra = {
            "example": {
                "page": 1,
                "page_size": 20,
                "sort_by": "created_at",
                "sort_order": "desc"
            }
        }


class PaginatedResponse(BaseModel):
    """Generic paginated response."""
    items: List[Dict[str, Any]]
    total: int
    page: int
    page_size: int
    total_pages: int

    class Config:
        json_schema_extra = {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        }


# ===== Standard Response Envelopes =====

class StandardResponse(BaseModel):
    """Standard API response envelope."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "data": {"agent_id": "cmo_001"},
                "metadata": {
                    "timestamp": "2025-11-22T10:30:00Z",
                    "request_id": "req-123"
                }
            }
        }


class ListResponse(BaseModel):
    """Standard list response with pagination."""
    success: bool
    data: List[Dict[str, Any]]
    pagination: Optional[PaginatedResponse] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

