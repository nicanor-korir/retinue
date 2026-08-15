"""Utilities for agent capability matching and validation.

This module provides functions for:
- Checking if an agent can handle specific tasks
- Finding agents with specific capabilities
- Validating team compositions
- Matching task requirements to agent capabilities
"""

from typing import List, Tuple, Optional
from app.agents.agent_registry import AgentRegistry, Specialization
import logging

logger = logging.getLogger(__name__)


def can_agent_handle_task(
    agent_id: str,
    required_skills: List[str],
    required_output_type: Optional[str] = None
) -> Tuple[bool, List[str]]:
    """Check if an agent can handle a task based on skills and output requirements.

    Args:
        agent_id: The agent ID to check
        required_skills: List of required skill names
        required_output_type: Required output type (optional)

    Returns:
        Tuple of (can_handle: bool, missing_skills: List[str])
    """
    try:
        config = AgentRegistry.get_agent_config(agent_id)
    except ValueError:
        return False, [f"Unknown agent: {agent_id}"]

    agent_skills = set()
    for spec in config.get("specializations", []):
        if isinstance(spec, Specialization):
            agent_skills.add(spec.value)
        else:
            agent_skills.add(str(spec))

    # Check required skills
    missing_skills = []
    for skill in required_skills:
        skill_value = skill.value if isinstance(skill, Specialization) else skill
        if skill_value not in agent_skills:
            missing_skills.append(skill_value)

    # Check output type if required
    if required_output_type:
        output_types = AgentRegistry.get_agent_output_types(agent_id)
        if required_output_type not in output_types:
            missing_skills.append(f"Cannot produce {required_output_type}")

    return len(missing_skills) == 0, missing_skills


def find_capable_agents(
    required_skills: List[str],
    required_output_type: Optional[str] = None,
    from_agents: Optional[List[str]] = None
) -> List[str]:
    """Find agents capable of handling specific requirements.

    Args:
        required_skills: List of required skills
        required_output_type: Output type needed (optional)
        from_agents: Limit search to these agent IDs (optional)

    Returns:
        List of capable agent IDs
    """
    if from_agents is None:
        from_agents = list(AgentRegistry.AGENT_CATALOG.keys())

    capable = []
    for agent_id in from_agents:
        can_handle, _ = can_agent_handle_task(agent_id, required_skills, required_output_type)
        if can_handle:
            capable.append(agent_id)

    return capable


def validate_team_composition(selected_agents: List[str]) -> Tuple[bool, List[str]]:
    """Validate that selected agents form a complete team.

    Checks:
    - All always-active agents (CEO, PM, HR Monitor) are present
    - No unknown agents
    - At least one agent selected

    Args:
        selected_agents: List of selected agent IDs

    Returns:
        Tuple of (is_valid: bool, issues: List[str])
    """
    issues = []

    if not selected_agents:
        return False, ["No agents selected"]

    # Check for always-active agents
    required_always_active = ["ceo_001", "pm_001", "hr_monitor_001"]
    for agent_id in required_always_active:
        if agent_id not in selected_agents:
            issues.append(f"Missing always-active agent: {agent_id}")

    # Check for unknown agents
    for agent_id in selected_agents:
        if not AgentRegistry.agent_exists(agent_id):
            issues.append(f"Unknown agent: {agent_id}")

    return len(issues) == 0, issues


def validate_team_for_deliverable(
    selected_agents: List[str],
    deliverable_type: str
) -> Tuple[bool, List[str]]:
    """Validate that team can complete a specific deliverable type.

    Checks:
    - Team composition is valid (always-active agents present)
    - All required agents for deliverable type are included
    - No unknown agents

    Args:
        selected_agents: List of selected agent IDs
        deliverable_type: The deliverable type

    Returns:
        Tuple of (is_valid: bool, issues: List[str])
    """
    # First check basic composition
    is_valid, issues = validate_team_composition(selected_agents)

    # Then check required for deliverable
    required = AgentRegistry.get_required_agents(deliverable_type)
    selected_set = set(selected_agents)
    required_set = set(required)

    missing = list(required_set - selected_set)
    if missing:
        issues.extend([f"Missing required agent for {deliverable_type}: {a}" for a in missing])
        is_valid = False

    return is_valid, issues


