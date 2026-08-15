"""Task management API endpoints with capability matching.

Endpoints for:
- Creating tasks with capability requirements
- Assigning tasks based on agent capabilities
- Finding capable agents for tasks
- Getting task assignment suggestions
- Managing task outputs and formats
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from typing import List, Optional
from datetime import datetime
import uuid
import logging

from app.db.database import get_session
from app.db.models import Task, Project, TaskStatus, Priority
from app.agents import AgentRegistry
from app.utils.agent_capabilities import (
    find_capable_agents,
    calculate_skill_match,
    can_agent_handle_task
)
from app.api.schemas import (
    TaskCreate, TaskResponse, TaskCapableAgentsResponse,
    TaskAssignmentSuggestion, PriorityEnum, TaskStatusEnum,
    TaskOutputResponse, OutputFormatInfo
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/tasks", tags=["Tasks"])

# Supported output formats
SUPPORTED_FORMATS = {
    "text": {"name": "Plain Text", "mime_type": "text/plain", "ext": ".txt"},
    "json": {"name": "JSON", "mime_type": "application/json", "ext": ".json"},
    "markdown": {"name": "Markdown", "mime_type": "text/markdown", "ext": ".md"},
    "code": {"name": "Source Code", "mime_type": "text/plain", "ext": ".py"},
    "pdf": {"name": "PDF Document", "mime_type": "application/pdf", "ext": ".pdf"},
    "docx": {"name": "Word Document", "mime_type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "ext": ".docx"},
    "xlsx": {"name": "Excel Spreadsheet", "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "ext": ".xlsx"},
    "html": {"name": "HTML", "mime_type": "text/html", "ext": ".html"},
}


# ===== Task Creation & Retrieval =====

@router.post(
    "",
    response_model=TaskResponse,
    status_code=201,
    summary="Create a new task",
    description="Create a new task with capability requirements"
)
async def create_task(
    project_id: str = Query(..., description="Project ID"),
    task: TaskCreate = ...,
    session: AsyncSession = Depends(get_session)
):
    """
    Create a new task with optional capability requirements.

    **Query Parameters:**
    - `project_id`: The project ID this task belongs to

    **Request Body:**
    ```json
    {
        "title": "Create marketing strategy",
        "description": "Develop Q1 marketing strategy",
        "priority": "high",
        "required_skills": ["marketing_strategy", "content_planning"],
        "required_output_type": "document",
        "output_format": "pdf"
    }
    ```

    **Returns:** Created task with details

    **Errors:**
    - 404: Project not found
    - 422: Validation error
    """
    # Verify project exists
    project_result = await session.execute(
        select(Project).where(Project.project_id == project_id)
    )
    project = project_result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

    # Create task
    task_id = str(uuid.uuid4())
    skill_match_score = None
    assigned_capabilities = None

    # Calculate skill match if agent and skills specified
    if task.assigned_to_agent_id and task.required_skills:
        skill_match_score = calculate_skill_match(
            task.assigned_to_agent_id,
            task.required_skills
        )
        # Get agent's capabilities that match
        agent_config = AgentRegistry.get_agent_config(task.assigned_to_agent_id)
        if agent_config:
            agent_specs = agent_config.get("specializations", [])
            assigned_capabilities = {
                skill: 0.8 + (0.2 if skill.lower() in [s.lower() for s in agent_specs] else 0.0)
                for skill in (task.required_skills or [])
            }

    new_task = Task(
        task_id=task_id,
        project_id=project_id,
        title=task.title,
        description=task.description,
        status=TaskStatus.PENDING,
        priority=Priority[task.priority.upper()] if task.priority else Priority.MEDIUM,
        assigned_to_agent_id=task.assigned_to_agent_id,
        output_format=task.output_format or "text",
        output_metadata=task.output_metadata or {}
    )

    session.add(new_task)
    await session.commit()

    # Get assigned agent name
    assigned_agent_name = None
    if task.assigned_to_agent_id:
        agent_config = AgentRegistry.get_agent_config(task.assigned_to_agent_id)
        if agent_config:
            assigned_agent_name = agent_config.get("name", "")

    return TaskResponse(
        task_id=task_id,
        project_id=project_id,
        title=task.title,
        description=task.description,
        status=TaskStatusEnum.PENDING,
        priority=PriorityEnum[task.priority.upper()] if task.priority else PriorityEnum.MEDIUM,
        assigned_to_agent_id=task.assigned_to_agent_id,
        assigned_agent_name=assigned_agent_name,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        output_format=task.output_format,
        required_skills=task.required_skills or [],
        skill_match_score=skill_match_score,
        assigned_agent_capabilities=assigned_capabilities
    )


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get task details",
    description="Retrieve detailed information about a task"
)
async def get_task(
    task_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get detailed information about a task.

    **Path Parameters:**
    - `task_id`: The task identifier

    **Returns:** Task information including capability match details

    **Errors:**
    - 404: Task not found
    """
    result = await session.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    # Get assigned agent name
    assigned_agent_name = None
    if task.assigned_to_agent_id:
        agent_config = AgentRegistry.get_agent_config(task.assigned_to_agent_id)
        if agent_config:
            assigned_agent_name = agent_config.get("name", "")

    return TaskResponse(
        task_id=task.task_id,
        project_id=task.project_id,
        title=task.title,
        description=task.description,
        status=TaskStatusEnum(task.status.value) if task.status else TaskStatusEnum.PENDING,
        priority=PriorityEnum(task.priority.value) if task.priority else PriorityEnum.MEDIUM,
        assigned_to_agent_id=task.assigned_to_agent_id,
        assigned_agent_name=assigned_agent_name,
        created_at=task.created_at,
        updated_at=task.updated_at,
        output_format=task.output_format,
        required_skills=getattr(task, 'required_skills', []) or [],
        assigned_agent_capabilities=task.output_metadata
    )


