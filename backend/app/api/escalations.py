"""
API routes for Escalation Management System.

Provides RESTful endpoints for creating, updating, resolving, and querying escalations.
"""
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.database import get_session
from app.db.escalation_models import (
    EscalationType,
    EscalationPriority,
    EscalationStatus,
    EscalationLevel,
    ResolutionType,
    ImpactLevel,
    UrgencyLevel,
)
from app.services.escalation_service import EscalationService

router = APIRouter(prefix="/escalations", tags=["Escalations"])


# ==================== REQUEST/RESPONSE SCHEMAS ====================

class CreateEscalationRequest(BaseModel):
    """Request model for creating a new escalation."""
    title: str = Field(..., min_length=1, max_length=255)
    description: str = Field(..., min_length=1)
    escalation_type: EscalationType
    priority: EscalationPriority
    impact: ImpactLevel
    urgency: UrgencyLevel
    created_by_type: str = Field(..., pattern="^(agent|user)$")
    created_by_id: str
    related_task_id: Optional[UUID] = None
    related_project_id: Optional[UUID] = None
    related_agent_id: Optional[str] = None
    conflict_parties: Optional[List[dict]] = None
    department: Optional[str] = None
    tags: Optional[List[str]] = None
    due_date: Optional[datetime] = None


class UpdateEscalationRequest(BaseModel):
    """Request model for updating an escalation."""
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[EscalationPriority] = None
    status: Optional[EscalationStatus] = None
    department: Optional[str] = None
    tags: Optional[List[str]] = None
    due_date: Optional[datetime] = None


class ResolveEscalationRequest(BaseModel):
    """Request model for resolving an escalation."""
    resolution_type: ResolutionType
    resolution_notes: str = Field(..., min_length=1)
    resolved_by_type: str = Field(..., pattern="^(agent|user)$")
    resolved_by_id: str


class EscalateRequest(BaseModel):
    """Request model for escalating to next level."""
    actor_type: str = Field(..., pattern="^(agent|user)$")
    actor_id: str
    reason: str = Field(..., min_length=1)


class ReassignRequest(BaseModel):
    """Request model for reassigning an escalation."""
    new_assigned_to_type: str = Field(..., pattern="^(agent|user)$")
    new_assigned_to_id: str
    actor_type: str = Field(..., pattern="^(agent|user)$")
    actor_id: str
    reason: Optional[str] = None


class AddCommentRequest(BaseModel):
    """Request model for adding a comment."""
    author_type: str = Field(..., pattern="^(agent|user)$")
    author_id: str
    content: str = Field(..., min_length=1)
    is_internal: bool = False
    parent_comment_id: Optional[UUID] = None
    mentions: Optional[List[str]] = None


class EscalationResponse(BaseModel):
    """Response model for escalation details."""
    id: UUID
    escalation_number: str
    title: str
    description: str
    escalation_type: str
    priority: str
    status: str
    level: str
    created_by_type: str
    created_by_id: str
    assigned_to_type: Optional[str]
    assigned_to_id: Optional[str]
    assigned_at: Optional[datetime]
    escalation_path: List[dict]
    related_task_id: Optional[UUID]
    related_project_id: Optional[UUID]
    related_agent_id: Optional[str]
    conflict_parties: List[dict]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    closed_at: Optional[datetime]
    due_date: Optional[datetime]
    sla_deadline: datetime
    time_to_first_response: Optional[int]
    time_to_resolution: Optional[int]
    resolution_notes: Optional[str]
    resolution_type: Optional[str]
    auto_resolution_attempts: int
    resolved_by_type: Optional[str]
    resolved_by_id: Optional[str]
    impact_assessment: str
    urgency: str
    department: Optional[str]
    tags: List[str]
    meta_data: dict

    class Config:
        from_attributes = True


class EscalationListResponse(BaseModel):
    """Response model for list of escalations."""
    escalations: List[EscalationResponse]
    total: int
    page: int
    per_page: int


class TimelineEventResponse(BaseModel):
    """Response model for timeline events."""
    id: UUID
    escalation_id: UUID
    event_type: str
    actor_type: str
    actor_id: str
    timestamp: datetime
    description: str
    details: dict
    previous_state: Optional[dict]
    new_state: Optional[dict]

    class Config:
        from_attributes = True


class CommentResponse(BaseModel):
    """Response model for comments."""
    id: UUID
    escalation_id: UUID
    author_type: str
    author_id: str
    content: str
    created_at: datetime
    updated_at: datetime
    is_internal: bool
    parent_comment_id: Optional[UUID]
    attachments: List[dict]
    mentions: List[str]

    class Config:
        from_attributes = True


class StatsResponse(BaseModel):
    """Response model for escalation statistics."""
    total_escalations: int
    open_escalations: int
    resolved_today: int
    average_resolution_time_minutes: float
    sla_compliance_rate: float
    pending_human_decision: int
    by_type: dict
    by_priority: dict


# ==================== API ENDPOINTS ====================

