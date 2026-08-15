"""API routes for the Deviant platform."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import List, Optional
from datetime import datetime
import uuid
import re
import logging

logger = logging.getLogger(__name__)

from app.db.database import get_session
from app.api.escalations import router as escalations_router
from app.api.exports import router as exports_router
from app.api.feedback import router as feedback_router
from app.api.cache import router as cache_router
from app.api.performance import router as performance_router
from app.api.websocket import router as websocket_router
from app.api.task_controls import router as task_controls_router
from app.api.project_learnings import router as project_learnings_router
from app.api.project_similarity import router as project_similarity_router
from app.api.cross_project_learning import router as cross_project_learning_router
from app.db.models import (
    Project,
    Task,
    Agent,
    AgentStatus,
    Message,
    Decision,
    Escalation,
    HumanInteraction,
    AuditLog,
    Notification,
    NotificationType,
    ProjectStatus,
    TaskStatus,
    Priority,
    Availability,
)
from pydantic import BaseModel


# Pydantic models for API requests/responses
class ProjectCreate(BaseModel):
    """Request model for creating a new project."""
    name: str
    description: str
    priority: str = "medium"
    selectedAgents: Optional[List[str]] = None


class TaskResponse(BaseModel):
    """Response model for task information."""
    task_id: str
    title: str
    status: str
    assigned_to: str
    created_at: str
    updated_at: str


class ProjectResponse(BaseModel):
    """Response model for project information."""
    project_id: str
    name: str
    description: str
    status: str
    priority: str
    version: int
    created_at: str
    updated_at: str
    tasks: List[TaskResponse]


class AgentStatusResponse(BaseModel):
    """Response model for agent status."""
    agent_id: str
    name: str
    role: str
    availability: str
    last_active: str
    current_task_id: Optional[str]
    health_status: str


class MessageResponse(BaseModel):
    """Response model for messages."""
    message_id: str
    from_agent_id: str
    to_agent_id: Optional[str]
    content: str
    message_type: str
    priority: str
    read_status: bool
    timestamp: str


class DashboardResponse(BaseModel):
    """Response model for dashboard data."""
    total_projects: int
    active_projects: int
    completed_projects: int
    total_tasks: int
    pending_tasks: int
    in_progress_tasks: int
    completed_tasks: int
    blocked_tasks: int
    total_agents: int
    active_agents: int
    recent_activity: dict
    recent_escalations: List[dict]


class HumanInputCreate(BaseModel):
    """Request model for human input on projects/tasks."""
    input_text: str
    context: Optional[str] = None
    related_project_id: Optional[str] = None
    related_task_id: Optional[str] = None


class HumanInteractionResponse(BaseModel):
    """Response model for human interaction requests."""
    interaction_id: str
    initiated_by_agent_id: str
    interaction_type: str
    request: str
    status: str
    created_at: str


# Create router
router = APIRouter()


# Helper function to check and update project status after task changes
async def _check_and_update_project_status(session: AsyncSession, project_id):
    """
    Check project status after task changes and update accordingly.
    Returns dict with status and message.
    """
    # Refresh session to ensure we get latest data
    await session.flush()
    
    # Get all tasks for this project
    result = await session.execute(
        select(Task).where(Task.project_id == project_id)
    )
    tasks = result.scalars().all()
    
    if not tasks:
        return {"status": "no_tasks", "message": "No tasks in project"}
    
    # Count task statuses
    total_tasks = len(tasks)
    completed = sum(1 for t in tasks if t.status == TaskStatus.COMPLETED)
    cancelled = sum(1 for t in tasks if t.status == TaskStatus.CANCELLED)
    pending = sum(1 for t in tasks if t.status == TaskStatus.PENDING)
    in_progress = sum(1 for t in tasks if t.status == TaskStatus.IN_PROGRESS)
    blocked = sum(1 for t in tasks if t.status == TaskStatus.BLOCKED)
    review = sum(1 for t in tasks if t.status == TaskStatus.REVIEW)
    failed = sum(1 for t in tasks if t.status == TaskStatus.FAILED)
    
    # Calculate active tasks (not completed or cancelled)
    active_tasks = pending + in_progress + blocked + review
    
    # Get current project
    project_result = await session.execute(
        select(Project).where(Project.project_id == project_id)
    )
    project = project_result.scalar_one_or_none()
    
    if not project:
        return {"status": "error", "message": "Project not found"}
    
    old_status = project.status
    new_status = None
    message = None
    
    # Determine new project status based on task distribution
    if completed == total_tasks:
        # All tasks completed
        new_status = ProjectStatus.COMPLETED
        message = f"All {total_tasks} tasks completed"
    elif cancelled == total_tasks:
        # All tasks cancelled
        new_status = ProjectStatus.CANCELLED
        message = f"All {total_tasks} tasks cancelled"
    elif active_tasks == 0:
        # No active tasks - only completed, cancelled, or failed
        if completed > 0 and completed >= cancelled:
            # Some completed, more or equal completed than cancelled
            new_status = ProjectStatus.COMPLETED
            message = f"Project completed: {completed} completed, {cancelled} cancelled"
        elif cancelled > completed:
            # More cancelled than completed
            new_status = ProjectStatus.CANCELLED
            message = f"Project cancelled: {cancelled} cancelled, {completed} completed"
        elif failed > 0:
            new_status = ProjectStatus.FAILED
            message = f"Project failed: {failed} failed tasks"
    elif review > 0 or blocked > 0:
        # Tasks in review or blocked
        new_status = ProjectStatus.REVIEW
        message = f"{review} in review, {blocked} blocked, {in_progress} in progress"
    elif in_progress > 0:
        # At least one task actively being worked on
        new_status = ProjectStatus.IN_PROGRESS
        message = f"{in_progress} tasks in progress, {pending} pending"
    elif pending > 0:
        # Only pending tasks remain
        new_status = ProjectStatus.PLANNING
        message = f"{pending} tasks pending"
    
    # Update project status if changed
    if new_status and new_status != old_status:
        await session.execute(
            update(Project)
            .where(Project.project_id == project_id)
            .values(status=new_status)
        )
        
        # Log the status change
        audit_log = AuditLog(
            actor="system",
            action="project_status_updated",
            entity_type="project",
            entity_id=str(project_id),
            old_value={"status": old_status.value},
            new_value={
                "status": new_status.value,
                "reason": message,
                "task_counts": {
                    "total": total_tasks,
                    "completed": completed,
                    "cancelled": cancelled,
                    "in_progress": in_progress,
                    "pending": pending,
                    "blocked": blocked,
                    "review": review,
                }
            }
        )
        session.add(audit_log)
        
        await session.commit()
        
        return {
            "status": new_status.value,
            "message": message,
            "old_status": old_status.value,
            "updated": True,
            "task_counts": {
                "total": total_tasks,
                "completed": completed,
                "cancelled": cancelled,
                "in_progress": in_progress,
                "pending": pending,
            }
        }
    
    return {
        "status": old_status.value,
        "message": "No status change needed",
        "updated": False,
        "task_counts": {
            "total": total_tasks,
            "completed": completed,
            "cancelled": cancelled,
            "in_progress": in_progress,
            "pending": pending,
        }
    }


# ===== Project Endpoints =====

@router.post("/projects", response_model=ProjectResponse, status_code=201, tags=["Projects"])
async def create_project(
    project: ProjectCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new project and assign it to a team of agents (or CEO by default).

    This is the main entry point for humans to submit project requests.
    Multiple agents can collaborate together on the project.
    """
    # Map frontend agent IDs to backend agent IDs
    agent_mapping = {
        "ceo": "ceo_001",
        "cto": "cto_001",
        "pm": "pm_001",
        "backend": "backend_001",
        "frontend": "frontend_001",
        "designer": "designer_001",
    }

    # Determine which agents to assign to (default to CEO)
    if project.selectedAgents and len(project.selectedAgents) > 0:
        assigned_agent_ids = [agent_mapping.get(agent_id, agent_id) for agent_id in project.selectedAgents]
    else:
        assigned_agent_ids = ["ceo_001"]

    # Validate that selected agents exist in the database
    # Query to check which agents exist
    from sqlalchemy import select
    result = await session.execute(
        select(Agent.agent_id).where(Agent.agent_id.in_(assigned_agent_ids))
    )
    existing_agents = {row[0] for row in result.fetchall()}

    # Filter to only existing agents, fallback to CEO if none exist
    valid_assigned_agents = [agent_id for agent_id in assigned_agent_ids if agent_id in existing_agents]

    if not valid_assigned_agents:
        # If no selected agents exist, default to CEO
        logger.warning(f"Selected agents {assigned_agent_ids} do not exist. Defaulting to CEO.")
        assigned_agent_ids = ["ceo_001"]
    else:
        assigned_agent_ids = valid_assigned_agents

    # Primary agent (lead) is either the first selected agent or CEO
    primary_agent_id = assigned_agent_ids[0] if assigned_agent_ids else "ceo_001"

    # Create project - assign to primary agent
    new_project = Project(
        project_id=uuid.uuid4(),
        name=project.name,
        description=project.description,
        priority=Priority[project.priority.upper()],
        status=ProjectStatus.PLANNING,
        owner_agent_id=primary_agent_id,
        requester_agent_id=None,  # None indicates human requester
    )
    session.add(new_project)
    await session.flush()

    # Store team assignment in metadata
    if len(assigned_agent_ids) > 1:
        new_project.meta_data = {
            "team_agents": assigned_agent_ids,
            "collaboration_enabled": True,
        }
    # Note: Single agent independent mode metadata is set later in the task creation logic

    # Create audit log for project creation
    audit_log = AuditLog(
        actor="user",
        action="project_created",
        entity_type="project",
        entity_id=str(new_project.project_id),
        new_value={
            "name": new_project.name,
            "description": new_project.description,
            "priority": new_project.priority.value,
            "status": new_project.status.value,
            "assigned_agents": assigned_agent_ids,
            "primary_agent": primary_agent_id,
            "is_team": len(assigned_agent_ids) > 1,
        }
    )
    session.add(audit_log)

    # Determine if this is a single-agent independent project or a multi-agent collaborative project
    is_independent_project = len(assigned_agent_ids) == 1
    is_default_ceo = assigned_agent_ids == ["ceo_001"] and not project.selectedAgents

    if is_independent_project:
        # Single agent project: Agent works independently without communication to other agents
        task_title = f"Complete project: {project.name}"
        task_description = f"You are assigned to independently complete this project:\n\n{project.description}\n\nWork independently on this project and submit the results directly to the user."

        primary_task = Task(
            task_id=uuid.uuid4(),
            project_id=new_project.project_id,
            assigned_to_agent_id=primary_agent_id,
            title=task_title,
            description=task_description,
            status=TaskStatus.PENDING,
            estimated_hours=1,
        )
        session.add(primary_task)

        # Create audit log for independent task creation
        task_audit_log = AuditLog(
            actor="system",
            action="task_created",
            entity_type="task",
            entity_id=str(primary_task.task_id),
            new_value={
                "title": primary_task.title,
                "assigned_to": primary_task.assigned_to_agent_id,
                "status": primary_task.status.value,
                "project_id": str(new_project.project_id),
                "is_independent": True,
                "work_mode": "independent",
            }
        )
        session.add(task_audit_log)

        # Store independent mode flag in metadata
        new_project.meta_data = {
            "independent_mode": True,
            "assigned_agent": primary_agent_id,
            "no_team_communication": True,
        }

    elif is_default_ceo:
        # Default CEO project: CEO evaluates, then hands off to team
        task_title = f"Evaluate project: {project.name}"
        task_description = f"Review and evaluate this project request:\n\n{project.description}"

        primary_task = Task(
            task_id=uuid.uuid4(),
            project_id=new_project.project_id,
            assigned_to_agent_id=primary_agent_id,
            title=task_title,
            description=task_description,
            status=TaskStatus.PENDING,
            estimated_hours=1,
        )
        session.add(primary_task)

        # Create audit log for default CEO task
        task_audit_log = AuditLog(
            actor="system",
            action="task_created",
            entity_type="task",
            entity_id=str(primary_task.task_id),
            new_value={
                "title": primary_task.title,
                "assigned_to": primary_task.assigned_to_agent_id,
                "status": primary_task.status.value,
                "project_id": str(new_project.project_id),
                "is_team_lead": True,
                "work_mode": "default_evaluation",
            }
        )
        session.add(task_audit_log)

    else:
        # Multi-agent collaborative project: Primary agent leads, other agents collaborate
        task_title = f"Lead project: {project.name}"
        team_names = ", ".join([name.split("_")[0].upper() for name in assigned_agent_ids])
        task_description = f"Lead this collaborative project with {team_names} agents:\n\n{project.description}\n\nTeam Collaboration: Coordinate with other team members to complete this project."

        primary_task = Task(
            task_id=uuid.uuid4(),
            project_id=new_project.project_id,
            assigned_to_agent_id=primary_agent_id,
            title=task_title,
            description=task_description,
            status=TaskStatus.PENDING,
            estimated_hours=1,
        )
        session.add(primary_task)

        # Create audit log for collaborative task
        task_audit_log = AuditLog(
            actor="system",
            action="task_created",
            entity_type="task",
            entity_id=str(primary_task.task_id),
            new_value={
                "title": primary_task.title,
                "assigned_to": primary_task.assigned_to_agent_id,
                "status": primary_task.status.value,
                "project_id": str(new_project.project_id),
                "is_team_lead": True,
                "work_mode": "collaborative",
            }
        )
        session.add(task_audit_log)

        # Create notification tasks for other team members
        for team_agent_id in assigned_agent_ids[1:]:
            collab_task = Task(
                task_id=uuid.uuid4(),
                project_id=new_project.project_id,
                assigned_to_agent_id=team_agent_id,
                title=f"Collaborate on: {project.name}",
                description=f"Collaborate with {primary_agent_id} and other team members on this project:\n\n{project.description}",
                status=TaskStatus.PENDING,
                estimated_hours=1,
            )
            session.add(collab_task)

            # Create audit log for collaboration task
            collab_audit_log = AuditLog(
                actor="system",
                action="task_created",
                entity_type="task",
                entity_id=str(collab_task.task_id),
                new_value={
                    "title": collab_task.title,
                    "assigned_to": collab_task.assigned_to_agent_id,
                    "status": collab_task.status.value,
                    "project_id": str(new_project.project_id),
                    "is_team_member": True,
                    "work_mode": "collaborative",
                }
            )
            session.add(collab_audit_log)
    
    await session.commit()
    await session.refresh(new_project)
    
    # 🚀 TRIGGER AGENTS IMMEDIATELY
    # Trigger all assigned agents to check for work now instead of waiting for next cycle
    import asyncio
    from app.agents.ceo_agent import CEOAgent

    async def trigger_team_agents():
        """Trigger all assigned agents to process the new tasks immediately."""
        try:
            from app.db.database import AsyncSessionLocal

            # For now, we only have the CEO agent fully implemented
            # Future: Implement agent selection for other agent types
            agent = CEOAgent()
            async with AsyncSessionLocal() as agent_session:
                # Run one check cycle immediately for all agents in the team
                await agent.check_cycle()
        except Exception as e:
            logger.error(f"Error triggering team agents {assigned_agent_ids}: {e}")

    # Run in background so we don't block the API response
    asyncio.create_task(trigger_team_agents())

    return ProjectResponse(
        project_id=str(new_project.project_id),
        name=new_project.name,
        description=new_project.description or "",
        status=new_project.status.value,
        priority=new_project.priority.value,
        version=new_project.version,
        created_at=new_project.created_at.isoformat(),
        updated_at=new_project.updated_at.isoformat(),
        tasks=[],
    )