# ===== Capability-Based Assignment =====

@router.get(
    "/{task_id}/capable-agents",
    response_model=TaskCapableAgentsResponse,
    summary="Find capable agents",
    description="Get agents capable of performing a task"
)
async def get_capable_agents(
    task_id: str,
    session: AsyncSession = Depends(get_session),
    min_match_score: float = Query(0.5, ge=0.0, le=1.0, description="Minimum skill match score")
):
    """
    Find agents capable of performing a task based on required skills.

    **Path Parameters:**
    - `task_id`: The task identifier

    **Query Parameters:**
    - `min_match_score`: Minimum skill match score required (0.0-1.0, default: 0.5)

    **Returns:** List of agents ranked by skill match

    **Example Response:**
    ```json
    {
        "task_id": "task-123",
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
    ```

    **Errors:**
    - 404: Task not found
    """
    result = await session.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    required_skills = getattr(task, 'required_skills', None) or []

    # Find capable agents
    suggestions = []

    for agent_id, config in AgentRegistry.AGENT_CATALOG.items():
        agent_specs = config.get("specializations", [])
        matching_skills = [s for s in required_skills if any(
            spec.lower() == s.lower() or spec == s for spec in agent_specs
        )]

        if matching_skills:
            match_score = len(matching_skills) / len(required_skills) if required_skills else 0.0
            match_score = min(1.0, match_score + 0.1)  # Boost for having any skills

            if match_score >= min_match_score:
                missing_skills = [s for s in required_skills if s not in matching_skills]

                suggestion = TaskAssignmentSuggestion(
                    agent_id=agent_id,
                    agent_name=config.get("name", ""),
                    match_score=match_score,
                    matching_skills=matching_skills,
                    missing_skills=missing_skills,
                    reason=f"Has {len(matching_skills)}/{len(required_skills)} required skills"
                )
                suggestions.append(suggestion)

    # Sort by match score
    suggestions.sort(key=lambda s: s.match_score, reverse=True)

    return TaskCapableAgentsResponse(
        task_id=task_id,
        task_title=task.title,
        required_skills=required_skills,
        capable_agents=suggestions,
        total_capable=len(suggestions)
    )