@router.post("/", response_model=EscalationResponse, status_code=status.HTTP_201_CREATED)
async def create_escalation(
    request: CreateEscalationRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new escalation.
    
    - Automatically routes to appropriate handler based on type and priority
    - Calculates SLA deadline
    - Creates initial timeline event
    - Sends notifications to assigned handler
    """
    try:
        service = EscalationService(session)
        escalation = await service.create_escalation(
            title=request.title,
            description=request.description,
            escalation_type=request.escalation_type,
            priority=request.priority,
            impact=request.impact,
            urgency=request.urgency,
            created_by_type=request.created_by_type,
            created_by_id=request.created_by_id,
            related_task_id=request.related_task_id,
            related_project_id=request.related_project_id,
            related_agent_id=request.related_agent_id,
            conflict_parties=request.conflict_parties,
            department=request.department,
            tags=request.tags,
            due_date=request.due_date,
        )
        
        return EscalationResponse.from_orm(escalation)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create escalation: {str(e)}"
        )


@router.get("/", response_model=EscalationListResponse)
async def list_escalations(
    status_filter: Optional[List[EscalationStatus]] = Query(None, alias="status"),
    priority: Optional[List[EscalationPriority]] = Query(None),
    escalation_type: Optional[List[EscalationType]] = Query(None, alias="type"),
    level: Optional[List[EscalationLevel]] = Query(None),
    assigned_to_id: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    tags: Optional[List[str]] = Query(None),
    sla_at_risk: bool = Query(False),
    search: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    order_by: str = Query("created_at"),
    order_desc: bool = Query(True),
    session: AsyncSession = Depends(get_session)
):
    """
    List escalations with advanced filtering and pagination.
    
    Supports filtering by:
    - Status (multiple)
    - Priority (multiple)
    - Type (multiple)
    - Level (multiple)
    - Assigned user/agent
    - Department
    - Tags
    - SLA at risk (< 6 hours remaining)
    - Full-text search
    """
    try:
        service = EscalationService(session)
        skip = (page - 1) * per_page
        
        escalations, total = await service.list_escalations(
            status=status_filter,
            priority=priority,
            escalation_type=escalation_type,
            level=level,
            assigned_to_id=assigned_to_id,
            department=department,
            tags=tags,
            sla_at_risk=sla_at_risk,
            search=search,
            skip=skip,
            limit=per_page,
            order_by=order_by,
            order_desc=order_desc,
        )
        
        return EscalationListResponse(
            escalations=[EscalationResponse.from_orm(e) for e in escalations],
            total=total,
            page=page,
            per_page=per_page,
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list escalations: {str(e)}"
        )


@router.get("/{escalation_id}", response_model=EscalationResponse)
async def get_escalation(
    escalation_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """Get detailed information about a specific escalation."""
    try:
        service = EscalationService(session)
        escalation = await service.get_escalation(escalation_id)
        
        if not escalation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Escalation {escalation_id} not found"
            )
        
        return EscalationResponse.from_orm(escalation)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get escalation: {str(e)}"
        )


@router.patch("/{escalation_id}", response_model=EscalationResponse)
async def update_escalation(
    escalation_id: UUID,
    request: UpdateEscalationRequest,
    actor_type: str = Query(..., pattern="^(agent|user|system)$"),
    actor_id: str = Query(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Update escalation fields.
    
    - Tracks all changes in timeline
    - Updates timestamps
    - Sends notifications on significant changes
    """
    try:
        service = EscalationService(session)
        
        # Build updates dict from non-None fields
        updates = {}
        if request.title is not None:
            updates["title"] = request.title
        if request.description is not None:
            updates["description"] = request.description
        if request.priority is not None:
            updates["priority"] = request.priority
        if request.status is not None:
            updates["status"] = request.status
        if request.department is not None:
            updates["department"] = request.department
        if request.tags is not None:
            updates["tags"] = request.tags
        if request.due_date is not None:
            updates["due_date"] = request.due_date
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        escalation = await service.update_escalation(
            escalation_id=escalation_id,
            actor_type=actor_type,
            actor_id=actor_id,
            **updates
        )
        
        return EscalationResponse.from_orm(escalation)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update escalation: {str(e)}"
        )


@router.post("/{escalation_id}/resolve", response_model=EscalationResponse)
async def resolve_escalation(
    escalation_id: UUID,
    request: ResolveEscalationRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Resolve an escalation.
    
    - Marks as resolved with resolution details
    - Calculates time to resolution
    - Sends resolution notifications
    - Updates SLA compliance metrics
    """
    try:
        service = EscalationService(session)
        escalation = await service.resolve_escalation(
            escalation_id=escalation_id,
            resolution_type=request.resolution_type,
            resolution_notes=request.resolution_notes,
            resolved_by_type=request.resolved_by_type,
            resolved_by_id=request.resolved_by_id,
        )
        
        return EscalationResponse.from_orm(escalation)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve escalation: {str(e)}"
        )


@router.post("/{escalation_id}/escalate", response_model=EscalationResponse)
async def escalate_to_next_level(
    escalation_id: UUID,
    request: EscalateRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Escalate to the next hierarchical level.
    
    - Department → Executive → Human
    - Auto-assigns to appropriate handler for new level
    - Records escalation reason
    - Sends notifications to new handler
    """
    try:
        service = EscalationService(session)
        escalation = await service.escalate_to_next_level(
            escalation_id=escalation_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            reason=request.reason,
        )
        
        return EscalationResponse.from_orm(escalation)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to escalate: {str(e)}"
        )


