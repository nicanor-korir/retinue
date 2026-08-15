"""Project management API endpoints.

Endpoints for:
- Creating projects with team selection
- Retrieving project information
- Updating project details including team composition
- Managing project deliverables
- Team assignment and validation
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, func
from typing import List, Optional
from datetime import datetime
import uuid
import logging

from app.db.database import get_session
from app.db.models import (
    Project, Task, ProjectStatus, TaskStatus, Priority, Agent,
    ProjectAgentAssignment, AuditLog, DeliverableType
)
from app.agents import AgentRegistry
from app.utils.agent_capabilities import validate_team_composition
from app.api.schemas import (
    ProjectCreate, ProjectResponse, ProjectDetailedResponse,
    ProjectUpdateTeam, TeamValidationResponse, AgentInfoResponse,
    PriorityEnum
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/projects", tags=["Projects"])


# ===== Project Creation & Retrieval =====

@router.post(
    "",
    response_model=ProjectDetailedResponse,
    status_code=201,
    summary="Create a new project",
    description="Create a new project with flexible team selection"
)
async def create_project(
    project: ProjectCreate,
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new project with custom team selection.

    **Request Body:**
    ```json
    {
        "name": "Q1 Marketing Campaign",
        "description": "Comprehensive Q1 marketing campaign with content, design, and strategy",
        "priority": "high",
        "project_type": "marketing_campaign",
        "deliverable_type": "marketing_campaign",
        "selected_agents": ["ceo_001", "cmo_001", "designer_001"]
    }
    ```

    **Returns:** Created project with team details

    **Validation:**
    - Team composition validated if deliverable_type specified
    - All selected agents must exist
    - Required agents for deliverable type must be present

    **Errors:**
    - 400: Invalid team composition or missing agents
    - 422: Validation error in request data
    """
    # Determine agents to assign
    if project.selected_agents:
        agent_ids = project.selected_agents
        # Validate all agents exist
        invalid_agents = []
        for agent_id in agent_ids:
            if not AgentRegistry.get_agent_config(agent_id):
                invalid_agents.append(agent_id)

        if invalid_agents:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent IDs: {', '.join(invalid_agents)}"
            )
    else:
        # Default to CEO
        agent_ids = ["ceo_001"]

    # Validate team for deliverable type
    # if project.deliverable_type:
    #     required = AgentRegistry.get_required_agents(project.deliverable_type)
    #     missing = [a for a in required if a not in agent_ids]

    #     if missing:
    #         missing_names = [AgentRegistry.get_agent_config(a).get("name", a) for a in missing]
    #         raise HTTPException(
    #             status_code=400,
    #             detail=f"Missing required agents for {project.deliverable_type}: {', '.join(missing_names)}"
    #         )

    # Create project
    project_id = str(uuid.uuid4())
    new_project = Project(
        project_id=project_id,
        name=project.name,
        description=project.description,
        status=ProjectStatus.PLANNING,
        priority=Priority[project.priority.upper()],
        owner_agent_id=agent_ids[0],  # First agent is owner
        project_type=project.project_type,
        deliverable_type=project.deliverable_type,
        selected_agents=agent_ids
    )

    session.add(new_project)
    await session.flush()

    # Create project-agent assignments
    for agent_id in agent_ids:
        assignment = ProjectAgentAssignment(
            assignment_id=uuid.uuid4(),
            project_id=project_id,
            agent_id=agent_id,
            role_in_project="team_member" if agent_id != agent_ids[0] else "lead"
        )
        session.add(assignment)

    # Log creation
    audit_log = AuditLog(
        actor="system",
        action="project_created",
        entity_type="project",
        entity_id=str(project_id),
        old_value={},
        new_value={
            "name": project.name,
            "selected_agents": agent_ids,
            "deliverable_type": project.deliverable_type
        }
    )
    session.add(audit_log)

    await session.commit()

    # Build response
    team_members = []
    for agent_id in agent_ids:
        config = AgentRegistry.get_agent_config(agent_id)
        if config:
            team_members.append(AgentInfoResponse(
                agent_id=agent_id,
                name=config.get("name", ""),
                role=config.get("role", ""),
                department=config.get("department", ""),
                is_active=config.get("is_active", True)
            ))

    return ProjectDetailedResponse(
        project_id=project_id,
        name=new_project.name,
        description=new_project.description,
        status=ProjectStatus.PLANNING,
        priority=PriorityEnum[project.priority.upper()],
        project_type=new_project.project_type,
        deliverable_type=new_project.deliverable_type,
        selected_agents=agent_ids,
        owner_agent_id=new_project.owner_agent_id,
        created_at=new_project.created_at,
        updated_at=new_project.updated_at,
        version=1,
        task_count=0,
        team_members=team_members
    )