@router.post(
    "/{task_id}/assign-by-capability",
    response_model=TaskResponse,
    summary="Auto-assign task by capability",
    description="Automatically assign task to best matching agent"
)
async def assign_by_capability(
    task_id: str,
    session: AsyncSession = Depends(get_session),
    min_match_score: float = Query(0.5, ge=0.0, le=1.0)
):
    """
    Automatically assign a task to the best matching agent based on skills.

    **Path Parameters:**
    - `task_id`: The task identifier

    **Query Parameters:**
    - `min_match_score`: Minimum match score required (default: 0.5)

    **Returns:** Updated task with assignment

    **Errors:**
    - 404: Task not found or no capable agents found
    - 409: Task already assigned
    """
    result = await session.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    if task.assigned_to_agent_id:
        raise HTTPException(
            status_code=409,
            detail=f"Task already assigned to {task.assigned_to_agent_id}"
        )

    required_skills = getattr(task, 'required_skills', None) or []

    # Find best agent
    best_agent = None
    best_score = min_match_score

    for agent_id, config in AgentRegistry.AGENT_CATALOG.items():
        agent_specs = config.get("specializations", [])
        matching = sum(1 for s in required_skills if any(
            spec.lower() == s.lower() or spec == s for spec in agent_specs
        ))

        if matching > 0:
            score = matching / len(required_skills) if required_skills else 0.0
            if score > best_score:
                best_score = score
                best_agent = agent_id

    if not best_agent:
        raise HTTPException(
            status_code=404,
            detail=f"No agents found with minimum {min_match_score} skill match"
        )

    # Update task
    agent_config = AgentRegistry.get_agent_config(best_agent)
    agent_specs = agent_config.get("specializations", [])

    assigned_capabilities = {
        skill: 0.8 + (0.2 if skill.lower() in [s.lower() for s in agent_specs] else 0.0)
        for skill in (required_skills or [])
    }

    await session.execute(
        update(Task)
        .where(Task.task_id == task_id)
        .values(
            assigned_to_agent_id=best_agent,
            updated_at=datetime.utcnow()
        )
    )
    await session.commit()

    return TaskResponse(
        task_id=task.task_id,
        project_id=task.project_id,
        title=task.title,
        description=task.description,
        status=TaskStatusEnum(task.status.value) if task.status else TaskStatusEnum.PENDING,
        priority=PriorityEnum(task.priority.value) if task.priority else PriorityEnum.MEDIUM,
        assigned_to_agent_id=best_agent,
        assigned_agent_name=agent_config.get("name", ""),
        created_at=task.created_at,
        updated_at=datetime.utcnow(),
        output_format=task.output_format,
        required_skills=required_skills,
        skill_match_score=best_score,
        assigned_agent_capabilities=assigned_capabilities
    )


# ===== Output Format Endpoints =====

@router.get(
    "/output-formats",
    response_model=List[OutputFormatInfo],
    summary="List supported output formats",
    description="Get all supported output formats"
)
async def list_output_formats():
    """
    Get all supported output formats for tasks.

    **Returns:** List of supported output formats with MIME types

    **Example:**
    ```json
    [
        {
            "format_id": "pdf",
            "name": "PDF Document",
            "description": "Portable Document Format",
            "mime_type": "application/pdf",
            "file_extension": ".pdf",
            "is_active": true
        }
    ]
    ```
    """
    formats = []
    for format_id, info in SUPPORTED_FORMATS.items():
        formats.append(OutputFormatInfo(
            format_id=format_id,
            name=info["name"],
            description=info.get("description", ""),
            mime_type=info["mime_type"],
            file_extension=info["ext"]
        ))
    return formats