def get_agent_capability_summary(agent_id: str) -> dict:
    """Get a summary of an agent's capabilities.

    Args:
        agent_id: The agent ID

    Returns:
        Dictionary with agent info and capabilities
    """
    try:
        config = AgentRegistry.get_agent_config(agent_id)
    except ValueError:
        return {}

    spec_values = []
    for spec in config.get("specializations", []):
        if isinstance(spec, Specialization):
            spec_values.append(spec.value)
        else:
            spec_values.append(str(spec))

    return {
        "agent_id": agent_id,
        "name": config["name"],
        "role": config["role"],
        "department": config["department"].value if hasattr(config["department"], "value") else config["department"],
        "specializations": spec_values,
        "output_types": AgentRegistry.get_agent_output_types(agent_id),
        "always_active": config.get("always_active", False),
        "description": config.get("description", "")
    }


def get_team_capability_summary(agent_ids: List[str]) -> dict:
    """Get a summary of a team's combined capabilities.

    Args:
        agent_ids: List of agent IDs

    Returns:
        Dictionary with team composition and capabilities
    """
    team = []
    all_skills = set()
    all_output_types = set()
    departments = set()

    for agent_id in agent_ids:
        summary = get_agent_capability_summary(agent_id)
        if summary:
            team.append(summary)
            departments.add(summary["department"])
            all_skills.update(summary["specializations"])
            all_output_types.update(summary["output_types"])

    return {
        "team_size": len(team),
        "agents": team,
        "departments": sorted(list(departments)),
        "combined_skills": sorted(list(all_skills)),
        "output_types": sorted(list(all_output_types))
    }


def suggest_agents_for_task(
    task_description: str,
    required_skills: List[str],
    required_output_type: Optional[str] = None,
    from_agents: Optional[List[str]] = None
) -> List[dict]:
    """Suggest agents for a specific task.

    Args:
        task_description: Description of the task
        required_skills: Required skills for the task
        required_output_type: Required output type (optional)
        from_agents: Limit suggestions to these agents (optional)

    Returns:
        List of suggested agents with match scores
    """
    capable_agents = find_capable_agents(required_skills, required_output_type, from_agents)

    suggestions = []
    for agent_id in capable_agents:
        summary = get_agent_capability_summary(agent_id)
        if summary:
            suggestions.append({
                **summary,
                "match_score": calculate_skill_match(agent_id, required_skills)
            })

    return sorted(suggestions, key=lambda x: x["match_score"], reverse=True)


def calculate_skill_match(agent_id: str, required_skills: List[str]) -> float:
    """Calculate how well an agent's skills match required skills.

    Score ranges from 0.0 to 1.0.

    Args:
        agent_id: The agent ID
        required_skills: List of required skills

    Returns:
        Match score (0.0-1.0)
    """
    if not required_skills:
        return 1.0  # Perfect match if no skills required

    try:
        config = AgentRegistry.get_agent_config(agent_id)
    except ValueError:
        return 0.0

    agent_skills = set()
    for spec in config.get("specializations", []):
        if isinstance(spec, Specialization):
            agent_skills.add(spec.value)
        else:
            agent_skills.add(str(spec))

    required_set = set()
    for skill in required_skills:
        if isinstance(skill, Specialization):
            required_set.add(skill.value)
        else:
            required_set.add(str(skill))

    matches = len(agent_skills & required_set)
    return matches / len(required_set)


def get_department_agents(department: str) -> List[dict]:
    """Get all agents in a department with their capabilities.

    Args:
        department: Department name

    Returns:
        List of agent summaries in that department
    """
    agents = AgentRegistry.get_agents_by_department(department)
    return [get_agent_capability_summary(a["agent_id"]) for a in agents if a.get("agent_id")]


def find_agents_by_specialization(specialization: str) -> List[dict]:
    """Find all agents with a specific specialization.

    Args:
        specialization: Specialization name

    Returns:
        List of agent summaries with that specialization
    """
    agent_ids = AgentRegistry.get_agents_by_specialization(specialization)
    return [get_agent_capability_summary(aid) for aid in agent_ids]
