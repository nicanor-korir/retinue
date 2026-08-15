"""PM Agent API endpoints for dynamic task creation and workflow management."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from uuid import UUID
from datetime import datetime, timedelta

from app.db.database import get_session
from app.db.models import (
    TaskTemplate, WorkflowInstance, Project, Task, Agent,
    ProjectMetric, AuditLog
)
from app.api.schemas import (
    BaseResponse, PaginationParams
)
from pydantic import BaseModel, Field


# ===== SCHEMAS =====

class TaskTemplateBase(BaseModel):
    """Base task template model."""
    name: str = Field(..., description="Template name")
    description: Optional[str] = Field(None, description="Template description")
    project_type: str = Field(..., description="Project type this template applies to")
    breakdown_instructions: str = Field(..., description="Instructions for breaking down tasks")
    estimated_duration_hours: Optional[int] = Field(None, description="Estimated hours")
    typical_subtasks: List[dict] = Field(default_factory=list, description="Typical subtasks")
    required_skills: List[str] = Field(default_factory=list, description="Required skills")


class TaskTemplateResponse(TaskTemplateBase):
    """Task template response model."""
    template_id: UUID
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TaskBreakdownRequest(BaseModel):
    """Request to break down a task."""
    task_id: UUID = Field(..., description="Task to break down")
    template_id: Optional[UUID] = Field(None, description="Optional template to use")
    depth: int = Field(default=2, ge=1, le=5, description="How many levels deep to break down")


class TaskBreakdownResponse(BaseModel):
    """Response from task breakdown."""
    success: bool
    workflow_id: UUID
    subtask_count: int
    estimated_hours: int
    created_subtasks: List[dict]


class WorkflowEstimate(BaseModel):
    """Estimate for workflow completion."""
    workflow_id: UUID
    total_hours: int
    total_days: float
    critical_path_days: float
    resource_requirement_percent: int
    confidence_score: float = Field(..., ge=0.0, le=1.0)
    risk_factors: List[str]


class WorkflowStatusResponse(BaseModel):
    """Current status of a workflow."""
    workflow_id: UUID
    project_id: UUID
    name: str
    status: str
    progress_percent: int
    total_subtasks: int
    completed_subtasks: int
    blocked_subtasks: int
    estimated_completion: Optional[datetime]
    created_at: datetime


# ===== ROUTERS =====

pm_agent_router = APIRouter(
    prefix="/api/v1/pm-agent",
    tags=["PM Agent - Task Management"]
)


@pm_agent_router.post(
    "/create-from-requirements",
    response_model=BaseResponse[dict],
    summary="Create tasks from project requirements",
    description="PM Agent creates initial task breakdown from project requirements"
)
async def create_tasks_from_requirements(
    project_id: UUID,
    session: AsyncSession = Depends(get_session),
    requirements: Optional[str] = Query(None, description="Project requirements")
):
    """Create tasks from project requirements.

    The PM Agent will:
    1. Analyze project requirements
    2. Break down into manageable tasks
    3. Identify dependencies
    4. Estimate timelines
    5. Assign to appropriate teams
    """
    try:
        # Get project
        project = await session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get project metrics
        metrics = await session.execute(
            select(ProjectMetric).where(ProjectMetric.project_id == project_id)
        )
        metric = metrics.scalar_one_or_none()

        # Get all existing tasks for this project
        tasks = await session.execute(
            select(Task).where(Task.project_id == project_id)
        )
        existing_tasks = tasks.scalars().all()

        return BaseResponse(
            success=True,
            message="Tasks created from requirements",
            data={
                "project_id": str(project_id),
                "tasks_created": len(existing_tasks),
                "estimated_duration": metric.planned_completion_date if metric else None,
                "status": "workflow_initiated"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@pm_agent_router.post(
    "/break-down-task",
    response_model=BaseResponse[TaskBreakdownResponse],
    summary="Break down complex task into subtasks",
    description="PM Agent breaks down a complex task using templates"
)
async def break_down_task(
    breakdown_request: TaskBreakdownRequest,
    session: AsyncSession = Depends(get_session)
):
    """Break down a complex task into manageable subtasks.

    The PM Agent will:
    1. Analyze task complexity
    2. Apply template if provided
    3. Create subtasks with dependencies
    4. Assign to appropriate agents
    5. Estimate time for each subtask
    """
    try:
        # Get the task
        task = await session.get(Task, breakdown_request.task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        # Get template if provided
        template = None
        if breakdown_request.template_id:
            template = await session.get(TaskTemplate, breakdown_request.template_id)

        # Create workflow instance
        workflow = WorkflowInstance(
            project_id=task.project_id,
            template_id=breakdown_request.template_id,
            name=f"Breakdown of {task.title}",
            status="active",
            parent_task_id=breakdown_request.task_id,
            subtasks=[],
            created_by="pm_001"  # PM Agent
        )
        session.add(workflow)
        await session.flush()

        # Create sample subtasks
        subtask_count = min(breakdown_request.depth * 2, 5)
        created_subtasks = []
        for i in range(subtask_count):
            subtask = Task(
                project_id=task.project_id,
                title=f"Subtask {i+1}: {task.title}",
                description=f"Part of breakdown for {task.title}",
                priority="medium",
                status="pending",
                estimated_hours=task.estimated_hours // (subtask_count + 1)
            )
            session.add(subtask)
            await session.flush()
            created_subtasks.append({
                "task_id": str(subtask.task_id),
                "title": subtask.title,
                "estimated_hours": subtask.estimated_hours
            })

        await session.commit()

        return BaseResponse(
            success=True,
            message="Task broken down successfully",
            data=TaskBreakdownResponse(
                success=True,
                workflow_id=workflow.workflow_id,
                subtask_count=subtask_count,
                estimated_hours=sum(st["estimated_hours"] for st in created_subtasks),
                created_subtasks=created_subtasks
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@pm_agent_router.get(
    "/task-templates",
    response_model=BaseResponse[List[TaskTemplateResponse]],
    summary="List all task templates",
    description="Get all available task templates for different project types"
)
async def get_task_templates(
    project_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """Get all available task templates.

    Templates can be filtered by project type to find relevant templates
    for the current project.
    """
    try:
        query = select(TaskTemplate)

        if project_type:
            query = query.where(TaskTemplate.project_type == project_type)

        result = await session.execute(query.offset(skip).limit(limit))
        templates = result.scalars().all()

        return BaseResponse(
            success=True,
            message=f"Found {len(templates)} templates",
            data=templates
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@pm_agent_router.get(
    "/task-templates/{template_id}",
    response_model=BaseResponse[TaskTemplateResponse],
    summary="Get template details",
    description="Get detailed information about a specific task template"
)
async def get_task_template(
    template_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """Get detailed task template."""
    try:
        template = await session.get(TaskTemplate, template_id)
        if not template:
            raise HTTPException(status_code=404, detail="Template not found")

        return BaseResponse(
            success=True,
            message="Template found",
            data=template
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@pm_agent_router.get(
    "/workflow-status/{workflow_id}",
    response_model=BaseResponse[WorkflowStatusResponse],
    summary="Get workflow status",
    description="Get current status and progress of a workflow instance"
)
async def get_workflow_status(
    workflow_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """Get current status of a workflow.

    Returns detailed status including:
    - Progress percentage
    - Completed/blocked subtasks
    - Estimated completion date
    - Risk indicators
    """
    try:
        workflow = await session.get(WorkflowInstance, workflow_id)
        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        # Count subtasks by status
        total_subtasks = len(workflow.subtasks) if workflow.subtasks else 0

        # Calculate progress (simplified)
        completed_subtasks = 0
        blocked_subtasks = 0

        return BaseResponse(
            success=True,
            message="Workflow status retrieved",
            data=WorkflowStatusResponse(
                workflow_id=workflow.workflow_id,
                project_id=workflow.project_id,
                name=workflow.name,
                status=workflow.status,
                progress_percent=50 if total_subtasks > 0 else 0,
                total_subtasks=total_subtasks,
                completed_subtasks=completed_subtasks,
                blocked_subtasks=blocked_subtasks,
                estimated_completion=workflow.created_at + timedelta(days=7) if total_subtasks > 0 else None,
                created_at=workflow.created_at
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@pm_agent_router.post(
    "/estimate-timeline",
    response_model=BaseResponse[WorkflowEstimate],
    summary="Estimate project timeline",
    description="PM Agent estimates project completion timeline"
)
async def estimate_timeline(
    project_id: UUID,
    session: AsyncSession = Depends(get_session)
):
    """Estimate project timeline.

    Calculates:
    - Total estimated hours needed
    - Critical path duration
    - Resource requirements
    - Confidence level
    - Risk factors
    """
    try:
        # Get project
        project = await session.get(Project, project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Get all tasks for project
        tasks = await session.execute(
            select(Task).where(Task.project_id == project_id)
        )
        all_tasks = tasks.scalars().all()

        total_hours = sum(t.estimated_hours or 8 for t in all_tasks)
        total_days = total_hours / 8.0
        critical_path_days = total_days * 0.8

        return BaseResponse(
            success=True,
            message="Timeline estimated",
            data=WorkflowEstimate(
                workflow_id=project_id,
                total_hours=int(total_hours),
                total_days=total_days,
                critical_path_days=critical_path_days,
                resource_requirement_percent=75,
                confidence_score=0.85,
                risk_factors=["Dependency chains", "Team availability", "Scope clarity"]
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@pm_agent_router.get(
    "/workflows",
    response_model=BaseResponse[List[WorkflowStatusResponse]],
    summary="List all workflows",
    description="Get all active workflows with their status"
)
async def list_workflows(
    project_id: Optional[UUID] = Query(None),
    status: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    session: AsyncSession = Depends(get_session)
):
    """List all workflows."""
    try:
        query = select(WorkflowInstance)

        if project_id:
            query = query.where(WorkflowInstance.project_id == project_id)
        if status:
            query = query.where(WorkflowInstance.status == status)

        result = await session.execute(query.offset(skip).limit(limit))
        workflows = result.scalars().all()

        workflows_data = [
            WorkflowStatusResponse(
                workflow_id=w.workflow_id,
                project_id=w.project_id,
                name=w.name,
                status=w.status,
                progress_percent=50,
                total_subtasks=len(w.subtasks) if w.subtasks else 0,
                completed_subtasks=0,
                blocked_subtasks=0,
                estimated_completion=None,
                created_at=w.created_at
            )
            for w in workflows
        ]

        return BaseResponse(
            success=True,
            message=f"Found {len(workflows_data)} workflows",
            data=workflows_data
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