@router.post("/{escalation_id}/reassign", response_model=EscalationResponse)
async def reassign_escalation(
    escalation_id: UUID,
    request: ReassignRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Reassign escalation to a different handler.
    
    - Can reassign to different agent or user
    - Records reason for reassignment
    - Sends notifications to new and old assignees
    """
    try:
        service = EscalationService(session)
        escalation = await service.reassign_escalation(
            escalation_id=escalation_id,
            new_assigned_to_type=request.new_assigned_to_type,
            new_assigned_to_id=request.new_assigned_to_id,
            actor_type=request.actor_type,
            actor_id=request.actor_id,
            reason=request.reason,
        )
        
        return EscalationResponse.from_orm(escalation)
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reassign escalation: {str(e)}"
        )


@router.get("/{escalation_id}/timeline", response_model=List[TimelineEventResponse])
async def get_escalation_timeline(
    escalation_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """
    Get complete timeline of events for an escalation.
    
    Returns all events in chronological order including:
    - Creation
    - Status changes
    - Assignments
    - Comments
    - Resolutions
    - Escalations
    """
    try:
        service = EscalationService(session)
        timeline = await service.get_escalation_timeline(escalation_id)
        
        return [TimelineEventResponse.from_orm(event) for event in timeline]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get timeline: {str(e)}"
        )


@router.get("/{escalation_id}/comments", response_model=List[CommentResponse])
async def get_escalation_comments(
    escalation_id: UUID,
    include_internal: bool = Query(True),
    session: AsyncSession = Depends(get_session)
):
    """
    Get all comments for an escalation.
    
    - Supports filtering internal vs external comments
    - Returns in chronological order
    - Includes threading information
    """
    try:
        service = EscalationService(session)
        comments = await service.get_escalation_comments(
            escalation_id=escalation_id,
            include_internal=include_internal
        )
        
        return [CommentResponse.from_orm(comment) for comment in comments]
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get comments: {str(e)}"
        )


@router.post("/{escalation_id}/comments", response_model=CommentResponse, status_code=status.HTTP_201_CREATED)
async def add_comment(
    escalation_id: UUID,
    request: AddCommentRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Add a comment to an escalation.
    
    - Supports threaded comments via parent_comment_id
    - Can @mention users/agents for notifications
    - Internal comments hidden from certain viewers
    """
    try:
        service = EscalationService(session)
        comment = await service.add_comment(
            escalation_id=escalation_id,
            author_type=request.author_type,
            author_id=request.author_id,
            content=request.content,
            is_internal=request.is_internal,
            parent_comment_id=request.parent_comment_id,
            mentions=request.mentions,
        )
        
        return CommentResponse.from_orm(comment)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add comment: {str(e)}"
        )


@router.get("/stats/dashboard", response_model=StatsResponse)
async def get_escalation_stats(
    department: Optional[str] = Query(None),
    agent_id: Optional[str] = Query(None),
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    session: AsyncSession = Depends(get_session)
):
    """
    Get escalation statistics for dashboard.
    
    Returns comprehensive metrics including:
    - Total and open escalation counts
    - Resolution times
    - SLA compliance rates
    - Breakdown by type and priority
    - Human intervention metrics
    
    Can be filtered by department, agent, or date range.
    """
    try:
        service = EscalationService(session)
        stats = await service.get_escalation_stats(
            department=department,
            agent_id=agent_id,
            start_date=start_date,
            end_date=end_date,
        )
        
        return StatsResponse(**stats)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get stats: {str(e)}"
        )


@router.delete("/{escalation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_escalation(
    escalation_id: UUID,
    actor_type: str = Query(..., pattern="^(agent|user|system)$"),
    actor_id: str = Query(...),
    session: AsyncSession = Depends(get_session)
):
    """
    Soft delete an escalation.
    
    - Sets deleted_at timestamp
    - Preserves data for audit purposes
    - Can be undeleted if needed
    """
    try:
        service = EscalationService(session)
        escalation = await service.get_escalation(escalation_id)
        
        if not escalation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Escalation {escalation_id} not found"
            )
        
        # Soft delete
        await service.update_escalation(
            escalation_id=escalation_id,
            actor_type=actor_type,
            actor_id=actor_id,
            deleted_at=datetime.utcnow()
        )
        
        return JSONResponse(
            status_code=status.HTTP_204_NO_CONTENT,
            content=None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete escalation: {str(e)}"
        )