@router.get("/projects/{project_id}", response_model=ProjectResponse, tags=["Projects"])
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get project details including all tasks."""
    result = await session.execute(
        select(Project).where(
            Project.project_id == project_id,
            Project.deleted_at.is_(None)
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get tasks
    tasks_result = await session.execute(
        select(Task)
        .where(Task.project_id == project_id)
        .order_by(Task.created_at)
    )
    tasks = tasks_result.scalars().all()

    return ProjectResponse(
        project_id=str(project.project_id),
        name=project.name,
        description=project.description or "",
        status=project.status.value,
        priority=project.priority.value,
        version=project.version,
        created_at=project.created_at.isoformat(),
        updated_at=project.updated_at.isoformat(),
        tasks=[
            TaskResponse(
                task_id=str(t.task_id),
                title=t.title,
                status=t.status.value,
                assigned_to=t.assigned_to_agent_id,
                created_at=t.created_at.isoformat(),
                updated_at=t.updated_at.isoformat(),
            )
            for t in tasks
        ],
    )


@router.get("/projects", response_model=List[ProjectResponse], tags=["Projects"])
async def list_projects(
    status: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    session: AsyncSession = Depends(get_session)
):
    """List all non-deleted projects with optional status filter."""
    query = select(Project).where(Project.deleted_at.is_(None)).order_by(Project.created_at.desc()).limit(limit)

    if status:
        try:
            status_enum = ProjectStatus[status.upper()]
            query = query.where(Project.status == status_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    result = await session.execute(query)
    projects = result.scalars().all()

    # Get tasks for each project
    response = []
    for project in projects:
        tasks_result = await session.execute(
            select(Task).where(Task.project_id == project.project_id)
        )
        tasks = tasks_result.scalars().all()

        response.append(
            ProjectResponse(
                project_id=str(project.project_id),
                name=project.name,
                description=project.description or "",
                status=project.status.value,
                priority=project.priority.value,
                version=project.version,
                created_at=project.created_at.isoformat(),
                updated_at=project.updated_at.isoformat(),
                tasks=[
                    TaskResponse(
                        task_id=str(t.task_id),
                        title=t.title,
                        status=t.status.value,
                        assigned_to=t.assigned_to_agent_id,
                        created_at=t.created_at.isoformat(),
                        updated_at=t.updated_at.isoformat(),
                    )
                    for t in tasks
                ],
            )
        )

    return response


@router.post("/projects/{project_id}/restart", response_model=ProjectResponse, tags=["Projects"])
async def restart_project(
    project_id: str,
    project_update: Optional[ProjectCreate] = None,
    session: AsyncSession = Depends(get_session)
):
    """
    Restart a project with optional updated requirements.
    Creates a new version of the project while keeping the original.
    """
    # Get original project
    result = await session.execute(
        select(Project).where(Project.project_id == project_id)
    )
    original_project = result.scalar_one_or_none()

    if not original_project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Determine the root project ID (for version tracking)
    # If this project has a parent, use that as the root, otherwise use itself
    root_project_id = original_project.parent_project_id or original_project.project_id

    # Find the maximum version across the entire version chain
    version_result = await session.execute(
        select(func.max(Project.version))
        .where(
            (Project.project_id == root_project_id) |
            (Project.parent_project_id == root_project_id)
        )
    )
    max_version = version_result.scalar() or original_project.version
    next_version = max_version + 1

    # Use updated details if provided, otherwise use original
    if project_update:
        name = project_update.name
        description = project_update.description
        priority = Priority[project_update.priority.upper()]
    else:
        # Strip any existing version suffix (e.g., " (v2)" or " (v3)") from the name
        base_name = re.sub(r'\s*\(v\d+\)\s*$', '', original_project.name).strip()
        name = f"{base_name} (v{next_version})"
        description = original_project.description
        priority = original_project.priority

    # Create new version of the project
    new_project = Project(
        project_id=uuid.uuid4(),
        name=name,
        description=description,
        priority=priority,
        status=ProjectStatus.PLANNING,
        owner_agent_id="ceo_001",
        requester_agent_id=None,
        version=next_version,
        parent_project_id=root_project_id,  # Always point to the root project
        meta_data={
            "restarted_from": str(original_project.project_id),
            "original_version": original_project.version,
            "restart_reason": "User requested restart"
        }
    )
    session.add(new_project)
    await session.flush()

    # Create task for CEO to process this restarted project
    ceo_task = Task(
        task_id=uuid.uuid4(),
        project_id=new_project.project_id,
        assigned_to_agent_id="ceo_001",
        title=f"Evaluate restarted project (v{next_version}): {name}",
        description=f"""Review and approve/reject this restarted project request:

**Original Project ID:** {project_id}
**Version:** {next_version}
**Previous Version:** {original_project.version}

**Description:**
{description}

**Context:**
This is a restart of a previous project. Review the original project's outputs and this new request to provide an improved implementation.""",
        status=TaskStatus.PENDING,
        estimated_hours=1,
        version=next_version,
    )
    session.add(ceo_task)
    await session.commit()
    await session.refresh(new_project)

    return ProjectResponse(
        project_id=str(new_project.project_id),
        name=new_project.name,
        description=new_project.description or "",
        status=new_project.status.value,
        priority=new_project.priority.value,
        version=new_project.version,
        created_at=new_project.created_at.isoformat(),
        updated_at=new_project.updated_at.isoformat(),
        tasks=[],
    )


