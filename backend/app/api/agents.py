"""Agent management API endpoints.

Endpoints for:
- Listing and querying agents
- Retrieving agent capabilities
- Filtering agents by department or specialization
- Validating team composition
- Accessing deliverable type and department information
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
import logging

from app.db.database import get_session
from app.db.models import Agent, Department, DeliverableType
from app.agents import AgentRegistry, Department as DeptEnum, Specialization
from app.utils.agent_capabilities import (
    can_agent_handle_task,
    validate_team_composition,
    calculate_skill_match,
    get_agent_capability_summary,
    get_team_capability_summary,
    find_capable_agents,
)
from app.api.schemas import (
    AgentInfoResponse,
    AgentDetailedResponse,
    AgentStatusResponse,
    DepartmentResponse,
    DeliverableTypeResponse,
    TeamValidationRequest,
    TeamValidationResponse,
    TeamValidationIssue,
    AgentStatusEnum,
    PaginatedResponse,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/agents", tags=["Agents"])


# ===== Agent Endpoints =====

@router.get(
    "",
    response_model=List[AgentDetailedResponse],
    summary="List all agents",
    description="Get a complete list of all agents with full details including status, capabilities, and specializations"
)
async def list_agents(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    department: Optional[str] = Query(None, description="Filter by department ID"),
    active_only: bool = Query(True, description="Only return active agents"),
    session: AsyncSession = Depends(get_session)
):
    """
    List all agents with optional filtering and full details.

    **Query Parameters:**
    - `skip`: Number of agents to skip (default: 0)
    - `limit`: Number of agents to return (default: 100, max: 200)
    - `department`: Filter by department ID (e.g., 'marketing', 'engineering')
    - `active_only`: Only return active agents (default: True)

    **Returns:** List of agent objects with complete information including capabilities and status
    """
    agents = []

    for agent_id, config in AgentRegistry.AGENT_CATALOG.items():
        # Apply filters
        if active_only and not config.get("is_active", True):
            continue

        # Get all departments for this agent (supports multi-department)
        agent_departments = config.get("departments") or [config.get("department")]
        dept_values = []
        for d in agent_departments:
            if d is not None:
                dept_values.append(d.value if hasattr(d, "value") else str(d))

        # Primary department (first one) for backwards compatibility
        primary_dept = dept_values[0] if dept_values else "unknown"

        # Filter by department - check if agent belongs to the requested department
        if department and department not in dept_values:
            continue

        agent = AgentDetailedResponse(
            agent_id=agent_id,
            name=config.get("name", ""),
            role=config.get("role", ""),
            department=primary_dept,  # Legacy field
            departments=dept_values,  # New multi-department field
            is_active=config.get("is_active", True),
            description=config.get("description", ""),
            output_types=config.get("output_types", []),
            specializations=config.get("specializations", []),
            required_for_types=config.get("required_for_types", []),
            always_active=config.get("always_active", False),
            cost_per_hour=config.get("cost_per_hour", 0.0)
        )
        agents.append(agent)

    # Apply pagination
    return agents[skip : skip + limit]


@router.get(
    "/{agent_id}",
    response_model=AgentDetailedResponse,
    summary="Get agent details",
    description="Get detailed information about a specific agent including capabilities"
)
async def get_agent(agent_id: str):
    """
    Get detailed information about a specific agent.

    **Path Parameters:**
    - `agent_id`: The agent identifier (e.g., 'cmo_001')

    **Returns:** Detailed agent information with capabilities and metadata

    **Errors:**
    - 404: Agent not found
    """
    config = AgentRegistry.get_agent_config(agent_id)

    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Agent '{agent_id}' not found"
        )

    # Get all departments for multi-department support
    agent_departments = config.get("departments") or [config.get("department")]
    dept_values = []
    for d in agent_departments:
        if d is not None:
            dept_values.append(d.value if hasattr(d, "value") else str(d))

    primary_dept = dept_values[0] if dept_values else "unknown"

    return AgentDetailedResponse(
        agent_id=agent_id,
        name=config.get("name", ""),
        role=config.get("role", ""),
        department=primary_dept,  # Legacy field
        departments=dept_values,  # Multi-department support
        is_active=config.get("is_active", True),
        description=config.get("description", ""),
        output_types=config.get("output_types", []),
        specializations=config.get("specializations", []),
        required_for_types=config.get("required_for_types", []),
        always_active=config.get("always_active", False),
        cost_per_hour=config.get("cost_per_hour", 0.0)
    )


@router.get(
    "/by-department/{department}",
    response_model=List[AgentInfoResponse],
    summary="List agents by department",
    description="Get all agents in a specific department (supports multi-department agents)"
)
async def get_agents_by_department(
    department: str
):
    """
    Get all agents in a specific department.

    Now supports multi-department agents - an agent will be returned if the
    specified department is in their departments list.

    **Path Parameters:**
    - `department`: Department identifier

    **Returns:** List of agents in the department

    **Errors:**
    - 404: Department not found

    **Examples:**
    - `/agents/by-department/executive` - Returns CEO, CTO, CFO, CMO, etc.
    - `/agents/by-department/engineering` - Returns CTO, CEO, engineers, etc.
    """
    # Validate department exists
    try:
        dept_enum = DeptEnum[department.upper()]
    except KeyError:
        raise HTTPException(
            status_code=404,
            detail=f"Department '{department}' not found. Available: " +
                   ", ".join([d.value for d in DeptEnum])
        )

    # Use AgentRegistry.get_agents_by_department for multi-department support
    agent_configs = AgentRegistry.get_agents_by_department(department)

    agents = []
    for agent_data in agent_configs:
        # Get all departments for this agent
        agent_departments = agent_data.get("departments") or [agent_data.get("department")]
        dept_values = []
        for d in agent_departments:
            if d is not None:
                dept_values.append(d.value if hasattr(d, "value") else str(d))

        primary_dept = dept_values[0] if dept_values else "unknown"

        agent = AgentInfoResponse(
            agent_id=agent_data["agent_id"],
            name=agent_data.get("name", ""),
            role=agent_data.get("role", ""),
            department=primary_dept,  # Legacy field
            departments=dept_values,  # New multi-department field
            is_active=agent_data.get("is_active", True),
            description=agent_data.get("description", "")
        )
        agents.append(agent)

    return agents


@router.get(
    "/by-capability/{capability}",
    response_model=List[AgentInfoResponse],
    summary="Find agents by capability",
    description="Get agents that have a specific capability or skill"
)
async def get_agents_by_capability(
    capability: str
):
    """
    Find agents with a specific capability or specialization.

    **Path Parameters:**
    - `capability`: The capability/specialization to search for

    **Returns:** List of agents with the specified capability

    **Example:**
    - `/agents/by-capability/python` - Find all Python developers
    - `/agents/by-capability/marketing_strategy` - Find marketing strategists
    """
    agents = []

    for agent_id, config in AgentRegistry.AGENT_CATALOG.items():
        specs = config.get("specializations", [])
        # Check if capability matches any specialization
        if any(cap.lower() == capability.lower() or cap == capability for cap in specs):
            # Get all departments for multi-department support
            agent_departments = config.get("departments") or [config.get("department")]
            dept_values = []
            for d in agent_departments:
                if d is not None:
                    dept_values.append(d.value if hasattr(d, "value") else str(d))

            primary_dept = dept_values[0] if dept_values else "unknown"

            agent = AgentInfoResponse(
                agent_id=agent_id,
                name=config.get("name", ""),
                role=config.get("role", ""),
                department=primary_dept,  # Legacy field
                departments=dept_values,  # Multi-department support
                is_active=config.get("is_active", True),
                description=config.get("description", "")
            )
            agents.append(agent)

    if not agents:
        logger.warning(f"No agents found with capability: {capability}")

    return agents


# ===== Team Validation Endpoints =====

@router.post(
    "/validate-team",
    response_model=TeamValidationResponse,
    summary="Validate team composition",
    description="Check if a team of agents is valid for a project"
)
async def validate_team(request: TeamValidationRequest):
    """
    Validate team composition for a project.

    **Request Body:**
    ```json
    {
        "agent_ids": ["ceo_001", "cto_001", "backend_001"],
        "deliverable_type": "software_mvp",
        "project_type": "software_mvp"
    }
    ```

    **Returns:** Validation result with issues and warnings

    **Validation Checks:**
    - Required agents present (CEO, PM, HR Monitor for software projects)
    - Agent availability
    - Team completeness for deliverable type
    - Skill coverage
    """
    issues = []
    warnings = []

    # Validate that all agents exist
    missing_agents = []
    for agent_id in request.agent_ids:
        config = AgentRegistry.get_agent_config(agent_id)
        if not config:
            missing_agents.append(agent_id)

    if missing_agents:
        issues.append(TeamValidationIssue(
            severity="error",
            code="INVALID_AGENT_ID",
            message=f"Agent(s) not found: {', '.join(missing_agents)}",
            affected_agents=missing_agents
        ))

    # Check for required agents if deliverable type specified
    if request.deliverable_type:
        required = AgentRegistry.get_required_agents(request.deliverable_type)
        missing_required = [a for a in required if a not in request.agent_ids]

        if missing_required:
            missing_names = [
                AgentRegistry.get_agent_config(a).get("name", a)
                for a in missing_required
            ]
            issues.append(TeamValidationIssue(
                severity="error",
                code="MISSING_REQUIRED_AGENTS",
                message=f"Missing required agents for {request.deliverable_type}: {', '.join(missing_names)}",
                affected_agents=missing_required
            ))

    # Check for always-active agents
    always_active_agents = []
    for agent_id, config in AgentRegistry.AGENT_CATALOG.items():
        if config.get("always_active") and agent_id not in request.agent_ids:
            always_active_agents.append(agent_id)

    if always_active_agents:
        agent_names = [AgentRegistry.get_agent_config(a).get("name", a) for a in always_active_agents]
        warnings.append(
            f"Team is missing always-active agents: {', '.join(agent_names)}"
        )

    # Calculate team cost and time
    total_cost = 0.0
    agent_names = []
    for agent_id in request.agent_ids:
        config = AgentRegistry.get_agent_config(agent_id)
        if config:
            total_cost += config.get("cost_per_hour", 0.0) * 40  # Assume 40 hours
            agent_names.append(config.get("name", agent_id))

    # Get skill coverage
    required_roles = []
    optional_roles = []

    # Simple heuristic: if no issues, team is valid
    is_valid = len([i for i in issues if i.severity == "error"]) == 0

    return TeamValidationResponse(
        is_valid=is_valid,
        issues=issues,
        warnings=warnings,
        team_size=len(request.agent_ids),
        required_roles_present=agent_names[:len(request.agent_ids)//2],
        optional_roles_present=agent_names[len(request.agent_ids)//2:],
        estimated_completion_time_hours=40.0,
        estimated_cost=total_cost
    )


@router.post(
    "/suggest-agents",
    response_model=List[AgentInfoResponse],
    summary="Suggest agents for requirements",
    description="Get agent recommendations based on required skills and output types"
)
async def suggest_agents(
    skills: List[str] = Query(..., description="Required skills"),
    output_type: Optional[str] = Query(None, description="Required output type"),
    exclude_agents: List[str] = Query(None, description="Agent IDs to exclude")
):
    """
    Get agent recommendations based on required skills.

    **Query Parameters:**
    - `skills`: List of required skills (e.g., 'python', 'fastapi')
    - `output_type`: Required output type (e.g., 'code', 'document')
    - `exclude_agents`: Agent IDs to exclude from suggestions

    **Returns:** Sorted list of agents matching the requirements
    """
    exclude = exclude_agents or []
    suggestions = []

    for agent_id, config in AgentRegistry.AGENT_CATALOG.items():
        # Skip excluded agents
        if agent_id in exclude:
            continue

        # Check skill match
        agent_skills = config.get("specializations", [])
        matching = sum(1 for s in skills if any(
            sk.lower() == s.lower() or sk == s for sk in agent_skills
        ))

        if matching > 0:
            # Get all departments for multi-department support
            agent_departments = config.get("departments") or [config.get("department")]
            dept_values = []
            for d in agent_departments:
                if d is not None:
                    dept_values.append(d.value if hasattr(d, "value") else str(d))

            primary_dept = dept_values[0] if dept_values else "unknown"

            agent = AgentInfoResponse(
                agent_id=agent_id,
                name=config.get("name", ""),
                role=config.get("role", ""),
                department=primary_dept,  # Legacy field
                departments=dept_values,  # Multi-department support
                is_active=config.get("is_active", True),
                description=config.get("description", "")
            )
            suggestions.append((agent, matching))

    # Sort by number of matching skills (highest first)
    suggestions.sort(key=lambda x: x[1], reverse=True)

    return [agent for agent, _ in suggestions]


# ===== Department Endpoints =====

@router.get(
    "/departments",
    response_model=List[DepartmentResponse],
    summary="List all departments",
    description="Get all departments in the organization"
)
async def list_departments(session: AsyncSession = Depends(get_session)):
    """
    List all departments in the organization.

    **Returns:** List of department information
    """
    result = await session.execute(select(Department))
    db_depts = result.scalars().all()

    departments = []
    for dept in db_depts:
        # Count agents in department (supports multi-department agents)
        # Use AgentRegistry method which properly handles multi-department
        agent_count = AgentRegistry.count_agents_by_department(dept.department_id)

        dept_response = DepartmentResponse(
            department_id=dept.department_id,
            name=dept.name,
            description=dept.description,
            icon=dept.icon,
            color=dept.color,
            is_active=dept.is_active,
            agent_count=agent_count
        )
        departments.append(dept_response)

    return departments


@router.get(
    "/departments/{department_id}",
    response_model=DepartmentResponse,
    summary="Get department details",
    description="Get information about a specific department"
)
async def get_department(
    department_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get details about a specific department.

    **Path Parameters:**
    - `department_id`: The department identifier

    **Returns:** Department information with agent count

    **Errors:**
    - 404: Department not found
    """
    result = await session.execute(
        select(Department).where(Department.department_id == department_id)
    )
    dept = result.scalar_one_or_none()

    if not dept:
        raise HTTPException(status_code=404, detail=f"Department '{department_id}' not found")

    # Count agents in department (supports multi-department agents)
    agent_count = AgentRegistry.count_agents_by_department(department_id)

    return DepartmentResponse(
        department_id=dept.department_id,
        name=dept.name,
        description=dept.description,
        icon=dept.icon,
        color=dept.color,
        is_active=dept.is_active,
        agent_count=agent_count
    )