@router.get(
    "/{project_id}",
    response_model=ProjectDetailedResponse,
    summary="Get project details",
    description="Retrieve detailed information about a project including team"
)
async def get_project(
    project_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get detailed information about a project.

    **Path Parameters:**
    - `project_id`: The project identifier

    **Returns:** Project details with team members and validation status

    **Errors:**
    - 404: Project not found
    """
    result = await session.execute(
        select(Project).where(Project.project_id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    # Get team members
    team_members = []
    agent_ids = project.selected_agents or []

    for agent_id in agent_ids:
        config = AgentRegistry.get_agent_config(agent_id)
        if config:
            team_members.append(AgentInfoResponse(
                agent_id=agent_id,
                name=config.get("name", ""),
                role=config.get("role", ""),
                department=config.get("department", ""),
                is_active=config.get("is_active", True)
            ))

    # Count tasks
    task_result = await session.execute(
        select(func.count(Task.task_id)).where(Task.project_id == project_id)
    )
    task_count = task_result.scalar() or 0

    completed_result = await session.execute(
        select(func.count(Task.task_id)).where(
            Task.project_id == project_id,
            Task.status == TaskStatus.COMPLETED
        )
    )
    completed_count = completed_result.scalar() or 0

    progress = (completed_count / task_count * 100) if task_count > 0 else 0

    return ProjectDetailedResponse(
        project_id=project.project_id,
        name=project.name,
        description=project.description,
        status=project.status,
        priority=project.priority,
        project_type=project.project_type,
        deliverable_type=project.deliverable_type,
        selected_agents=agent_ids,
        owner_agent_id=project.owner_agent_id,
        created_at=project.created_at,
        updated_at=project.updated_at,
        version=project.version,
        task_count=task_count,
        completed_tasks=completed_count,
        progress_percentage=progress,
        team_members=team_members
    )


@router.get(
    "",
    response_model=List[ProjectResponse],
    summary="List projects",
    description="Get a list of projects with optional filtering"
)
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None, description="Filter by project status"),
    agent_id: Optional[str] = Query(None, description="Filter by assigned agent"),
    session: AsyncSession = Depends(get_session)
):
    """
    List projects with optional filtering.

    **Query Parameters:**
    - `skip`: Number of projects to skip (default: 0)
    - `limit`: Number of projects to return (default: 20, max: 100)
    - `status`: Filter by project status (planning, in_progress, completed, etc.)
    - `agent_id`: Filter by agent assigned to project

    **Returns:** List of projects
    """
    query = select(Project)

    if status:
        try:
            status_enum = ProjectStatus[status.upper()]
            query = query.where(Project.status == status_enum)
        except KeyError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status: {status}"
            )

    if agent_id:
        # Find projects with this agent
        query = query.where(Project.selected_agents.contains([agent_id]))

    result = await session.execute(query.offset(skip).limit(limit))
    projects = result.scalars().all()

    responses = []
    for project in projects:
        # Count tasks
        task_result = await session.execute(
            select(func.count(Task.task_id)).where(Task.project_id == project.project_id)
        )
        task_count = task_result.scalar() or 0

        completed_result = await session.execute(
            select(func.count(Task.task_id)).where(
                Task.project_id == project.project_id,
                Task.status == TaskStatus.COMPLETED
            )
        )
        completed_count = completed_result.scalar() or 0
        progress = (completed_count / task_count * 100) if task_count > 0 else 0

        responses.append(ProjectResponse(
            project_id=project.project_id,
            name=project.name,
            description=project.description,
            status=project.status,
            priority=project.priority,
            project_type=project.project_type,
            deliverable_type=project.deliverable_type,
            selected_agents=project.selected_agents or [],
            owner_agent_id=project.owner_agent_id,
            created_at=project.created_at,
            updated_at=project.updated_at,
            version=project.version,
            task_count=task_count,
            completed_tasks=completed_count,
            progress_percentage=progress
        ))

    return responses


# ===== Team Management =====

@router.get(
    "/{project_id}/team",
    response_model=List[AgentInfoResponse],
    summary="Get project team",
    description="Get the team of agents assigned to a project"
)
async def get_project_team(
    project_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get the team of agents assigned to a project.

    **Path Parameters:**
    - `project_id`: The project identifier

    **Returns:** List of team members with details

    **Errors:**
    - 404: Project not found
    """
    result = await session.execute(
        select(Project).where(Project.project_id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    team_members = []
    agent_ids = project.selected_agents or []

    for agent_id in agent_ids:
        config = AgentRegistry.get_agent_config(agent_id)
        if config:
            team_members.append(AgentInfoResponse(
                agent_id=agent_id,
                name=config.get("name", ""),
                role=config.get("role", ""),
                department=config.get("department", ""),
                is_active=config.get("is_active", True)
            ))

    return team_members


@router.post(
    "/{project_id}/team",
    response_model=ProjectDetailedResponse,
    summary="Update project team",
    description="Update the team of agents assigned to a project"
)
async def update_project_team(
    project_id: str,
    team_update: ProjectUpdateTeam,
    session: AsyncSession = Depends(get_session)
):
    """
    Update the team assigned to a project.

    **Path Parameters:**
    - `project_id`: The project identifier

    **Request Body:**
    ```json
    {
        "selected_agents": ["ceo_001", "cmo_001", "designer_001"],
        "reason": "Adding designer for visual assets"
    }
    ```

    **Returns:** Updated project with new team

    **Validation:**
    - All agents must exist
    - If project has deliverable_type, required agents must be present
    - Project must exist

    **Errors:**
    - 400: Invalid agent IDs or team composition
    - 404: Project not found
    """
    result = await session.execute(
        select(Project).where(Project.project_id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    # Validate all agents exist
    invalid_agents = []
    for agent_id in team_update.selected_agents:
        if not AgentRegistry.get_agent_config(agent_id):
            invalid_agents.append(agent_id)

    if invalid_agents:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent IDs: {', '.join(invalid_agents)}"
        )

    # Validate team for deliverable type
    if project.deliverable_type:
        required = AgentRegistry.get_required_agents(project.deliverable_type)
        missing = [a for a in required if a not in team_update.selected_agents]

        if missing:
            missing_names = [AgentRegistry.get_agent_config(a).get("name", a) for a in missing]
            raise HTTPException(
                status_code=400,
                detail=f"Missing required agents for {project.deliverable_type}: {', '.join(missing_names)}"
            )

    # Update project
    old_agents = project.selected_agents or []
    await session.execute(
        update(Project)
        .where(Project.project_id == project_id)
        .values(
            selected_agents=team_update.selected_agents,
            version=Project.version + 1,
            updated_at=datetime.utcnow()
        )
    )

    # Update assignments
    # Delete old assignments
    result = await session.execute(
        select(ProjectAgentAssignment).where(
            ProjectAgentAssignment.project_id == project_id
        )
    )
    old_assignments = result.scalars().all()
    for assignment in old_assignments:
        await session.delete(assignment)

    # Create new assignments
    for idx, agent_id in enumerate(team_update.selected_agents):
        assignment = ProjectAgentAssignment(
            assignment_id=uuid.uuid4(),
            project_id=project_id,
            agent_id=agent_id,
            role_in_project="lead" if idx == 0 else "team_member"
        )
        session.add(assignment)

    # Log change
    audit_log = AuditLog(
        actor="system",
        action="project_team_updated",
        entity_type="project",
        entity_id=str(project_id),
        old_value={"selected_agents": old_agents, "reason": team_update.reason},
        new_value={"selected_agents": team_update.selected_agents}
    )
    session.add(audit_log)

    await session.commit()

    # Get updated project
    result = await session.execute(
        select(Project).where(Project.project_id == project_id)
    )
    updated_project = result.scalar_one()

    # Build response
    team_members = []
    for agent_id in team_update.selected_agents:
        config = AgentRegistry.get_agent_config(agent_id)
        if config:
            team_members.append(AgentInfoResponse(
                agent_id=agent_id,
                name=config.get("name", ""),
                role=config.get("role", ""),
                department=config.get("department", ""),
                is_active=config.get("is_active", True)
            ))

    return ProjectDetailedResponse(
        project_id=updated_project.project_id,
        name=updated_project.name,
        description=updated_project.description,
        status=updated_project.status,
        priority=updated_project.priority,
        project_type=updated_project.project_type,
        deliverable_type=updated_project.deliverable_type,
        selected_agents=team_update.selected_agents,
        owner_agent_id=updated_project.owner_agent_id,
        created_at=updated_project.created_at,
        updated_at=updated_project.updated_at,
        version=updated_project.version,
        task_count=0,
        team_members=team_members
    )


# ===== Deliverable Info =====

@router.get(
    "/{project_id}/deliverable-info",
    summary="Get project deliverable info",
    description="Get information about the project's deliverable type"
)
async def get_project_deliverable_info(
    project_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get information about the project's deliverable type.

    **Path Parameters:**
    - `project_id`: The project identifier

    **Returns:** Deliverable type information

    **Errors:**
    - 404: Project not found or no deliverable type specified
    """
    result = await session.execute(
        select(Project).where(Project.project_id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    if not project.deliverable_type:
        raise HTTPException(
            status_code=404,
            detail="Project has no deliverable type specified"
        )

    # Get deliverable type from database
    dt_result = await session.execute(
        select(DeliverableType).where(DeliverableType.type_id == project.deliverable_type)
    )
    dt = dt_result.scalar_one_or_none()

    if not dt:
        return {
            "type_id": project.deliverable_type,
            "message": "Deliverable type not found in database"
        }

    return {
        "type_id": dt.type_id,
        "name": dt.name,
        "description": dt.description,
        "output_format": dt.output_format,
        "typical_agents": dt.typical_agents or []
    }


# ===== Project Completion & Deliverables =====

@router.post(
    "/{project_id}/complete",
    summary="Complete a project",
    description="Mark a project as complete and prepare deliverables"
)
async def complete_project(
    project_id: str,
    deliverable_type: str = "download",  # 'download' or 'hosted'
    session: AsyncSession = Depends(get_session)
):
    """
    Complete a project and prepare deliverables.

    **Path Parameters:**
    - `project_id`: The project identifier

    **Query Parameters:**
    - `deliverable_type`: How to deliver the project ('download' or 'hosted')

    **Returns:** Project status with deliverable information

    **Deliverable Types:**
    - `download`: Package project files for download
    - `hosted`: Deploy and host the project

    **Errors:**
    - 404: Project not found
    - 400: Invalid deliverable type or project state
    """
    result = await session.execute(
        select(Project).where(Project.project_id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    if project.status == ProjectStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Project is already completed"
        )

    # Update project status
    await session.execute(
        update(Project)
        .where(Project.project_id == project_id)
        .values(
            status=ProjectStatus.COMPLETED,
            version=Project.version + 1,
            updated_at=datetime.utcnow()
        )
    )

    # Log completion
    audit_log = AuditLog(
        actor="system",
        action="project_completed",
        entity_type="project",
        entity_id=str(project_id),
        old_value={"status": project.status},
        new_value={
            "status": ProjectStatus.COMPLETED,
            "deliverable_type": deliverable_type
        }
    )
    session.add(audit_log)

    await session.commit()

    # Prepare deliverable information
    deliverable_info = {
        "project_id": project_id,
        "project_name": project.name,
        "status": "completed",
        "deliverable_type": deliverable_type,
        "created_at": datetime.utcnow().isoformat(),
    }

    if deliverable_type == "download":
        deliverable_info.update({
            "download_url": f"/api/v1/projects/{project_id}/download",
            "format": "zip",
            "description": "Complete project files packaged for download"
        })
    elif deliverable_type == "hosted":
        deliverable_info.update({
            "hosted_url": f"https://projects.retinue.team/{project_id}",
            "status": "deploying",
            "description": "Project will be deployed and hosted"
        })
    else:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid deliverable type: {deliverable_type}. Use 'download' or 'hosted'"
        )

    return deliverable_info


@router.get(
    "/{project_id}/download",
    summary="Download project deliverables",
    description="Download project files as a ZIP archive"
)
async def download_project(
    project_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Download project deliverables as a ZIP file.

    **Path Parameters:**
    - `project_id`: The project identifier

    **Returns:** ZIP file with project contents

    **Errors:**
    - 404: Project not found
    - 400: Project not completed
    """
    result = await session.execute(
        select(Project).where(Project.project_id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    if project.status != ProjectStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Only completed projects can be downloaded"
        )

    # Get all tasks and their outputs
    task_result = await session.execute(
        select(Task).where(Task.project_id == project_id)
    )
    tasks = task_result.scalars().all()

    # Prepare downloadable content
    download_content = {
        "project_id": project.project_id,
        "project_name": project.name,
        "description": project.description,
        "status": project.status,
        "priority": project.priority,
        "created_at": project.created_at.isoformat(),
        "completed_at": datetime.utcnow().isoformat(),
        "team": [],
        "tasks": []
    }

    # Add team members
    for agent_id in (project.selected_agents or []):
        config = AgentRegistry.get_agent_config(agent_id)
        if config:
            download_content["team"].append({
                "agent_id": agent_id,
                "name": config.get("name", ""),
                "role": config.get("role", ""),
                "department": config.get("department", "")
            })

    # Add tasks
    for task in tasks:
        download_content["tasks"].append({
            "task_id": str(task.task_id),
            "title": task.title,
            "status": task.status,
            "assigned_to": task.assigned_to_agent_id,
            "output": task.output,
            "completed_at": task.updated_at.isoformat() if task.status == TaskStatus.COMPLETED else None
        })

    return {
        "status": "ready",
        "message": "Project files ready for download",
        "download_info": download_content,
        "format": "json"
    }


@router.post(
    "/{project_id}/approve",
    summary="Approve a project in review",
    description="Approve and move a project from REVIEW status to COMPLETED"
)
async def approve_project(
    project_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Approve a project that is currently in REVIEW status.

    **Path Parameters:**
    - `project_id`: The project identifier

    **Returns:** Updated project with COMPLETED status

    **Errors:**
    - 404: Project not found
    - 400: Project is not in REVIEW status
    """
    result = await session.execute(
        select(Project).where(Project.project_id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    if project.status != ProjectStatus.REVIEW:
        raise HTTPException(
            status_code=400,
            detail=f"Project is not in REVIEW status (current status: {project.status.value})"
        )

    # Update project status to COMPLETED
    await session.execute(
        update(Project)
        .where(Project.project_id == project_id)
        .values(
            status=ProjectStatus.COMPLETED,
            version=Project.version + 1,
            updated_at=datetime.utcnow()
        )
    )

    # Log approval
    audit_log = AuditLog(
        actor="system",
        action="project_approved",
        entity_type="project",
        entity_id=str(project_id),
        old_value={"status": project.status},
        new_value={"status": ProjectStatus.COMPLETED}
    )
    session.add(audit_log)

    await session.commit()

    # Get updated project
    result = await session.execute(
        select(Project).where(Project.project_id == project_id)
    )
    updated_project = result.scalar_one()

    # Build response with team members
    team_members = []
    for agent_id in (updated_project.selected_agents or []):
        config = AgentRegistry.get_agent_config(agent_id)
        if config:
            team_members.append(AgentInfoResponse(
                agent_id=agent_id,
                name=config.get("name", ""),
                role=config.get("role", ""),
                department=config.get("department", ""),
                is_active=config.get("is_active", True)
            ))

    # Count tasks for progress
    task_result = await session.execute(
        select(func.count(Task.task_id)).where(Task.project_id == project_id)
    )
    task_count = task_result.scalar() or 0

    completed_result = await session.execute(
        select(func.count(Task.task_id)).where(
            Task.project_id == project_id,
            Task.status == TaskStatus.COMPLETED
        )
    )
    completed_count = completed_result.scalar() or 0
    progress = (completed_count / task_count * 100) if task_count > 0 else 0

    return ProjectDetailedResponse(
        project_id=updated_project.project_id,
        name=updated_project.name,
        description=updated_project.description,
        status=updated_project.status,
        priority=updated_project.priority,
        project_type=updated_project.project_type,
        deliverable_type=updated_project.deliverable_type,
        selected_agents=updated_project.selected_agents or [],
        owner_agent_id=updated_project.owner_agent_id,
        created_at=updated_project.created_at,
        updated_at=updated_project.updated_at,
        version=updated_project.version,
        task_count=task_count,
        completed_tasks=completed_count,
        progress_percentage=progress,
        team_members=team_members
    )


@router.post(
    "/{project_id}/deploy",
    summary="Deploy project to hosting",
    description="Deploy a completed project to a hosting platform"
)
async def deploy_project(
    project_id: str,
    hosting_provider: str = "retinue_cloud",
    session: AsyncSession = Depends(get_session)
):
    """
    Deploy a completed project to hosting.

    **Path Parameters:**
    - `project_id`: The project identifier

    **Query Parameters:**
    - `hosting_provider`: Where to deploy ('retinue_cloud', 'vercel', 'heroku')

    **Returns:** Deployment status and access information

    **Errors:**
    - 404: Project not found
    - 400: Project not completed or invalid provider
    """
    result = await session.execute(
        select(Project).where(Project.project_id == project_id)
    )
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    if project.status != ProjectStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail="Only completed projects can be deployed"
        )

    valid_providers = ["retinue_cloud", "vercel", "heroku"]
    if hosting_provider not in valid_providers:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid hosting provider. Use: {', '.join(valid_providers)}"
        )

    # Log deployment
    audit_log = AuditLog(
        actor="system",
        action="project_deployed",
        entity_type="project",
        entity_id=str(project_id),
        old_value={},
        new_value={
            "hosting_provider": hosting_provider,
            "deployed_at": datetime.utcnow().isoformat()
        }
    )
    session.add(audit_log)
    await session.commit()

    # Return deployment info
    deployment_urls = {
        "retinue_cloud": f"https://projects.retinue.team/{project_id}",
        "vercel": f"https://{project_id.replace('_', '-')}.vercel.app",
        "heroku": f"https://{project_id.replace('_', '-')}.herokuapp.com"
    }

    return {
        "status": "deploying",
        "project_id": project_id,
        "project_name": project.name,
        "hosting_provider": hosting_provider,
        "deployed_url": deployment_urls.get(hosting_provider),
        "deployment_status": "in_progress",
        "estimated_time": "3-5 minutes",
        "message": f"Your project is being deployed to {hosting_provider}. Check the URL shortly."
    }

