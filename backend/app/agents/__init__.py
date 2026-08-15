"""Agent package initialization - Import all agent classes and registry."""
from app.agents.base_agent import BaseAgent
from app.agents.ceo_agent import CEOAgent
from app.agents.cto_agent import CTOAgent
from app.agents.pm_agent import PMAgent
from app.agents.hr_agent import HRAgent
from app.agents.backend_engineer_agent import BackendEngineerAgent
from app.agents.frontend_engineer_agent import FrontendEngineerAgent
from app.agents.designer_agent import DesignerAgent

# New agent registry system (Phase 0)
from app.agents.agent_registry import (
    AgentRegistry,
    Department,
    OutputType,
    Specialization,
    CapabilityCategory,
)

__all__ = [
    # Base and existing agents
    "BaseAgent",
    "CEOAgent",
    "CTOAgent",
    "PMAgent",
    "HRAgent",
    "BackendEngineerAgent",
    "FrontendEngineerAgent",
    "DesignerAgent",
    # New registry system
    "AgentRegistry",
    "Department",
    "OutputType",
    "Specialization",
    "CapabilityCategory",
]