@router.get("/projects/{project_id}/versions", tags=["Projects"])
async def get_project_versions(
    project_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get all versions of a project."""
    # First check if this is a parent or child project
    result = await session.execute(
        select(Project).where(Project.project_id == project_id)
    )
    current_project = result.scalar_one_or_none()

    if not current_project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Determine the root project ID
    root_id = current_project.parent_project_id or current_project.project_id

    # Get all versions (original + all children)
    versions_result = await session.execute(
        select(Project)
        .where(
            (Project.project_id == root_id) |
            (Project.parent_project_id == root_id)
        )
        .order_by(Project.version.asc())
    )
    versions = versions_result.scalars().all()

    return [
        {
            "project_id": str(v.project_id),
            "name": v.name,
            "version": v.version,
            "status": v.status.value,
            "created_at": v.created_at.isoformat(),
            "is_current": str(v.project_id) == project_id,
        }
        for v in versions
    ]


@router.get("/projects/{project_id}/activity", tags=["Projects"])
async def get_project_activity(
    project_id: str,
    limit: int = Query(default=50, le=200),
    session: AsyncSession = Depends(get_session)
):
    """Get real-time activity feed for a project including all tasks."""
    # Verify project exists
    project_result = await session.execute(
        select(Project).where(Project.project_id == project_id)
    )
    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Get all task IDs for this project
    tasks_result = await session.execute(
        select(Task.task_id).where(Task.project_id == project_id)
    )
    task_ids = [str(task_id) for task_id in tasks_result.scalars().all()]

    # Get audit logs for the project and its tasks
    if task_ids:
        query = select(AuditLog).where(
            (AuditLog.entity_id == project_id) |
            (AuditLog.entity_id.in_(task_ids))
        ).order_by(AuditLog.timestamp.desc()).limit(limit)
    else:
        query = select(AuditLog).where(
            AuditLog.entity_id == project_id
        ).order_by(AuditLog.timestamp.desc()).limit(limit)

    result = await session.execute(query)
    logs = result.scalars().all()

    # Get messages related to this project
    messages_result = await session.execute(
        select(Message)
        .where(Message.related_project_id == project_id)
        .order_by(Message.timestamp.desc())
        .limit(20)
    )
    messages = messages_result.scalars().all()

    # Get decisions for this project
    decisions_result = await session.execute(
        select(Decision)
        .where(Decision.project_id == project_id)
        .order_by(Decision.timestamp.desc())
        .limit(10)
    )
    decisions = decisions_result.scalars().all()

    # Get human interactions for this project
    interactions_result = await session.execute(
        select(HumanInteraction)
        .where(
            (HumanInteraction.related_entity_type == "project") |
            (HumanInteraction.meta_data['related_project_id'].astext == project_id)
        )
        .order_by(HumanInteraction.created_at.desc())
        .limit(10)
    )
    interactions = interactions_result.scalars().all()

    # Combine and format all activities
    activities = []

    # Add audit logs
    for log in logs:
        activities.append({
            "type": "audit",
            "timestamp": log.timestamp.isoformat(),
            "actor": log.actor,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": str(log.entity_id) if log.entity_id else None,
            "details": log.new_value,
        })

    # Add messages
    for msg in messages:
        activities.append({
            "type": "message",
            "timestamp": msg.timestamp.isoformat(),
            "from_agent": msg.from_agent_id,
            "to_agent": msg.to_agent_id,
            "message_type": msg.message_type.value if msg.message_type else "info",
            "content": msg.content,
            "priority": msg.priority.value if msg.priority else "medium",
        })

    # Add decisions
    for decision in decisions:
        activities.append({
            "type": "decision",
            "timestamp": decision.timestamp.isoformat(),
            "actor": decision.made_by_agent_id,
            "decision_type": decision.decision_type,
            "question": decision.question,
            "decision": decision.decision,
            "rationale": decision.rationale,
        })

    # Add human interactions
    for interaction in interactions:
        activities.append({
            "type": "human_input",
            "timestamp": interaction.created_at.isoformat(),
            "interaction_type": interaction.interaction_type,
            "request": interaction.request,
            "response": interaction.human_response,
            "status": interaction.status,
            "target_agent": interaction.meta_data.get("target_agent_id") if interaction.meta_data else None,
        })

    # Sort all activities by timestamp
    activities.sort(key=lambda x: x["timestamp"], reverse=True)

    return activities[:limit]


@router.delete("/projects/{project_id}", tags=["Projects"])
async def soft_delete_project(
    project_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Soft delete a project and all its associated tasks.
    Properly stops and cancels all tasks before deletion.
    Sets deleted_at timestamp instead of actually deleting records.
    """
    # Check if project exists and is not already deleted
    result = await session.execute(
        select(Project).where(
            Project.project_id == project_id,
            Project.deleted_at.is_(None)
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found or already deleted")

    # Get all tasks for this project that aren't already deleted
    tasks_result = await session.execute(
        select(Task).where(
            Task.project_id == project_id,
            Task.deleted_at.is_(None)
        )
    )
    tasks = tasks_result.scalars().all()

    # Cancel all active tasks and clear agent assignments
    cancelled_tasks = []
    freed_agents = []

    for task in tasks:
        # Only cancel tasks that aren't already completed or cancelled
        if task.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
            # Track which tasks were actively cancelled
            cancelled_tasks.append({
                "task_id": str(task.task_id),
                "title": task.title,
                "status": task.status.value,
                "assigned_to": task.assigned_to_agent_id
            })

            # Check if agent is currently working on this task
            agent_status_result = await session.execute(
                select(AgentStatus).where(
                    AgentStatus.agent_id == task.assigned_to_agent_id,
                    AgentStatus.current_task_id == task.task_id
                )
            )
            agent_status = agent_status_result.scalar_one_or_none()

            if agent_status:
                # Free up the agent
                agent_status.current_task_id = None
                agent_status.availability = Availability.AVAILABLE
                agent_status.updated_at = func.now()
                freed_agents.append(task.assigned_to_agent_id)

    # Cancel and soft delete all associated tasks
    await session.execute(
        update(Task)
        .where(
            Task.project_id == project_id,
            Task.deleted_at.is_(None)
        )
        .values(
            status=TaskStatus.CANCELLED,
            deleted_at=func.now()
        )
    )

    # Cancel the project and soft delete it
    await session.execute(
        update(Project)
        .where(Project.project_id == project_id)
        .values(
            status=ProjectStatus.CANCELLED,
            deleted_at=func.now()
        )
    )

    # Create audit log for project deletion
    audit_log = AuditLog(
        actor="user",
        action="project_deleted",
        entity_type="project",
        entity_id=str(project_id),
        old_value={
            "name": project.name,
            "status": project.status.value,
            "tasks_count": len(tasks),
        },
        new_value={
            "deleted_at": datetime.now().isoformat(),
            "cancelled_tasks": len(cancelled_tasks),
            "freed_agents": freed_agents,
        }
    )
    session.add(audit_log)

    await session.commit()

    return {
        "message": "Project and associated tasks stopped and deleted successfully",
        "project_id": str(project_id),
        "deleted_at": datetime.now().isoformat(),
        "tasks_cancelled": len(cancelled_tasks),
        "tasks_total": len(tasks),
        "agents_freed": freed_agents,
        "cancelled_tasks": cancelled_tasks
    }


@router.post("/projects/{project_id}/follow-up", tags=["Projects"])
async def add_follow_up_question(
    project_id: str,
    follow_up: dict,
    session: AsyncSession = Depends(get_session)
):
    """
    Add a follow-up question to an existing project.
    Creates a new task for the CEO to answer the follow-up question.
    """
    # Check if project exists
    result = await session.execute(
        select(Project).where(
            Project.project_id == project_id,
            Project.deleted_at.is_(None)
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    question = follow_up.get("question")
    priority_str = follow_up.get("priority", "medium")

    if not question:
        raise HTTPException(status_code=400, detail="Question is required")

    try:
        priority = Priority[priority_str.upper()]
    except KeyError:
        priority = Priority.MEDIUM

    # Create a new task for CEO to answer the follow-up
    ceo_task = Task(
        task_id=uuid.uuid4(),
        project_id=project.project_id,
        assigned_to_agent_id="ceo_001",
        title=f"Follow-up question: {question[:50]}{'...' if len(question) > 50 else ''}",
        description=f"""Follow-up question on project: {project.name}

**Original Project Description:**
{project.description}

**Follow-up Question:**
{question}

Please provide a detailed answer to this follow-up question.""",
        status=TaskStatus.PENDING,
        estimated_hours=1,
    )
    session.add(ceo_task)

    # Update project status if it was completed (reopen for follow-up)
    if project.status == ProjectStatus.COMPLETED:
        project.status = ProjectStatus.IN_PROGRESS

    # Log the follow-up question
    audit_log = AuditLog(
        actor="human",
        action="follow_up_question_added",
        entity_type="project",
        entity_id=str(project_id),
        new_value={
            "question": question,
            "priority": priority_str,
            "task_id": str(ceo_task.task_id),
        }
    )
    session.add(audit_log)

    await session.commit()
    await session.refresh(ceo_task)

    return {
        "message": "Follow-up question added successfully",
        "project_id": str(project_id),
        "task_id": str(ceo_task.task_id),
        "question": question,
        "priority": priority.value,
        "created_at": ceo_task.created_at.isoformat(),
    }


@router.post("/projects/{project_id}/cancel", tags=["Projects"])
async def cancel_project(
    project_id: str,
    reason: str = Query(..., description="Reason for cancellation"),
    session: AsyncSession = Depends(get_session)
):
    """
    Cancel a project and all its associated tasks.
    Updates status to CANCELLED and logs the reason.
    """
    # Check if project exists and is not already completed/cancelled
    result = await session.execute(
        select(Project).where(
            Project.project_id == project_id,
            Project.deleted_at.is_(None)
        )
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project.status in [ProjectStatus.COMPLETED, ProjectStatus.CANCELLED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel project with status: {project.status.value}"
        )

    # Update project status to CANCELLED
    await session.execute(
        update(Project)
        .where(Project.project_id == project_id)
        .values(
            status=ProjectStatus.CANCELLED,
            meta_data=func.jsonb_set(
                Project.meta_data,
                '{cancellation}',
                func.cast({
                    "cancelled_at": datetime.utcnow().isoformat(),
                    "cancelled_by": "user",
                    "reason": reason
                }, type_=func.jsonb())
            )
        )
    )

    # Cancel all non-completed tasks
    await session.execute(
        update(Task)
        .where(
            Task.project_id == project_id,
            Task.status != TaskStatus.COMPLETED
        )
        .values(
            status=TaskStatus.CANCELLED,
            blocking_reason=f"Project cancelled: {reason}"
        )
    )

    # Log the cancellation
    audit_log = AuditLog(
        actor="user",
        action="project_cancelled",
        entity_type="project",
        entity_id=str(project_id),
        new_value={
            "status": "cancelled",
            "reason": reason,
            "cancelled_by": "user"
        }
    )
    session.add(audit_log)

    await session.commit()

    return {
        "message": "Project cancelled successfully",
        "project_id": str(project_id),
        "reason": reason,
        "cancelled_at": datetime.utcnow().isoformat(),
    }


# ===== Agent Endpoints =====
# NOTE: All agent endpoints have been consolidated to /api/v1/agents in agents.py
# This provides a unified endpoint with full agent details, capabilities, and status


@router.get("/agents/{agent_id}", tags=["Agents"])
async def get_agent_details(
    agent_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get detailed information about a specific agent."""
    agent_result = await session.execute(
        select(Agent).where(Agent.agent_id == agent_id)
    )
    agent = agent_result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    status_result = await session.execute(
        select(AgentStatus).where(AgentStatus.agent_id == agent_id)
    )
    status = status_result.scalar_one_or_none()

    # Get current tasks
    tasks_result = await session.execute(
        select(Task)
        .where(
            Task.assigned_to_agent_id == agent_id,
            Task.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED])
        )
        .order_by(Task.created_at.desc())
    )
    tasks = tasks_result.scalars().all()

    return {
        "agent_id": agent.agent_id,
        "name": agent.name,
        "role": agent.role,
        "department": agent.department,  # Legacy field
        "departments": agent.all_departments,  # Multi-department support
        "reports_to": agent.reports_to,
        "status": {
            "availability": status.availability.value if status else "unknown",
            "last_active": status.last_active.isoformat() if status else None,
            "current_task_id": str(status.current_task_id) if status and status.current_task_id else None,
            "health_status": status.health_status if status else "unknown",
        },
        "current_tasks": [
            {
                "task_id": str(t.task_id),
                "title": t.title,
                "status": t.status.value,
                "created_at": t.created_at.isoformat(),
            }
            for t in tasks
        ],
    }


# ===== Task Endpoints =====

@router.get("/tasks", tags=["Tasks"])
async def get_all_tasks(
    status: Optional[str] = None,
    agent_id: Optional[str] = None,
    project_id: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    session: AsyncSession = Depends(get_session)
):
    """Get all tasks with optional filters."""
    query = select(Task).order_by(Task.created_at.desc()).limit(limit)

    if status:
        try:
            status_enum = TaskStatus[status.upper()]
            query = query.where(Task.status == status_enum)
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")

    if agent_id:
        query = query.where(Task.assigned_to_agent_id == agent_id)

    if project_id:
        query = query.where(Task.project_id == project_id)

    result = await session.execute(query)
    tasks = result.scalars().all()

    return [
        {
            "task_id": str(t.task_id),
            "project_id": str(t.project_id),
            "title": t.title,
            "description": t.description,
            "status": t.status.value,
            "assigned_to": t.assigned_to_agent_id,
            "created_at": t.created_at.isoformat(),
            "updated_at": t.updated_at.isoformat(),
            "output": t.output,
        }
        for t in tasks
    ]


@router.get("/tasks/{task_id}", tags=["Tasks"])
async def get_task_details(
    task_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get detailed information about a specific task."""
    result = await session.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task_id": str(task.task_id),
        "project_id": str(task.project_id),
        "title": task.title,
        "description": task.description,
        "status": task.status.value,
        "assigned_to": task.assigned_to_agent_id,
        "assigned_to_agent_id": task.assigned_to_agent_id,
        "dependencies": task.dependencies,
        "estimated_hours": task.estimated_hours,
        "actual_hours": task.actual_hours,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
        "blocking_reason": task.blocking_reason,
        "output": task.output,
        "version": task.version if hasattr(task, 'version') else 1,
    }


@router.get("/tasks/{task_id}/activity", tags=["Tasks"])
async def get_task_activity(
    task_id: str,
    limit: int = Query(default=50, le=200),
    session: AsyncSession = Depends(get_session)
):
    """Get real-time activity feed for a specific task."""
    # Verify task exists
    task_result = await session.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = task_result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Get audit logs for this task
    logs_result = await session.execute(
        select(AuditLog)
        .where(AuditLog.entity_id == task_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
    )
    logs = logs_result.scalars().all()

    # Get messages related to this task
    messages_result = await session.execute(
        select(Message)
        .where(Message.related_task_id == task_id)
        .order_by(Message.timestamp.desc())
        .limit(20)
    )
    messages = messages_result.scalars().all()

    # Get decisions for this task
    decisions_result = await session.execute(
        select(Decision)
        .where(Decision.task_id == task_id)
        .order_by(Decision.timestamp.desc())
        .limit(10)
    )
    decisions = decisions_result.scalars().all()

    # Get human interactions for this task
    interactions_result = await session.execute(
        select(HumanInteraction)
        .where(
            (HumanInteraction.related_entity_type == "task") |
            (HumanInteraction.meta_data['related_task_id'].astext == str(task_id))
        )
        .order_by(HumanInteraction.created_at.desc())
        .limit(10)
    )
    interactions = interactions_result.scalars().all()

    # Combine and format all activities
    activities = []

    # Add audit logs
    for log in logs:
        activities.append({
            "type": "audit",
            "timestamp": log.timestamp.isoformat(),
            "actor": log.actor,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": str(log.entity_id) if log.entity_id else None,
            "details": log.new_value,
        })

    # Add messages
    for msg in messages:
        activities.append({
            "type": "message",
            "timestamp": msg.timestamp.isoformat(),
            "from_agent": msg.from_agent_id,
            "to_agent": msg.to_agent_id,
            "message_type": msg.message_type.value if msg.message_type else "info",
            "content": msg.content,
            "priority": msg.priority.value if msg.priority else "medium",
        })

    # Add decisions
    for decision in decisions:
        activities.append({
            "type": "decision",
            "timestamp": decision.timestamp.isoformat(),
            "agent_id": decision.made_by_agent_id,
            "decision_type": decision.decision_type,
            "question": decision.question,
            "decision": decision.decision,
            "rationale": decision.rationale,
        })

    # Add human interactions
    for interaction in interactions:
        activities.append({
            "type": "human_input",
            "timestamp": interaction.created_at.isoformat(),
            "interaction_type": interaction.interaction_type,
            "request": interaction.request,
            "response": interaction.human_response,
            "status": interaction.status,
            "target_agent": interaction.meta_data.get("target_agent_id") if interaction.meta_data else None,
        })

    # Sort all activities by timestamp
    activities.sort(key=lambda x: x["timestamp"], reverse=True)

    return activities[:limit]


@router.post("/tasks/{task_id}/cancel", tags=["Tasks"])
async def cancel_task(
    task_id: str,
    reason: str = Query(..., description="Reason for cancellation"),
    session: AsyncSession = Depends(get_session)
):
    """
    Cancel a task.
    Updates status to CANCELLED and logs the reason.
    """
    # Check if task exists and is not already completed/cancelled
    result = await session.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel task with status: {task.status.value}"
        )

    # Update task status to CANCELLED
    await session.execute(
        update(Task)
        .where(Task.task_id == task_id)
        .values(
            status=TaskStatus.CANCELLED,
            blocking_reason=f"Cancelled by user: {reason}"
        )
    )

    # Log the cancellation
    audit_log = AuditLog(
        actor="user",
        action="task_cancelled",
        entity_type="task",
        entity_id=str(task_id),
        new_value={
            "status": "cancelled",
            "reason": reason,
            "cancelled_by": "user"
        }
    )
    session.add(audit_log)

    await session.commit()

    # Check if project status needs updating
    project_id = task.project_id
    project_status_update = await _check_and_update_project_status(session, project_id)

    return {
        "message": "Task cancelled successfully",
        "task_id": str(task_id),
        "reason": reason,
        "cancelled_at": datetime.utcnow().isoformat(),
        "project_status": project_status_update.get("status") if project_status_update else None,
        "project_message": project_status_update.get("message") if project_status_update else None,
    }


class ResolveReviewRequest(BaseModel):
    """Request model for resolving a review timeout escalation."""
    resolution_notes: str
    clear_direction: str
    resolved_by_agent_id: str


@router.post("/tasks/{task_id}/resolve-review", tags=["Tasks"])
async def resolve_review_escalation(
    task_id: str,
    request: ResolveReviewRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Resolve a task review timeout escalation by providing clear direction.

    This endpoint is called by project managers, CTOs, CEOs, or HR to resolve
    tasks that have been in REVIEW status for more than 5 minutes.

    Parameters:
    - task_id: The task ID
    - resolution_notes: Feedback from the manager on what was reviewed
    - clear_direction: Clear direction on what needs to be done next
    - resolved_by_agent_id: The agent ID of the manager resolving this
    """
    from app.services.escalation_service import EscalationService

    try:
        # Verify task exists and is in REVIEW status
        task_result = await session.execute(
            select(Task).where(Task.task_id == task_id)
        )
        task = task_result.scalar_one_or_none()

        if not task:
            raise HTTPException(status_code=404, detail="Task not found")

        if task.status != TaskStatus.REVIEW:
            raise HTTPException(
                status_code=400,
                detail=f"Task is not in REVIEW status. Current status: {task.status.value}"
            )

        if not task.review_started_at:
            raise HTTPException(
                status_code=400,
                detail="Task does not have a review_started_at timestamp"
            )

        # Use escalation service to resolve the review escalation
        escalation_service = EscalationService(session)
        updated_task = await escalation_service.resolve_review_escalation(
            task_id=task_id,
            resolution_notes=request.resolution_notes,
            clear_direction=request.clear_direction,
            resolved_by_agent_id=request.resolved_by_agent_id,
        )

        # Log the resolution
        audit_log = AuditLog(
            actor=request.resolved_by_agent_id,
            action="review_escalation_resolved",
            entity_type="task",
            entity_id=str(task_id),
            new_value={
                "status": "in_progress",
                "resolved_by": request.resolved_by_agent_id,
                "resolution_notes": request.resolution_notes,
                "clear_direction": request.clear_direction,
                "resolved_at": datetime.utcnow().isoformat(),
            }
        )
        session.add(audit_log)
        await session.commit()

        # Calculate time spent in review
        review_duration_seconds = (datetime.utcnow() - task.review_started_at).total_seconds()
        review_duration_minutes = review_duration_seconds / 60

        return {
            "message": "Review escalation resolved successfully",
            "task_id": str(task_id),
            "previous_status": "review",
            "new_status": "in_progress",
            "resolved_by": request.resolved_by_agent_id,
            "resolution_notes": request.resolution_notes,
            "clear_direction": request.clear_direction,
            "review_duration_minutes": round(review_duration_minutes, 2),
            "resolved_at": datetime.utcnow().isoformat(),
        }

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error resolving review escalation for task {task_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to resolve review escalation")


# ===== Dashboard Endpoint =====

@router.get("/dashboard", response_model=DashboardResponse, tags=["Dashboard"])
async def get_dashboard_data(session: AsyncSession = Depends(get_session)):
    """Get comprehensive dashboard data."""
    # Total projects count (excluding deleted)
    total_projects = await session.execute(
        select(func.count(Project.project_id)).where(Project.deleted_at.is_(None))
    )

    # Active projects count (excluding deleted)
    active_projects = await session.execute(
        select(func.count(Project.project_id)).where(
            Project.status.in_([ProjectStatus.PLANNING, ProjectStatus.IN_PROGRESS, ProjectStatus.REVIEW]),
            Project.deleted_at.is_(None)
        )
    )

    # Completed projects count (excluding deleted)
    completed_projects = await session.execute(
        select(func.count(Project.project_id)).where(
            Project.status == ProjectStatus.COMPLETED,
            Project.deleted_at.is_(None)
        )
    )

    # Total tasks count
    total_tasks = await session.execute(
        select(func.count(Task.task_id))
    )

    # Task counts by status
    pending_tasks = await session.execute(
        select(func.count(Task.task_id)).where(Task.status == TaskStatus.PENDING)
    )
    in_progress_tasks = await session.execute(
        select(func.count(Task.task_id)).where(Task.status == TaskStatus.IN_PROGRESS)
    )
    completed_tasks = await session.execute(
        select(func.count(Task.task_id)).where(Task.status == TaskStatus.COMPLETED)
    )
    blocked_tasks = await session.execute(
        select(func.count(Task.task_id)).where(Task.status == TaskStatus.BLOCKED)
    )

    # Agent counts
    total_agents = await session.execute(
        select(func.count(Agent.agent_id))
    )
    active_agents = await session.execute(
        select(func.count(AgentStatus.agent_id)).where(
            AgentStatus.availability.in_(["AVAILABLE", "BUSY"])
        )
    )

    # Recent projects (last 10, excluding deleted)
    recent_projects_result = await session.execute(
        select(Project)
        .where(Project.deleted_at.is_(None))
        .order_by(Project.created_at.desc())
        .limit(10)
    )
    recent_projects = recent_projects_result.scalars().all()

    # Recent tasks (last 10)
    recent_tasks_result = await session.execute(
        select(Task)
        .order_by(Task.updated_at.desc())
        .limit(10)
    )
    recent_tasks = recent_tasks_result.scalars().all()

    # Recent escalations
    recent_escalations = await session.execute(
        select(Escalation)
        .where(Escalation.status == "open")
        .order_by(Escalation.created_at.desc())
        .limit(5)
    )

    return DashboardResponse(
        total_projects=total_projects.scalar() or 0,
        active_projects=active_projects.scalar() or 0,
        completed_projects=completed_projects.scalar() or 0,
        total_tasks=total_tasks.scalar() or 0,
        pending_tasks=pending_tasks.scalar() or 0,
        in_progress_tasks=in_progress_tasks.scalar() or 0,
        completed_tasks=completed_tasks.scalar() or 0,
        blocked_tasks=blocked_tasks.scalar() or 0,
        total_agents=total_agents.scalar() or 0,
        active_agents=active_agents.scalar() or 0,
        recent_activity={
            "projects": [
                {
                    "project_id": str(p.project_id),
                    "name": p.name,
                    "description": p.description or "",
                    "status": p.status.value,
                    "priority": p.priority.value,
                    "created_at": p.created_at.isoformat(),
                }
                for p in recent_projects
            ],
            "tasks": [
                {
                    "task_id": str(t.task_id),
                    "title": t.title,
                    "status": t.status.value,
                    "assigned_to_agent_id": t.assigned_to_agent_id,
                    "created_at": t.created_at.isoformat(),
                    "updated_at": t.updated_at.isoformat(),
                }
                for t in recent_tasks
            ],
        },
        recent_escalations=[
            {
                "id": str(e.escalation_id),
                "type": e.issue_type,
                "severity": e.severity.value,
                "description": e.description,
                "escalated_by": e.escalated_by_agent_id,
                "created_at": e.created_at.isoformat(),
            }
            for e in recent_escalations.scalars().all()
        ],
    )


# ===== Messages Endpoint =====

@router.get("/messages", response_model=List[MessageResponse], tags=["Messages"])
async def get_messages(
    agent_id: Optional[str] = None,
    limit: int = Query(default=50, le=100),
    session: AsyncSession = Depends(get_session)
):
    """Get messages with optional agent filter."""
    query = select(Message).order_by(Message.timestamp.desc()).limit(limit)

    if agent_id:
        query = query.where(
            (Message.from_agent_id == agent_id) | (Message.to_agent_id == agent_id)
        )

    result = await session.execute(query)
    messages = result.scalars().all()

    return [
        MessageResponse(
            message_id=str(m.message_id),
            from_agent_id=m.from_agent_id,
            to_agent_id=m.to_agent_id,
            content=m.content,
            message_type=m.message_type.value,
            priority=m.priority.value,
            read_status=m.read_status,
            timestamp=m.timestamp.isoformat(),
        )
        for m in messages
    ]

# ===== Human Interactions Endpoint =====

@router.get("/human-interactions", response_model=List[HumanInteractionResponse], tags=["Human Interactions"])
async def get_human_interactions(
    status: str = Query(default="pending"),
    session: AsyncSession = Depends(get_session)
):
    """Get pending human interaction requests."""
    result = await session.execute(
        select(HumanInteraction)
        .where(HumanInteraction.status == status)
        .order_by(HumanInteraction.created_at.desc())
    )
    interactions = result.scalars().all()

    return [
        HumanInteractionResponse(
            interaction_id=str(i.interaction_id),
            initiated_by_agent_id=i.initiated_by_agent_id,
            interaction_type=i.interaction_type,
            request=i.request,
            status=i.status,
            created_at=i.created_at.isoformat(),
        )
        for i in interactions
    ]


@router.post("/human-interactions/{interaction_id}/respond", tags=["Human Interactions"])
async def respond_to_interaction(
    interaction_id: str,
    response: dict,
    session: AsyncSession = Depends(get_session)
):
    """Human responds to an agent's request."""
    stmt = (
        update(HumanInteraction)
        .where(HumanInteraction.interaction_id == interaction_id)
        .values(
            human_response=response.get("response"),
            status="responded",
            responded_at=datetime.utcnow(),
        )
    )
    await session.execute(stmt)
    await session.commit()

    return {"status": "success", "message": "Response recorded"}


# ===== Project Completion Endpoint =====

@router.post("/projects/{project_id}/check-completion", tags=["Projects"])
async def check_project_completion(
    project_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Manually trigger project completion check.
    Checks if all tasks are complete and marks project as complete if so.
    """
    from app.utils.project_completion import check_and_complete_project

    result = await check_and_complete_project(session, project_id)

    return {
        "project_id": project_id,
        "completed": result.get("completed", False),
        "reason": result.get("reason", "Unknown"),
        "final_status": result.get("final_status"),
        "stats": result.get("stats", {})
    }


@router.get("/projects/{project_id}/completion-summary", tags=["Projects"])
async def get_completion_summary(
    project_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get detailed project completion summary without modifying anything.
    Useful for showing progress to users.
    """
    from app.utils.project_completion import get_project_completion_summary

    summary = await get_project_completion_summary(session, project_id)
    return summary


# ===== Agent Activity Endpoint =====

@router.get("/agents/{agent_id}/activity", tags=["Agents"])
async def get_agent_activity(
    agent_id: str,
    limit: int = Query(default=50, le=200),
    session: AsyncSession = Depends(get_session)
):
    """
    Get comprehensive activity feed for a specific agent showing:
    - Their current task and project
    - Recent audit logs
    - Messages sent/received
    - Decisions made
    - Escalations created
    """
    # Get agent info
    agent_result = await session.execute(
        select(Agent).where(Agent.agent_id == agent_id)
    )
    agent = agent_result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Get agent status
    status_result = await session.execute(
        select(AgentStatus).where(AgentStatus.agent_id == agent_id)
    )
    agent_status = status_result.scalar_one_or_none()

    # Get current task and project if any
    current_task = None
    current_project = None
    if agent_status and agent_status.current_task_id:
        task_result = await session.execute(
            select(Task).where(Task.task_id == agent_status.current_task_id)
        )
        task = task_result.scalar_one_or_none()
        if task:
            current_task = {
                "task_id": str(task.task_id),
                "title": task.title,
                "status": task.status.value,
                "project_id": str(task.project_id),
            }

            # Get the project
            project_result = await session.execute(
                select(Project).where(Project.project_id == task.project_id)
            )
            project = project_result.scalar_one_or_none()
            if project:
                current_project = {
                    "project_id": str(project.project_id),
                    "name": project.name,
                    "status": project.status.value,
                }

    # Get recent audit logs for this agent
    audit_result = await session.execute(
        select(AuditLog)
        .where(AuditLog.actor == agent_id)
        .order_by(AuditLog.timestamp.desc())
        .limit(limit)
    )
    audit_logs = audit_result.scalars().all()

    # Get recent messages (sent or received)
    messages_result = await session.execute(
        select(Message)
        .where(
            (Message.from_agent_id == agent_id) | (Message.to_agent_id == agent_id)
        )
        .order_by(Message.timestamp.desc())
        .limit(limit)
    )
    messages = messages_result.scalars().all()

    # Get recent decisions
    decisions_result = await session.execute(
        select(Decision)
        .where(Decision.made_by_agent_id == agent_id)
        .order_by(Decision.timestamp.desc())
        .limit(limit)
    )
    decisions = decisions_result.scalars().all()

    # Get recent escalations
    escalations_result = await session.execute(
        select(Escalation)
        .where(
            (Escalation.escalated_by_agent_id == agent_id) |
            (Escalation.escalated_to_agent_id == agent_id)
        )
        .order_by(Escalation.created_at.desc())
        .limit(limit)
    )
    escalations = escalations_result.scalars().all()

    # Get recent human interactions initiated by this agent
    interactions_result = await session.execute(
        select(HumanInteraction)
        .where(HumanInteraction.initiated_by_agent_id == agent_id)
        .order_by(HumanInteraction.created_at.desc())
        .limit(limit)
    )
    interactions = interactions_result.scalars().all()

    # Combine all activities
    activities = []

    for log in audit_logs:
        activities.append({
            "type": "audit",
            "timestamp": log.timestamp.isoformat(),
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": str(log.entity_id) if log.entity_id else None,
            "details": {
                "old_value": log.old_value,
                "new_value": log.new_value,
                "metadata": log.details,
            }
        })

    for msg in messages:
        activities.append({
            "type": "message",
            "timestamp": msg.timestamp.isoformat(),
            "from_agent": msg.from_agent_id,
            "to_agent": msg.to_agent_id,
            "content": msg.content,
            "message_type": msg.message_type.value if msg.message_type else None,
            "priority": msg.priority.value,
            "read": msg.read_status,
        })

    for decision in decisions:
        activities.append({
            "type": "decision",
            "timestamp": decision.timestamp.isoformat(),
            "decision_type": decision.decision_type,
            "question": decision.question,
            "decision": decision.decision,
            "rationale": decision.rationale,
            "project_id": str(decision.project_id) if decision.project_id else None,
            "task_id": str(decision.task_id) if decision.task_id else None,
        })

    for escalation in escalations:
        activities.append({
            "type": "escalation",
            "timestamp": escalation.created_at.isoformat(),
            "issue_type": escalation.issue_type,
            "severity": escalation.severity.value,
            "escalated_by": escalation.escalated_by_agent_id,
            "escalated_to": escalation.escalated_to_agent_id,
            "description": escalation.description,
            "status": escalation.status,
        })

    for interaction in interactions:
        activities.append({
            "type": "human_interaction",
            "timestamp": interaction.created_at.isoformat(),
            "interaction_type": interaction.interaction_type,
            "request": interaction.request,
            "status": interaction.status,
            "response": interaction.human_response,
        })

    # Sort all activities by timestamp
    activities.sort(key=lambda x: x["timestamp"], reverse=True)

    return {
        "agent": {
            "agent_id": agent.agent_id,
            "name": agent.name,
            "role": agent.role,
            "department": agent.department,  # Legacy field
            "departments": agent.all_departments,  # Multi-department support
        },
        "status": {
            "availability": agent_status.availability.value if agent_status else "offline",
            "last_active": agent_status.last_active.isoformat() if agent_status else None,
            "health_status": agent_status.health_status if agent_status else "unknown",
        },
        "current_work": {
            "task": current_task,
            "project": current_project,
        },
        "activities": activities[:limit],
    }


@router.post("/agents/{agent_id}/human-input", tags=["Agents"])
async def add_human_input_to_agent(
    agent_id: str,
    input_data: HumanInputCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Add human input/interruption to an agent's work.
    This creates a message and a human interaction record.
    The input will be visible in project/task activity feeds.
    """
    # Verify agent exists
    agent_result = await session.execute(
        select(Agent).where(Agent.agent_id == agent_id)
    )
    agent = agent_result.scalar_one_or_none()

    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    # Create a human interaction record
    interaction = HumanInteraction(
        interaction_id=uuid.uuid4(),
        initiated_by_agent_id="human",  # Special identifier for human
        interaction_type="interruption",
        related_entity_type="agent",
        related_entity_id=None,
        request=f"Human input to {agent.name} ({agent.role})",
        human_response=input_data.input_text,
        status="completed",
        responded_at=datetime.utcnow(),
        meta_data={
            "context": input_data.context,
            "related_project_id": input_data.related_project_id,
            "related_task_id": input_data.related_task_id,
            "target_agent_id": agent_id,
        }
    )
    session.add(interaction)

    # Create a message to the agent
    message = Message(
        message_id=uuid.uuid4(),
        from_agent_id="human",  # Special identifier
        to_agent_id=agent_id,
        content=input_data.input_text,
        message_type=None,
        priority=Priority.HIGH,
        read_status=False,
        related_task_id=uuid.UUID(input_data.related_task_id) if input_data.related_task_id else None,
        related_project_id=uuid.UUID(input_data.related_project_id) if input_data.related_project_id else None,
        meta_data={
            "context": input_data.context,
            "interaction_type": "human_input",
        }
    )
    session.add(message)

    # Create an audit log entry
    audit = AuditLog(
        agent_id="human",
        action="human_input",
        entity_type="agent",
        entity_id=None,
        new_value={
            "target_agent": agent_id,
            "input": input_data.input_text,
            "context": input_data.context,
        },
        meta_data={
            "related_project_id": input_data.related_project_id,
            "related_task_id": input_data.related_task_id,
        }
    )
    session.add(audit)

    await session.commit()

    return {
        "status": "success",
        "message": f"Input delivered to {agent.name}",
        "interaction_id": str(interaction.interaction_id),
        "message_id": str(message.message_id),
    }


# ===== Audit Log Endpoint =====

@router.get("/audit-log", tags=["Audit Log"])
async def get_audit_log(
    agent_id: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    session: AsyncSession = Depends(get_session)
):
    """Get audit log entries."""
    query = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(limit)

    if agent_id:
        query = query.where(AuditLog.actor == agent_id)
    if action:
        query = query.where(AuditLog.action == action)

    result = await session.execute(query)
    logs = result.scalars().all()

    return [
        {
            "log_id": log.log_id,
            "actor": log.actor,
            "action": log.action,
            "entity_type": log.entity_type,
            "entity_id": str(log.entity_id) if log.entity_id else None,
            "old_value": log.old_value,
            "new_value": log.new_value,
            "timestamp": log.timestamp.isoformat(),
            "reason": log.reason,
            "details": log.details if log.details else {},
        }
        for log in logs
    ]


# ===== Include Escalations Router =====
router.include_router(escalations_router)
router.include_router(exports_router)
# Note: exports_v2_router is mounted at /api/v2 in main.py, not here
router.include_router(feedback_router)
router.include_router(cache_router)  # Phase 3: Cache management endpoints
router.include_router(performance_router)  # Phase 3.4: Performance monitoring endpoints
# WebSocket router is now included directly in main.py instead of here
# router.include_router(websocket_router)  # Phase 1: WebSocket real-time activity streaming
router.include_router(task_controls_router)  # Phase 2: User task controls (pause/resume/cancel)
router.include_router(project_learnings_router)  # Phase 2: Project learnings extraction
router.include_router(project_similarity_router)  # Phase 2: Project similarity detection
router.include_router(cross_project_learning_router)  # Phase 4: Cross-project learning and knowledge graph

# ===== Notification Endpoints =====

class NotificationResponse(BaseModel):
    """Response model for notification."""
    notification_id: str
    type: str
    title: str
    message: str
    related_entity_type: Optional[str]
    related_entity_id: Optional[str]
    agent_id: Optional[str]
    agent_name: Optional[str]
    priority: str
    read: bool
    read_at: Optional[str]
    created_at: str
    meta_data: dict


@router.get("/notifications", response_model=List[NotificationResponse], tags=["Notifications"])
async def get_notifications(
    unread_only: bool = Query(default=False, description="Filter to show only unread notifications"),
    limit: int = Query(default=50, le=100),
    session: AsyncSession = Depends(get_session)
):
    """Get user notifications."""
    query = select(Notification).order_by(Notification.created_at.desc()).limit(limit)

    if unread_only:
        query = query.where(Notification.read == False)

    result = await session.execute(query)
    notifications = result.scalars().all()

    # Get agent names for notifications
    response = []
    for notification in notifications:
        agent_name = None
        if notification.agent_id:
            agent_result = await session.execute(
                select(Agent).where(Agent.agent_id == notification.agent_id)
            )
            agent = agent_result.scalar_one_or_none()
            if agent:
                agent_name = agent.name

        response.append(NotificationResponse(
            notification_id=str(notification.notification_id),
            type=notification.type.value,
            title=notification.title,
            message=notification.message,
            related_entity_type=notification.related_entity_type,
            related_entity_id=str(notification.related_entity_id) if notification.related_entity_id else None,
            agent_id=notification.agent_id,
            agent_name=agent_name,
            priority=notification.priority.value,
            read=notification.read,
            read_at=notification.read_at.isoformat() if notification.read_at else None,
            created_at=notification.created_at.isoformat(),
            meta_data=notification.meta_data or {}
        ))

    return response


@router.post("/notifications/{notification_id}/mark-read", tags=["Notifications"])
async def mark_notification_read(
    notification_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Mark a notification as read."""
    result = await session.execute(
        select(Notification).where(Notification.notification_id == notification_id)
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    notification.read = True
    notification.read_at = datetime.utcnow()
    await session.commit()

    return {
        "notification_id": str(notification.notification_id),
        "read": True,
        "read_at": notification.read_at.isoformat()
    }


@router.post("/notifications/mark-all-read", tags=["Notifications"])
async def mark_all_notifications_read(
    session: AsyncSession = Depends(get_session)
):
    """Mark all notifications as read."""
    await session.execute(
        update(Notification)
        .where(Notification.read == False)
        .values(read=True, read_at=datetime.utcnow())
    )
    await session.commit()

    return {"message": "All notifications marked as read"}


@router.delete("/notifications/{notification_id}", tags=["Notifications"])
async def delete_notification(
    notification_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Delete a notification."""
    result = await session.execute(
        select(Notification).where(Notification.notification_id == notification_id)
    )
    notification = result.scalar_one_or_none()

    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")

    await session.delete(notification)
    await session.commit()

    return {"message": "Notification deleted", "notification_id": str(notification_id)}


@router.get("/notifications/unread-count", tags=["Notifications"])
async def get_unread_count(
    session: AsyncSession = Depends(get_session)
):
    """Get count of unread notifications."""
    result = await session.execute(
        select(func.count(Notification.notification_id))
        .where(Notification.read == False)
    )
    count = result.scalar_one()

    return {"unread_count": count}


# ===== Real-Time Event Stream Endpoints =====

from fastapi import WebSocket, WebSocketDisconnect
from app.services.websocket_manager import ws_manager
from app.services.event_service import EventService


@router.websocket("/ws/projects/{project_id}")
async def project_websocket(
    websocket: WebSocket,
    project_id: str
):
    """
    WebSocket endpoint for real-time project updates.
    Streams all agent activities, thoughts, decisions, and handoffs for a specific project.
    """
    try:
        await ws_manager.connect(websocket, project_id=project_id)
    except Exception as e:
        logger.error(f"Failed to connect WebSocket for project {project_id}: {e}")
        return

    try:
        while True:
            # Keep connection alive and handle any incoming messages
            try:
                data = await websocket.receive_text()
            except RuntimeError as e:
                # WebSocket closed or not connected
                logger.warning(f"WebSocket receive error for project {project_id}: {e}")
                break

            # Handle ping/pong or other client messages
            if data == "ping":
                try:
                    await websocket.send_json({"type": "pong"})
                except Exception as e:
                    logger.warning(f"Failed to send pong: {e}")
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for project {project_id}")
    except Exception as e:
        logger.error(f"WebSocket error for project {project_id}: {e}")
    finally:
        ws_manager.disconnect(websocket)


@router.websocket("/ws/agents/{agent_id}")
async def agent_websocket(
    websocket: WebSocket,
    agent_id: str
):
    """
    WebSocket endpoint for real-time agent-specific updates.
    Streams all activities, thoughts, and interactions for a specific agent.
    """
    try:
        await ws_manager.connect(websocket, agent_id=agent_id)
    except Exception as e:
        logger.error(f"Failed to connect WebSocket for agent {agent_id}: {e}")
        return

    try:
        while True:
            try:
                data = await websocket.receive_text()
            except RuntimeError as e:
                logger.warning(f"WebSocket receive error for agent {agent_id}: {e}")
                break

            if data == "ping":
                try:
                    await websocket.send_json({"type": "pong"})
                except Exception as e:
                    logger.warning(f"Failed to send pong: {e}")
                    break

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for agent {agent_id}")
    except Exception as e:
        logger.error(f"WebSocket error for agent {agent_id}: {e}")
    finally:
        ws_manager.disconnect(websocket)


@router.websocket("/ws/stream")
async def global_websocket(
    websocket: WebSocket
):
    """
    WebSocket endpoint for global real-time updates.
    Streams all events across all projects and agents.
    """
    try:
        await ws_manager.connect(websocket, subscribe_all=True)
    except Exception as e:
        logger.error(f"Failed to connect global WebSocket: {e}")
        return

    try:
        while True:
            try:
                data = await websocket.receive_text()
            except RuntimeError as e:
                logger.warning(f"WebSocket receive error (global): {e}")
                break

            if data == "ping":
                try:
                    await websocket.send_json({"type": "pong"})
                except Exception as e:
                    logger.warning(f"Failed to send pong: {e}")
                    break

    except WebSocketDisconnect:
        logger.info("Global WebSocket disconnected")
    except Exception as e:
        logger.error(f"Global WebSocket error: {e}")
    finally:
        ws_manager.disconnect(websocket)


@router.get("/ws/stats", tags=["Real-Time Events"])
async def get_websocket_stats():
    """Get WebSocket connection statistics."""
    return ws_manager.get_stats()


@router.get("/projects/{project_id}/stream", tags=["Real-Time Events"])
async def get_project_event_stream(
    project_id: str,
    limit: int = Query(default=50, le=200),
    session: AsyncSession = Depends(get_session)
):
    """
    Get complete event stream for a project including:
    - Agent activities
    - Agent handoffs
    - Timeline events
    - Pending decisions
    """
    event_service = EventService(session)
    stream = await event_service.get_project_stream(uuid.UUID(project_id), limit=limit)
    
    return {
        "project_id": project_id,
        "activities": [
            {
                "activity_id": str(a.activity_id),
                "agent_id": a.agent_id,
                "activity_type": a.activity_type.value,
                "title": a.title,
                "description": a.description,
                "stage": a.stage,
                "progress_percentage": a.progress_percentage,
                "is_active": a.is_active,
                "created_at": a.created_at.isoformat(),
                "completed_at": a.completed_at.isoformat() if a.completed_at else None,
                "metadata": a.metadata,
            }
            for a in stream["activities"]
        ],
        "handoffs": [
            {
                "handoff_id": str(h.handoff_id),
                "from_agent_id": h.from_agent_id,
                "to_agent_id": h.to_agent_id,
                "handoff_type": h.handoff_type,
                "message": h.message,
                "status": h.status.value,
                "initiated_at": h.initiated_at.isoformat(),
                "received_at": h.received_at.isoformat() if h.received_at else None,
                "completed_at": h.completed_at.isoformat() if h.completed_at else None,
                "attachments": h.attachments,
            }
            for h in stream["handoffs"]
        ],
        "timeline": [
            {
                "event_id": str(e.event_id),
                "agent_id": e.agent_id,
                "event_type": e.event_type,
                "event_category": e.event_category,
                "title": e.title,
                "description": e.description,
                "is_highlight": e.is_highlight,
                "highlight_type": e.highlight_type,
                "event_timestamp": e.event_timestamp.isoformat(),
            }
            for e in stream["timeline"]
        ],
        "pending_decisions": [
            {
                "decision_point_id": str(d.decision_point_id),
                "agent_id": d.agent_id,
                "title": d.title,
                "question": d.question,
                "options": d.options,
                "rationale": d.rationale,
                "impact": d.impact,
                "risk_level": d.risk_level,
                "requires_approval": d.requires_approval,
                "created_at": d.created_at.isoformat(),
            }
            for d in stream["pending_decisions"]
        ],
    }


@router.get("/agents/{agent_id}/stream", tags=["Real-Time Events"])
async def get_agent_event_stream(
    agent_id: str,
    project_id: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    session: AsyncSession = Depends(get_session)
):
    """
    Get complete event stream for an agent including:
    - Current activities
    - Recent thoughts
    - LLM interactions
    """
    event_service = EventService(session)
    project_uuid = uuid.UUID(project_id) if project_id else None
    stream = await event_service.get_agent_stream(agent_id, project_id=project_uuid, limit=limit)
    
    return {
        "agent_id": agent_id,
        "activities": [
            {
                "activity_id": str(a.activity_id),
                "activity_type": a.activity_type.value,
                "title": a.title,
                "description": a.description,
                "stage": a.stage,
                "progress_percentage": a.progress_percentage,
                "is_active": a.is_active,
                "project_id": str(a.project_id) if a.project_id else None,
                "task_id": str(a.task_id) if a.task_id else None,
                "created_at": a.created_at.isoformat(),
            }
            for a in stream["activities"]
        ],
        "thoughts": [
            {
                "thought_id": str(t.thought_id),
                "thought_type": t.thought_type.value,
                "content": t.content,
                "context": t.context,
                "created_at": t.created_at.isoformat(),
            }
            for t in stream["thoughts"]
        ],
        "llm_interactions": [
            {
                "interaction_id": str(i.interaction_id),
                "provider": i.provider.value,
                "model": i.model,
                "prompt": i.prompt[:200] + "..." if len(i.prompt) > 200 else i.prompt,  # Truncate for list view
                "response": i.response[:200] + "..." if i.response and len(i.response) > 200 else i.response,
                "total_tokens": i.total_tokens,
                "latency_ms": i.latency_ms,
                "status": i.status,
                "started_at": i.started_at.isoformat(),
                "completed_at": i.completed_at.isoformat() if i.completed_at else None,
            }
            for i in stream["llm_interactions"]
        ],
    }


@router.get("/projects/{project_id}/activities", tags=["Real-Time Events"])
async def get_project_activities(
    project_id: str,
    limit: int = Query(default=50, le=200),
    activity_type: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    """Get agent activities for a project."""
    from app.db.event_models import ActivityType as ActivityTypeEnum
    
    event_service = EventService(session)
    
    activity_type_enum = None
    if activity_type:
        try:
            activity_type_enum = ActivityTypeEnum[activity_type.upper()]
        except KeyError:
            raise HTTPException(status_code=400, detail=f"Invalid activity type: {activity_type}")
    
    activities = await event_service.get_project_activities(
        uuid.UUID(project_id),
        limit=limit,
        activity_type=activity_type_enum
    )
    
    return [
        {
            "activity_id": str(a.activity_id),
            "agent_id": a.agent_id,
            "activity_type": a.activity_type.value,
            "title": a.title,
            "description": a.description,
            "stage": a.stage,
            "progress_percentage": a.progress_percentage,
            "is_active": a.is_active,
            "task_id": str(a.task_id) if a.task_id else None,
            "created_at": a.created_at.isoformat(),
            "updated_at": a.updated_at.isoformat(),
            "completed_at": a.completed_at.isoformat() if a.completed_at else None,
            "metadata": a.metadata,
        }
        for a in activities
    ]


@router.get("/projects/{project_id}/thoughts", tags=["Real-Time Events"])
async def get_project_thoughts(
    project_id: str,
    agent_id: Optional[str] = None,
    limit: int = Query(default=50, le=200),
    session: AsyncSession = Depends(get_session)
):
    """Get agent thoughts for a project."""
    from sqlalchemy import select, desc
    from app.db.event_models import AgentThought
    
    query = select(AgentThought).where(
        AgentThought.project_id == uuid.UUID(project_id)
    )
    
    if agent_id:
        query = query.where(AgentThought.agent_id == agent_id)
    
    query = query.order_by(desc(AgentThought.created_at)).limit(limit)
    
    result = await session.execute(query)
    thoughts = result.scalars().all()
    
    return [
        {
            "thought_id": str(t.thought_id),
            "agent_id": t.agent_id,
            "thought_type": t.thought_type.value,
            "content": t.content,
            "context": t.context,
            "activity_id": str(t.activity_id) if t.activity_id else None,
            "task_id": str(t.task_id) if t.task_id else None,
            "created_at": t.created_at.isoformat(),
        }
        for t in thoughts
    ]


@router.get("/projects/{project_id}/llm-interactions", tags=["Real-Time Events"])
async def get_project_llm_interactions(
    project_id: str,
    agent_id: Optional[str] = None,
    limit: int = Query(default=20, le=100),
    session: AsyncSession = Depends(get_session)
):
    """Get LLM interactions for a project."""
    event_service = EventService(session)
    
    interactions = await event_service.get_llm_interactions(
        project_id=uuid.UUID(project_id),
        agent_id=agent_id,
        limit=limit
    )
    
    return [
        {
            "interaction_id": str(i.interaction_id),
            "agent_id": i.agent_id,
            "provider": i.provider.value,
            "model": i.model,
            "prompt": i.prompt,
            "system_prompt": i.system_prompt,
            "response": i.response,
            "prompt_tokens": i.prompt_tokens,
            "completion_tokens": i.completion_tokens,
            "total_tokens": i.total_tokens,
            "latency_ms": i.latency_ms,
            "cost": i.cost,
            "status": i.status,
            "error_message": i.error_message,
            "activity_id": str(i.activity_id) if i.activity_id else None,
            "task_id": str(i.task_id) if i.task_id else None,
            "started_at": i.started_at.isoformat(),
            "completed_at": i.completed_at.isoformat() if i.completed_at else None,
        }
        for i in interactions
    ]


@router.get("/projects/{project_id}/handoffs", tags=["Real-Time Events"])
async def get_project_handoffs(
    project_id: str,
    limit: int = Query(default=50, le=200),
    session: AsyncSession = Depends(get_session)
):
    """Get agent handoffs for a project."""
    event_service = EventService(session)
    
    handoffs = await event_service.get_project_handoffs(
        uuid.UUID(project_id),
        limit=limit
    )
    
    return [
        {
            "handoff_id": str(h.handoff_id),
            "from_agent_id": h.from_agent_id,
            "to_agent_id": h.to_agent_id,
            "handoff_type": h.handoff_type,
            "message": h.message,
            "attachments": h.attachments,
            "status": h.status.value,
            "task_id": str(h.task_id) if h.task_id else None,
            "initiated_at": h.initiated_at.isoformat(),
            "received_at": h.received_at.isoformat() if h.received_at else None,
            "completed_at": h.completed_at.isoformat() if h.completed_at else None,
            "response": h.response,
        }
        for h in handoffs
    ]


@router.get("/projects/{project_id}/timeline", tags=["Real-Time Events"])
async def get_project_timeline(
    project_id: str,
    limit: int = Query(default=100, le=500),
    highlights_only: bool = Query(default=False),
    session: AsyncSession = Depends(get_session)
):
    """
    Get project timeline for time travel / replay feature.
    Can filter to show only highlights (key milestones).
    """
    event_service = EventService(session)
    
    timeline = await event_service.get_project_timeline(
        uuid.UUID(project_id),
        limit=limit,
        highlights_only=highlights_only
    )
    
    return [
        {
            "event_id": str(e.event_id),
            "agent_id": e.agent_id,
            "event_type": e.event_type,
            "event_category": e.event_category,
            "title": e.title,
            "description": e.description,
            "is_highlight": e.is_highlight,
            "highlight_type": e.highlight_type,
            "related_activity_id": str(e.related_activity_id) if e.related_activity_id else None,
            "related_task_id": str(e.related_task_id) if e.related_task_id else None,
            "event_timestamp": e.event_timestamp.isoformat(),
        }
        for e in timeline
    ]


@router.get("/projects/{project_id}/decision-points", tags=["Real-Time Events"])
async def get_project_decision_points(
    project_id: str,
    pending_only: bool = Query(default=False),
    session: AsyncSession = Depends(get_session)
):
    """Get decision points for a project."""
    from sqlalchemy import select, desc, and_
    from app.db.event_models import DecisionPoint
    
    query = select(DecisionPoint).where(
        DecisionPoint.project_id == uuid.UUID(project_id)
    )
    
    if pending_only:
        query = query.where(
            and_(
                DecisionPoint.requires_approval == True,
                DecisionPoint.approval_status == "pending"
            )
        )
    
    query = query.order_by(desc(DecisionPoint.created_at))
    
    result = await session.execute(query)
    decisions = result.scalars().all()
    
    return [
        {
            "decision_point_id": str(d.decision_point_id),
            "agent_id": d.agent_id,
            "title": d.title,
            "question": d.question,
            "options": d.options,
            "rationale": d.rationale,
            "pros_cons": d.pros_cons,
            "impact": d.impact,
            "risk_level": d.risk_level,
            "requires_approval": d.requires_approval,
            "approved_by": d.approved_by,
            "approval_status": d.approval_status,
            "chosen_option": d.chosen_option,
            "activity_id": str(d.activity_id) if d.activity_id else None,
            "task_id": str(d.task_id) if d.task_id else None,
            "created_at": d.created_at.isoformat(),
            "decided_at": d.decided_at.isoformat() if d.decided_at else None,
        }
        for d in decisions
    ]


@router.post("/decision-points/{decision_point_id}/approve", tags=["Real-Time Events"])
async def approve_decision_point(
    decision_point_id: str,
    approved_by: str = Query(..., description="Approver identifier (e.g., 'user' or agent_id)"),
    session: AsyncSession = Depends(get_session)
):
    """Approve a pending decision point."""
    event_service = EventService(session)
    
    try:
        decision = await event_service.resolve_decision_point(
            uuid.UUID(decision_point_id),
            chosen_option="approved",
            approved_by=approved_by,
            approval_status="approved"
        )
        
        return {
            "decision_point_id": str(decision.decision_point_id),
            "approval_status": decision.approval_status,
            "approved_by": decision.approved_by,
            "decided_at": decision.decided_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/decision-points/{decision_point_id}/reject", tags=["Real-Time Events"])
async def reject_decision_point(
    decision_point_id: str,
    approved_by: str = Query(..., description="Approver identifier (e.g., 'user' or agent_id)"),
    reason: str = Query(..., description="Reason for rejection"),
    session: AsyncSession = Depends(get_session)
):
    """Reject a pending decision point."""
    event_service = EventService(session)
    
    try:
        decision = await event_service.resolve_decision_point(
            uuid.UUID(decision_point_id),
            chosen_option=f"rejected: {reason}",
            approved_by=approved_by,
            approval_status="rejected"
        )
        
        return {
            "decision_point_id": str(decision.decision_point_id),
            "approval_status": decision.approval_status,
            "approved_by": decision.approved_by,
            "reason": reason,
            "decided_at": decision.decided_at.isoformat()
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ===== System Settings Endpoints =====

from app.db.models import SystemSettings, UserProfile, SettingsAuditLog


class SystemSettingsResponse(BaseModel):
    """Response model for system settings."""
    id: int
    default_llm_model: str
    llm_temperature: int
    llm_max_tokens: int
    show_thinking_process: bool
    context_strategy: str
    default_communication_style: str
    escalation_time_threshold: int
    auto_retry_attempts: int
    agent_autonomy_level: str
    request_caching_enabled: bool
    concurrent_agent_limit: int
    auto_scaling_enabled: bool
    log_level: str
    debug_mode: bool
    auto_backup_enabled: bool
    backup_frequency: str
    advanced_settings: dict
    updated_at: str
    updated_by: Optional[str]


class SystemSettingsUpdate(BaseModel):
    """Request model for updating system settings."""
    default_llm_model: Optional[str] = None
    llm_temperature: Optional[int] = None
    llm_max_tokens: Optional[int] = None
    show_thinking_process: Optional[bool] = None
    context_strategy: Optional[str] = None
    default_communication_style: Optional[str] = None
    escalation_time_threshold: Optional[int] = None
    auto_retry_attempts: Optional[int] = None
    agent_autonomy_level: Optional[str] = None
    request_caching_enabled: Optional[bool] = None
    concurrent_agent_limit: Optional[int] = None
    auto_scaling_enabled: Optional[bool] = None
    log_level: Optional[str] = None
    debug_mode: Optional[bool] = None
    auto_backup_enabled: Optional[bool] = None
    backup_frequency: Optional[str] = None
    advanced_settings: Optional[dict] = None


@router.get("/system-settings", response_model=SystemSettingsResponse, tags=["System Settings"])
async def get_system_settings(session: AsyncSession = Depends(get_session)):
    """Get current system settings. Returns default settings if none exist."""
    result = await session.execute(select(SystemSettings).limit(1))
    settings = result.scalar_one_or_none()
    
    # If no settings exist, create default ones
    if not settings:
        settings = SystemSettings()
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
    
    return SystemSettingsResponse(
        id=settings.id,
        default_llm_model=settings.default_llm_model,
        llm_temperature=settings.llm_temperature,
        llm_max_tokens=settings.llm_max_tokens,
        show_thinking_process=settings.show_thinking_process,
        context_strategy=settings.context_strategy,
        default_communication_style=settings.default_communication_style,
        escalation_time_threshold=settings.escalation_time_threshold,
        auto_retry_attempts=settings.auto_retry_attempts,
        agent_autonomy_level=settings.agent_autonomy_level,
        request_caching_enabled=settings.request_caching_enabled,
        concurrent_agent_limit=settings.concurrent_agent_limit,
        auto_scaling_enabled=settings.auto_scaling_enabled,
        log_level=settings.log_level,
        debug_mode=settings.debug_mode,
        auto_backup_enabled=settings.auto_backup_enabled,
        backup_frequency=settings.backup_frequency,
        advanced_settings=settings.advanced_settings or {},
        updated_at=settings.updated_at.isoformat(),
        updated_by=settings.updated_by,
    )


@router.put("/system-settings", response_model=SystemSettingsResponse, tags=["System Settings"])
async def update_system_settings(
    settings_update: SystemSettingsUpdate,
    updated_by: str = Query(default="admin", description="User making the update"),
    session: AsyncSession = Depends(get_session)
):
    """Update system settings. Only admins should have access to this endpoint."""
    # Get existing settings
    result = await session.execute(select(SystemSettings).limit(1))
    settings = result.scalar_one_or_none()
    
    if not settings:
        # Create new settings if none exist
        settings = SystemSettings()
        session.add(settings)
    
    # Track changes for audit log
    changes = []
    update_data = settings_update.dict(exclude_unset=True)
    
    for field, new_value in update_data.items():
        if new_value is not None:
            old_value = getattr(settings, field)
            if old_value != new_value:
                changes.append({
                    "field": field,
                    "old_value": str(old_value) if old_value is not None else None,
                    "new_value": str(new_value),
                })
                setattr(settings, field, new_value)
    
    settings.updated_by = updated_by
    settings.updated_at = datetime.utcnow()
    
    await session.commit()
    await session.refresh(settings)
    
    # Create audit log entries for each change
    for change in changes:
        audit_log = SettingsAuditLog(
            entity_type="system_settings",
            entity_id=None,
            changed_by_user_id=None,
            changed_by_admin=True,
            field_name=change["field"],
            old_value=change["old_value"],
            new_value=change["new_value"],
        )
        session.add(audit_log)
    
    await session.commit()
    
    return SystemSettingsResponse(
        id=settings.id,
        default_llm_model=settings.default_llm_model,
        llm_temperature=settings.llm_temperature,
        llm_max_tokens=settings.llm_max_tokens,
        show_thinking_process=settings.show_thinking_process,
        context_strategy=settings.context_strategy,
        default_communication_style=settings.default_communication_style,
        escalation_time_threshold=settings.escalation_time_threshold,
        auto_retry_attempts=settings.auto_retry_attempts,
        agent_autonomy_level=settings.agent_autonomy_level,
        request_caching_enabled=settings.request_caching_enabled,
        concurrent_agent_limit=settings.concurrent_agent_limit,
        auto_scaling_enabled=settings.auto_scaling_enabled,
        log_level=settings.log_level,
        debug_mode=settings.debug_mode,
        auto_backup_enabled=settings.auto_backup_enabled,
        backup_frequency=settings.backup_frequency,
        advanced_settings=settings.advanced_settings or {},
        updated_at=settings.updated_at.isoformat(),
        updated_by=settings.updated_by,
    )


# ===== User Profile Endpoints =====

class UserProfileResponse(BaseModel):
    """Response model for user profile."""
    user_id: str
    full_name: str
    display_name: Optional[str]
    email: str
    phone: Optional[str]
    job_title: Optional[str]
    department: Optional[str]
    location: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    pronouns: Optional[str]
    timezone: str
    theme: str
    display_density: str
    font_size: int
    language: str
    animations_enabled: bool
    sidebar_collapsed: bool
    default_landing_page: str
    email_notifications: str
    desktop_notifications: bool
    notification_sounds: bool
    notification_preferences: dict
    show_online_status: bool
    show_last_active: bool
    show_email_in_directory: bool
    activity_broadcasting: bool
    work_start_time: str
    work_end_time: str
    default_task_view: str
    availability_status: str
    connected_accounts: dict
    role: str
    is_admin: bool
    created_at: str
    updated_at: str
    last_login: Optional[str]


class UserProfileCreate(BaseModel):
    """Request model for creating a user profile."""
    full_name: str
    email: str
    password: Optional[str] = None  # For future authentication
    phone: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None


class UserProfileUpdate(BaseModel):
    """Request model for updating user profile."""
    full_name: Optional[str] = None
    display_name: Optional[str] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    location: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    pronouns: Optional[str] = None
    timezone: Optional[str] = None
    theme: Optional[str] = None
    display_density: Optional[str] = None
    font_size: Optional[int] = None
    language: Optional[str] = None
    animations_enabled: Optional[bool] = None
    sidebar_collapsed: Optional[bool] = None
    default_landing_page: Optional[str] = None
    email_notifications: Optional[str] = None
    desktop_notifications: Optional[bool] = None
    notification_sounds: Optional[bool] = None
    notification_preferences: Optional[dict] = None
    show_online_status: Optional[bool] = None
    show_last_active: Optional[bool] = None
    show_email_in_directory: Optional[bool] = None
    activity_broadcasting: Optional[bool] = None
    work_start_time: Optional[str] = None
    work_end_time: Optional[str] = None
    default_task_view: Optional[str] = None
    availability_status: Optional[str] = None
    connected_accounts: Optional[dict] = None


@router.post("/profiles", response_model=UserProfileResponse, status_code=201, tags=["User Profiles"])
async def create_user_profile(
    profile: UserProfileCreate,
    session: AsyncSession = Depends(get_session)
):
    """Create a new user profile."""
    # Check if email already exists
    result = await session.execute(
        select(UserProfile).where(UserProfile.email == profile.email)
    )
    existing = result.scalar_one_or_none()
    
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    new_profile = UserProfile(
        user_id=uuid.uuid4(),
        full_name=profile.full_name,
        email=profile.email,
        phone=profile.phone,
        job_title=profile.job_title,
        department=profile.department,
    )
    
    session.add(new_profile)
    await session.commit()
    await session.refresh(new_profile)
    
    return UserProfileResponse(
        user_id=str(new_profile.user_id),
        full_name=new_profile.full_name,
        display_name=new_profile.display_name,
        email=new_profile.email,
        phone=new_profile.phone,
        job_title=new_profile.job_title,
        department=new_profile.department,
        location=new_profile.location,
        bio=new_profile.bio,
        avatar_url=new_profile.avatar_url,
        pronouns=new_profile.pronouns,
        timezone=new_profile.timezone,
        theme=new_profile.theme,
        display_density=new_profile.display_density,
        font_size=new_profile.font_size,
        language=new_profile.language,
        animations_enabled=new_profile.animations_enabled,
        sidebar_collapsed=new_profile.sidebar_collapsed,
        default_landing_page=new_profile.default_landing_page,
        email_notifications=new_profile.email_notifications,
        desktop_notifications=new_profile.desktop_notifications,
        notification_sounds=new_profile.notification_sounds,
        notification_preferences=new_profile.notification_preferences or {},
        show_online_status=new_profile.show_online_status,
        show_last_active=new_profile.show_last_active,
        show_email_in_directory=new_profile.show_email_in_directory,
        activity_broadcasting=new_profile.activity_broadcasting,
        work_start_time=new_profile.work_start_time,
        work_end_time=new_profile.work_end_time,
        default_task_view=new_profile.default_task_view,
        availability_status=new_profile.availability_status,
        connected_accounts=new_profile.connected_accounts or {},
        role=new_profile.role,
        is_admin=new_profile.is_admin,
        created_at=new_profile.created_at.isoformat(),
        updated_at=new_profile.updated_at.isoformat(),
        last_login=new_profile.last_login.isoformat() if new_profile.last_login else None,
    )


@router.get("/profiles/{user_id}", response_model=UserProfileResponse, tags=["User Profiles"])
async def get_user_profile(
    user_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get user profile by ID."""
    result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    return UserProfileResponse(
        user_id=str(profile.user_id),
        full_name=profile.full_name,
        display_name=profile.display_name,
        email=profile.email,
        phone=profile.phone,
        job_title=profile.job_title,
        department=profile.department,
        location=profile.location,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        pronouns=profile.pronouns,
        timezone=profile.timezone,
        theme=profile.theme,
        display_density=profile.display_density,
        font_size=profile.font_size,
        language=profile.language,
        animations_enabled=profile.animations_enabled,
        sidebar_collapsed=profile.sidebar_collapsed,
        default_landing_page=profile.default_landing_page,
        email_notifications=profile.email_notifications,
        desktop_notifications=profile.desktop_notifications,
        notification_sounds=profile.notification_sounds,
        notification_preferences=profile.notification_preferences or {},
        show_online_status=profile.show_online_status,
        show_last_active=profile.show_last_active,
        show_email_in_directory=profile.show_email_in_directory,
        activity_broadcasting=profile.activity_broadcasting,
        work_start_time=profile.work_start_time,
        work_end_time=profile.work_end_time,
        default_task_view=profile.default_task_view,
        availability_status=profile.availability_status,
        connected_accounts=profile.connected_accounts or {},
        role=profile.role,
        is_admin=profile.is_admin,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat(),
        last_login=profile.last_login.isoformat() if profile.last_login else None,
    )


@router.put("/profiles/{user_id}", response_model=UserProfileResponse, tags=["User Profiles"])
async def update_user_profile(
    user_id: str,
    profile_update: UserProfileUpdate,
    session: AsyncSession = Depends(get_session)
):
    """Update user profile."""
    result = await session.execute(
        select(UserProfile).where(UserProfile.user_id == user_id)
    )
    profile = result.scalar_one_or_none()
    
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")
    
    # Track changes for audit log
    changes = []
    update_data = profile_update.dict(exclude_unset=True)
    
    for field, new_value in update_data.items():
        if new_value is not None:
            old_value = getattr(profile, field)
            if old_value != new_value:
                changes.append({
                    "field": field,
                    "old_value": str(old_value) if old_value is not None else None,
                    "new_value": str(new_value) if not isinstance(new_value, dict) else str(new_value),
                })
                setattr(profile, field, new_value)
    
    profile.updated_at = datetime.utcnow()
    
    await session.commit()
    await session.refresh(profile)
    
    # Create audit log entries for each change
    for change in changes:
        audit_log = SettingsAuditLog(
            entity_type="user_profile",
            entity_id=str(user_id),
            changed_by_user_id=uuid.UUID(user_id),
            changed_by_admin=False,
            field_name=change["field"],
            old_value=change["old_value"],
            new_value=change["new_value"],
        )
        session.add(audit_log)
    
    await session.commit()
    
    return UserProfileResponse(
        user_id=str(profile.user_id),
        full_name=profile.full_name,
        display_name=profile.display_name,
        email=profile.email,
        phone=profile.phone,
        job_title=profile.job_title,
        department=profile.department,
        location=profile.location,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        pronouns=profile.pronouns,
        timezone=profile.timezone,
        theme=profile.theme,
        display_density=profile.display_density,
        font_size=profile.font_size,
        language=profile.language,
        animations_enabled=profile.animations_enabled,
        sidebar_collapsed=profile.sidebar_collapsed,
        default_landing_page=profile.default_landing_page,
        email_notifications=profile.email_notifications,
        desktop_notifications=profile.desktop_notifications,
        notification_sounds=profile.notification_sounds,
        notification_preferences=profile.notification_preferences or {},
        show_online_status=profile.show_online_status,
        show_last_active=profile.show_last_active,
        show_email_in_directory=profile.show_email_in_directory,
        activity_broadcasting=profile.activity_broadcasting,
        work_start_time=profile.work_start_time,
        work_end_time=profile.work_end_time,
        default_task_view=profile.default_task_view,
        availability_status=profile.availability_status,
        connected_accounts=profile.connected_accounts or {},
        role=profile.role,
        is_admin=profile.is_admin,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat(),
        last_login=profile.last_login.isoformat() if profile.last_login else None,
    )


@router.get("/profiles", response_model=List[UserProfileResponse], tags=["User Profiles"])
async def list_user_profiles(
    limit: int = Query(default=50, le=100),
    session: AsyncSession = Depends(get_session)
):
    """List all user profiles."""
    result = await session.execute(
        select(UserProfile).order_by(UserProfile.created_at.desc()).limit(limit)
    )
    profiles = result.scalars().all()
    
    return [
        UserProfileResponse(
            user_id=str(p.user_id),
            full_name=p.full_name,
            display_name=p.display_name,
            email=p.email,
            phone=p.phone,
            job_title=p.job_title,
            department=p.department,
            location=p.location,
            bio=p.bio,
            avatar_url=p.avatar_url,
            pronouns=p.pronouns,
            timezone=p.timezone,
            theme=p.theme,
            display_density=p.display_density,
            font_size=p.font_size,
            language=p.language,
            animations_enabled=p.animations_enabled,
            sidebar_collapsed=p.sidebar_collapsed,
            default_landing_page=p.default_landing_page,
            email_notifications=p.email_notifications,
            desktop_notifications=p.desktop_notifications,
            notification_sounds=p.notification_sounds,
            notification_preferences=p.notification_preferences or {},
            show_online_status=p.show_online_status,
            show_last_active=p.show_last_active,
            show_email_in_directory=p.show_email_in_directory,
            activity_broadcasting=p.activity_broadcasting,
            work_start_time=p.work_start_time,
            work_end_time=p.work_end_time,
            default_task_view=p.default_task_view,
            availability_status=p.availability_status,
            connected_accounts=p.connected_accounts or {},
            role=p.role,
            is_admin=p.is_admin,
            created_at=p.created_at.isoformat(),
            updated_at=p.updated_at.isoformat(),
            last_login=p.last_login.isoformat() if p.last_login else None,
        )
        for p in profiles
    ]


# ===== Settings Audit Log Endpoints =====

@router.get("/settings-audit-log", tags=["Settings Audit"])
async def get_settings_audit_log(
    entity_type: Optional[str] = Query(default=None, description="Filter by entity type: system_settings or user_profile"),
    entity_id: Optional[str] = Query(default=None, description="Filter by specific entity ID (user_id for profiles)"),
    limit: int = Query(default=100, le=500),
    session: AsyncSession = Depends(get_session)
):
    """Get settings audit log."""
    query = select(SettingsAuditLog).order_by(SettingsAuditLog.timestamp.desc()).limit(limit)
    
    if entity_type:
        query = query.where(SettingsAuditLog.entity_type == entity_type)
    if entity_id:
        query = query.where(SettingsAuditLog.entity_id == entity_id)
    
    result = await session.execute(query)
    logs = result.scalars().all()
    
    return [
        {
            "log_id": log.log_id,
            "entity_type": log.entity_type,
            "entity_id": log.entity_id,
            "changed_by_user_id": str(log.changed_by_user_id) if log.changed_by_user_id else None,
            "changed_by_admin": log.changed_by_admin,
            "field_name": log.field_name,
            "old_value": log.old_value,
            "new_value": log.new_value,
            "change_reason": log.change_reason,
            "ip_address": log.ip_address,
            "user_agent": log.user_agent,
            "timestamp": log.timestamp.isoformat(),
            "meta_data": log.meta_data or {},
        }
        for log in logs
    ]