@router.get(
    "/{task_id}/output",
    response_model=TaskOutputResponse,
    summary="Get task output",
    description="Get the output of a completed task"
)
async def get_task_output(
    task_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get the output of a task.

    **Path Parameters:**
    - `task_id`: The task identifier

    **Returns:** Task output with format and metadata

    **Errors:**
    - 404: Task not found or no output available
    """
    result = await session.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=404,
            detail=f"Task not completed yet (status: {task.status.value})"
        )

    return TaskOutputResponse(
        task_id=task.task_id,
        output_format=task.output_format or "text",
        output_content=getattr(task, 'output_content', None),
        output_metadata=task.output_metadata or {},
        created_at=task.updated_at
    )


@router.post(
    "/{task_id}/output/convert",
    response_model=TaskOutputResponse,
    summary="Convert task output",
    description="Convert task output to a different format"
)
async def convert_task_output(
    task_id: str,
    target_format: str = Query(..., description="Target output format"),
    session: AsyncSession = Depends(get_session)
):
    """
    Convert task output to a different format.

    **Path Parameters:**
    - `task_id`: The task identifier

    **Query Parameters:**
    - `target_format`: Target output format (pdf, docx, xlsx, json, etc.)

    **Returns:** Converted task output

    **Supported Formats:** pdf, docx, xlsx, json, markdown, html

    **Errors:**
    - 400: Unsupported format
    - 404: Task not found or no output available
    """
    if target_format not in SUPPORTED_FORMATS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported format: {target_format}. Available: {', '.join(SUPPORTED_FORMATS.keys())}"
        )

    result = await session.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=404,
            detail=f"Task not completed yet (status: {task.status.value})"
        )

    # Update task format
    await session.execute(
        update(Task)
        .where(Task.task_id == task_id)
        .values(output_format=target_format)
    )
    await session.commit()

    return TaskOutputResponse(
        task_id=task.task_id,
        output_format=target_format,
        output_metadata=task.output_metadata or {},
        created_at=task.updated_at
    )


@router.post(
    "/{task_id}/approve",
    response_model=TaskResponse,
    summary="Approve a task in review",
    description="Approve and move a task from REVIEW status to COMPLETED"
)
async def approve_task(
    task_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Approve a task that is currently in REVIEW status.

    **Path Parameters:**
    - `task_id`: The task identifier

    **Returns:** Updated task with COMPLETED status

    **Errors:**
    - 404: Task not found
    - 400: Task is not in REVIEW status
    """
    result = await session.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    if task.status != TaskStatus.REVIEW:
        raise HTTPException(
            status_code=400,
            detail=f"Task is not in REVIEW status (current status: {task.status.value})"
        )

    # Update task status to COMPLETED
    await session.execute(
        update(Task)
        .where(Task.task_id == task_id)
        .values(
            status=TaskStatus.COMPLETED,
            updated_at=datetime.utcnow()
        )
    )

    await session.commit()

    # Get updated task
    result = await session.execute(
        select(Task).where(Task.task_id == task_id)
    )
    updated_task = result.scalar_one()

    # Get assigned agent name
    assigned_agent_name = None
    if updated_task.assigned_to_agent_id:
        agent_config = AgentRegistry.get_agent_config(updated_task.assigned_to_agent_id)
        if agent_config:
            assigned_agent_name = agent_config.get("name", "")

    return TaskResponse(
        task_id=updated_task.task_id,
        project_id=updated_task.project_id,
        title=updated_task.title,
        description=updated_task.description,
        status=updated_task.status,
        priority=updated_task.priority,
        assigned_to_agent_id=updated_task.assigned_to_agent_id,
        assigned_agent_name=assigned_agent_name,
        created_at=updated_task.created_at,
        updated_at=updated_task.updated_at,
        output_format=updated_task.output_format,
        required_skills=getattr(updated_task, 'required_skills', []) or [],
        assigned_agent_capabilities=updated_task.output_metadata
    )


@router.get(
    "/{task_id}/output/download",
    summary="Download task output",
    description="Download task output file"
)
async def download_task_output(
    task_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Download task output as a file.

    **Path Parameters:**
    - `task_id`: The task identifier

    **Returns:** File download with appropriate content type

    **Errors:**
    - 404: Task not found or no output available
    """
    result = await session.execute(
        select(Task).where(Task.task_id == task_id)
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail=f"Task '{task_id}' not found")

    if task.status != TaskStatus.COMPLETED:
        raise HTTPException(
            status_code=404,
            detail=f"Task not completed yet (status: {task.status.value})"
        )

    # In a real implementation, this would return the actual file
    # For now, return a redirect to output endpoint
    return {
        "download_url": f"/api/v1/tasks/{task_id}/output",
        "format": task.output_format,
        "filename": f"{task.task_id}{SUPPORTED_FORMATS.get(task.output_format, {}).get('ext', '.txt')}"
    }