# ===== Deliverable Type Endpoints =====

@router.get(
    "/deliverable-types",
    response_model=List[DeliverableTypeResponse],
    summary="List deliverable types",
    description="Get all available deliverable types for projects"
)
async def list_deliverable_types(
    active_only: bool = Query(True),
    session: AsyncSession = Depends(get_session)
):
    """
    List all available deliverable types.

    **Query Parameters:**
    - `active_only`: Only return active deliverable types (default: True)

    **Returns:** List of deliverable types with typical agent requirements
    """
    query = select(DeliverableType)
    if active_only:
        query = query.where(DeliverableType.is_active == True)

    result = await session.execute(query)
    types = result.scalars().all()

    return [
        DeliverableTypeResponse(
            type_id=dt.type_id,
            name=dt.name,
            description=dt.description,
            output_format=dt.output_format,
            typical_agents=dt.typical_agents or [],
            is_active=dt.is_active
        )
        for dt in types
    ]


@router.get(
    "/deliverable-types/{type_id}",
    response_model=DeliverableTypeResponse,
    summary="Get deliverable type details",
    description="Get detailed information about a specific deliverable type"
)
async def get_deliverable_type(
    type_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get details about a specific deliverable type.

    **Path Parameters:**
    - `type_id`: The deliverable type identifier (e.g., 'software_mvp')

    **Returns:** Deliverable type information

    **Errors:**
    - 404: Deliverable type not found
    """
    result = await session.execute(
        select(DeliverableType).where(DeliverableType.type_id == type_id)
    )
    dt = result.scalar_one_or_none()

    if not dt:
        raise HTTPException(
            status_code=404,
            detail=f"Deliverable type '{type_id}' not found"
        )

    return DeliverableTypeResponse(
        type_id=dt.type_id,
        name=dt.name,
        description=dt.description,
        output_format=dt.output_format,
        typical_agents=dt.typical_agents or [],
        is_active=dt.is_active
    )


# ===== Agent Status Endpoints =====

@router.get(
    "/status",
    response_model=List[AgentInfoResponse],
    summary="Get all agent statuses",
    description="Get runtime status and information of all agents"
)
async def get_all_agent_status(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    active_only: bool = Query(True, description="Only return active agents"),
    session: AsyncSession = Depends(get_session)
):
    """
    Get runtime status and information of all agents.

    **Query Parameters:**
    - `skip`: Number of agents to skip (default: 0)
    - `limit`: Number of agents to return (default: 100, max: 200)
    - `active_only`: Only return active agents (default: True)

    **Returns:** List of agent information with current status
    """
    agents = []

    # Get all agents from registry
    for agent_id, config in AgentRegistry.AGENT_CATALOG.items():
        # Apply active_only filter
        if active_only and not config.get("is_active", True):
            continue

        # Get all departments for multi-department support
        agent_departments = config.get("departments") or [config.get("department")]
        dept_values = []
        for d in agent_departments:
            if d is not None:
                dept_values.append(d.value if hasattr(d, "value") else str(d))

        primary_dept = dept_values[0] if dept_values else "unknown"

        agent = AgentInfoResponse(
            agent_id=agent_id,
            name=config.get("name", ""),
            role=config.get("role", ""),
            department=primary_dept,  # Legacy field
            departments=dept_values,  # Multi-department support
            is_active=config.get("is_active", True),
            description=config.get("description", "")
        )
        agents.append(agent)

    # Apply pagination
    return agents[skip : skip + limit]


@router.get(
    "/{agent_id}/status",
    response_model=AgentDetailedResponse,
    summary="Get agent status and details",
    description="Get runtime status and detailed information of a specific agent"
)
async def get_agent_status(
    agent_id: str,
    session: AsyncSession = Depends(get_session)
):
    """
    Get runtime status and detailed information of a specific agent.

    **Path Parameters:**
    - `agent_id`: The agent identifier

    **Returns:** Agent status including availability, capabilities, and specializations

    **Errors:**
    - 404: Agent not found
    """
    config = AgentRegistry.get_agent_config(agent_id)

    if not config:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_id}' not found")

    # Get all departments for multi-department support
    agent_departments = config.get("departments") or [config.get("department")]
    dept_values = []
    for d in agent_departments:
        if d is not None:
            dept_values.append(d.value if hasattr(d, "value") else str(d))

    primary_dept = dept_values[0] if dept_values else "unknown"

    return AgentDetailedResponse(
        agent_id=agent_id,
        name=config.get("name", ""),
        role=config.get("role", ""),
        department=primary_dept,  # Legacy field
        departments=dept_values,  # Multi-department support
        is_active=config.get("is_active", True),
        description=config.get("description", ""),
        output_types=config.get("output_types", []),
        specializations=config.get("specializations", []),
        required_for_types=config.get("required_for_types", []),
        always_active=config.get("always_active", False),
        cost_per_hour=config.get("cost_per_hour", 0.0)
    )

