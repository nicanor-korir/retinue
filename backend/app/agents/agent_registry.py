"""Central registry for all available agents in the Deviant platform.

This module provides a centralized catalog of all available agents,
their capabilities, departments, and requirements. This replaces the
previous hardcoded agent definitions scattered throughout the codebase.

Key Components:
- Department enum: All business departments
- OutputType enum: Types of outputs agents can produce
- Specialization enum: Skills and expertise areas
- CapabilityCategory enum: Categories of capabilities
- AgentRegistry class: Central catalog with query methods
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


# ===== ENUMS =====

class Department(str, Enum):
    """All business departments in Deviant."""
    EXECUTIVE = "executive"
    ENGINEERING = "engineering"
    MARKETING = "marketing"
    SALES = "sales"
    FINANCE = "finance"
    HR = "hr"
    OPERATIONS = "operations"
    LEGAL = "legal"
    RESEARCH = "research"


class OutputType(str, Enum):
    """Types of outputs agents can produce."""
    CODE = "code"
    PDF = "pdf"
    MARKDOWN = "markdown"
    DOCX = "docx"
    XLSX = "xlsx"
    PPTX = "pptx"
    JSON = "json"
    TEXT = "text"
    DECISION = "decision"
    APPROVAL = "approval"


class Specialization(str, Enum):
    """Agent specializations and skills."""
    # Engineering
    PYTHON = "python"
    FASTAPI = "fastapi"
    SQLALCHEMY = "sqlalchemy"
    POSTGRESQL = "postgresql"
    REACT = "react"
    NEXTJS = "nextjs"
    TYPESCRIPT = "typescript"
    TAILWINDCSS = "tailwindcss"
    REST_API = "rest_api"

    # Design
    UI_UX = "ui_ux"
    VISUAL_DESIGN = "visual_design"
    USER_RESEARCH = "user_research"
    ACCESSIBILITY = "accessibility"

    # Marketing
    MARKETING_STRATEGY = "marketing_strategy"
    COPYWRITING = "copywriting"
    SOCIAL_MEDIA = "social_media"
    CONTENT_STRATEGY = "content_strategy"
    SEO = "seo"
    PAID_ADVERTISING = "paid_advertising"
    BRAND_MANAGEMENT = "brand_management"

    # Finance
    FINANCIAL_MODELING = "financial_modeling"
    BUDGETING = "budgeting"
    FORECASTING = "forecasting"
    DATA_ANALYSIS = "data_analysis"
    FINANCIAL_PLANNING = "financial_planning"

    # Sales
    B2B_SALES = "b2b_sales"
    ENTERPRISE_SALES = "enterprise_sales"
    NEGOTIATION = "negotiation"
    SALES_STRATEGY = "sales_strategy"

    # HR
    HR_STRATEGY = "hr_strategy"
    TALENT_MANAGEMENT = "talent_management"
    COMPLIANCE = "compliance"
    EMPLOYEE_RELATIONS = "employee_relations"
    HR_OPERATIONS = "hr_operations"

    # Operations
    OPERATIONS = "operations"
    PROCESS_IMPROVEMENT = "process_improvement"
    PROJECT_MANAGEMENT = "project_management"
    COORDINATION = "coordination"

    # Legal
    CORPORATE_LAW = "corporate_law"
    CONTRACTS = "contracts"
    LEGAL_COMPLIANCE = "legal_compliance"

    # Research & Analytics
    MARKET_RESEARCH = "market_research"
    COMPETITIVE_ANALYSIS = "competitive_analysis"
    DATA_VISUALIZATION = "data_visualization"
    ANALYTICS = "analytics"

    # Cross-functional
    STRATEGIC_PLANNING = "strategic_planning"
    DECISION_MAKING = "decision_making"
    LEADERSHIP = "leadership"
    SYSTEM_HEALTH = "system_health"
    AGENT_MONITORING = "agent_monitoring"
    TECHNICAL = 'technical'


class CapabilityCategory(str, Enum):
    """Categories of agent capabilities."""
    TECHNICAL = "technical"
    STRATEGIC = "strategic"
    OPERATIONAL = "operational"
    CREATIVE = "creative"
    ANALYTICAL = "analytical"


# ===== AGENT REGISTRY =====

class AgentRegistry:
    """Central registry for all available agents in Deviant.

    Provides methods to:
    - Get agent configurations
    - Filter agents by department, capability, or specialization
    - Validate agent selections
    - Find capable agents for specific tasks
    """

    AGENT_CATALOG = {
        # ===== EXECUTIVE DEPARTMENT =====

        "ceo_001": {
            "class": "CEOAgent",
            "name": "CEO Agent",
            "role": "Chief Executive Officer",
            "departments": [
                Department.EXECUTIVE,
                Department.ENGINEERING,
                Department.MARKETING,
                Department.SALES,
                Department.FINANCE,
                Department.HR,
                Department.OPERATIONS,
                Department.LEGAL,
                Department.RESEARCH
            ],  # CEO has access to all departments
            "output_types": [OutputType.DECISION, OutputType.APPROVAL, OutputType.TEXT],
            "specializations": [Specialization.STRATEGIC_PLANNING, Specialization.DECISION_MAKING, Specialization.LEADERSHIP],
            "required_for_types": [],  # Required for all project types
            "always_active": True,
            "cost_per_hour": 0,
            "description": "Strategic oversight and executive decision making"
        },

        # ===== OPERATIONS DEPARTMENT (Project Management) =====

        "pm_001": {
            "class": "PMAgent",
            "name": "Project Manager",
            "role": "Senior Project Manager",
            "departments": [Department.OPERATIONS],
            "output_types": [OutputType.TEXT, OutputType.JSON, OutputType.MARKDOWN],
            "specializations": [Specialization.PROJECT_MANAGEMENT, Specialization.COORDINATION],
            "required_for_types": [],  # Required for all project types
            "always_active": True,
            "cost_per_hour": 0,
            "description": "Project planning, task coordination, and progress tracking"
        },

        # ===== HR DEPARTMENT (Agent Monitoring) =====

        "hr_monitor_001": {
            "class": "HRMonitorAgent",
            "name": "HR Monitor",
            "role": "Agent Health Monitor",
            "departments": [Department.HR, Department.OPERATIONS],
            "output_types": [OutputType.TEXT, OutputType.DECISION],
            "specializations": [Specialization.SYSTEM_HEALTH, Specialization.AGENT_MONITORING],
            "required_for_types": [],  # Required for all project types
            "always_active": True,
            "cost_per_hour": 0,
            "description": "Agent health monitoring and system escalation"
        },

        # ===== ENGINEERING DEPARTMENT =====

        "cto_001": {
            "class": "CTOAgent",
            "name": "CTO Agent",
            "role": "Chief Technology Officer",
            "departments": [Department.ENGINEERING, Department.EXECUTIVE, Department.RESEARCH],
            "output_types": [OutputType.TEXT, OutputType.MARKDOWN, OutputType.DECISION],
            "specializations": [Specialization.STRATEGIC_PLANNING, Specialization.TECHNICAL, Specialization.LEADERSHIP],
            "required_for_types": ["software_mvp", "api_development"],
            "always_active": False,
            "cost_per_hour": 0,
            "description": "Technical architecture and engineering oversight"
        },

        "backend_001": {
            "class": "BackendEngineerAgent",
            "name": "Backend Engineer",
            "role": "Senior Backend Engineer",
            "departments": [Department.ENGINEERING],
            "output_types": [OutputType.CODE, OutputType.TEXT, OutputType.MARKDOWN],
            "specializations": [
                Specialization.PYTHON,
                Specialization.FASTAPI,
                Specialization.SQLALCHEMY,
                Specialization.POSTGRESQL,
                Specialization.REST_API
            ],
            "required_for_types": ["software_mvp", "api_development"],
            "always_active": False,
            "cost_per_hour": 0,
            "description": "Backend API development and database design"
        },

        "frontend_001": {
            "class": "FrontendEngineerAgent",
            "name": "Frontend Engineer",
            "role": "Senior Frontend Engineer",
            "departments": [Department.ENGINEERING],
            "output_types": [OutputType.CODE, OutputType.TEXT, OutputType.MARKDOWN],
            "specializations": [
                Specialization.REACT,
                Specialization.NEXTJS,
                Specialization.TYPESCRIPT,
                Specialization.TAILWINDCSS
            ],
            "required_for_types": ["software_mvp", "web_application"],
            "always_active": False,
            "cost_per_hour": 0,
            "description": "Frontend UI development and web applications"
        },

        "designer_001": {
            "class": "DesignerAgent",
            "name": "Product Designer",
            "role": "Senior Product Designer",
            "departments": [Department.ENGINEERING],
            "output_types": [OutputType.TEXT, OutputType.MARKDOWN, OutputType.JSON],
            "specializations": [
                Specialization.UI_UX,
                Specialization.VISUAL_DESIGN,
                Specialization.USER_RESEARCH,
                Specialization.ACCESSIBILITY
            ],
            "required_for_types": ["software_mvp", "marketing_campaign"],
            "always_active": False,
            "cost_per_hour": 0,
            "description": "UI/UX design and product specifications"
        },

        # ===== MARKETING DEPARTMENT (NEW) =====

        "cmo_001": {
            "class": "CMOAgent",
            "name": "CMO Agent",
            "role": "Chief Marketing Officer",
            "departments": [Department.MARKETING, Department.OPERATIONS, Department.EXECUTIVE],
            "output_types": [OutputType.MARKDOWN, OutputType.TEXT, OutputType.PDF, OutputType.JSON],
            "specializations": [
                Specialization.MARKETING_STRATEGY,
                Specialization.BRAND_MANAGEMENT,
                Specialization.STRATEGIC_PLANNING
            ],
            "required_for_types": ["marketing_campaign", "brand_strategy"],
            "always_active": False,
            "cost_per_hour": 0,
            "description": "Marketing strategy and campaign planning"
        },

        "content_001": {
            "class": "ContentMarketingAgent",
            "name": "Content Marketing Specialist",
            "role": "Content Marketing Manager",
            "departments": [Department.MARKETING],
            "output_types": [OutputType.MARKDOWN, OutputType.TEXT],
            "specializations": [
                Specialization.COPYWRITING,
                Specialization.SEO,
                Specialization.CONTENT_STRATEGY
            ],
            "required_for_types": ["marketing_campaign", "content_strategy"],
            "always_active": False,
            "cost_per_hour": 0,
            "description": "Content creation and copywriting"
        },

        "social_media_001": {
            "class": "SocialMediaAgent",
            "name": "Social Media Manager",
            "role": "Social Media Specialist",
            "departments": [Department.MARKETING],
            "output_types": [OutputType.TEXT, OutputType.MARKDOWN, OutputType.JSON],
            "specializations": [
                Specialization.SOCIAL_MEDIA,
                Specialization.PAID_ADVERTISING,
                Specialization.COPYWRITING
            ],
            "required_for_types": ["marketing_campaign"],
            "always_active": False,
            "cost_per_hour": 0,
            "description": "Social media strategy and campaign management"
        },

        # ===== FINANCE DEPARTMENT (NEW) =====

        "cfo_001": {
            "class": "CFOAgent",
            "name": "CFO Agent",
            "role": "Chief Financial Officer",
            "departments": [Department.FINANCE, Department.EXECUTIVE, Department.OPERATIONS],
            "output_types": [OutputType.TEXT, OutputType.MARKDOWN, OutputType.XLSX],
            "specializations": [
                Specialization.FINANCIAL_PLANNING,
                Specialization.BUDGETING,
                Specialization.FORECASTING
            ],
            "required_for_types": ["financial_analysis", "budget_planning"],
            "always_active": False,
            "cost_per_hour": 0,
            "description": "Financial strategy and planning"
        },

        "financial_analyst_001": {
            "class": "FinancialAnalystAgent",
            "name": "Financial Analyst",
            "role": "Senior Financial Analyst",
            "departments": [Department.FINANCE],
            "output_types": [OutputType.TEXT, OutputType.MARKDOWN, OutputType.XLSX, OutputType.JSON],
            "specializations": [
                Specialization.FINANCIAL_MODELING,
                Specialization.DATA_ANALYSIS,
                Specialization.FORECASTING
            ],
            "required_for_types": ["financial_analysis", "investment_analysis"],
            "always_active": False,
            "cost_per_hour": 0,
            "description": "Financial analysis and modeling"
        },

        # ===== SALES DEPARTMENT (NEW) =====

        "sales_manager_001": {
            "class": "SalesManagerAgent",
            "name": "Sales Manager",
            "role": "Sales Team Lead",
            "departments": [Department.SALES],
            "output_types": [OutputType.MARKDOWN, OutputType.TEXT, OutputType.PDF],
            "specializations": [
                Specialization.B2B_SALES,
                Specialization.ENTERPRISE_SALES,
                Specialization.NEGOTIATION,
                Specialization.SALES_STRATEGY
            ],
            "required_for_types": ["business_proposal", "sales_strategy"],
            "always_active": False,
            "cost_per_hour": 0,
            "description": "Sales strategy and business development"
        },

        # ===== HR DEPARTMENT (NEW AGENTS) =====

        "chro_001": {
            "class": "CHROAgent",
            "name": "CHRO Agent",
            "role": "Chief Human Resources Officer",
            "departments": [Department.HR, Department.EXECUTIVE],
            "output_types": [OutputType.TEXT, OutputType.MARKDOWN, OutputType.DOCX],
            "specializations": [
                Specialization.HR_STRATEGY,
                Specialization.TALENT_MANAGEMENT,
                Specialization.LEADERSHIP
            ],
            "required_for_types": ["hr_policy", "talent_strategy"],
            "always_active": False,
            "cost_per_hour": 0,
            "description": "HR strategy and talent management"
        },

        "hr_specialist_001": {
            "class": "HRSpecialistAgent",
            "name": "HR Specialist",
            "role": "HR Operations Specialist",
            "departments": [Department.HR],
            "output_types": [OutputType.DOCX, OutputType.TEXT, OutputType.MARKDOWN],
            "specializations": [
                Specialization.HR_OPERATIONS,
                Specialization.COMPLIANCE,
                Specialization.EMPLOYEE_RELATIONS
            ],
            "required_for_types": ["hr_policy"],
            "always_active": False,
            "cost_per_hour": 0,
            "description": "HR documentation and operations"
        },

        # ===== LEGAL DEPARTMENT (NEW) =====

        "legal_001": {
            "class": "LegalAgent",
            "name": "Legal Counsel",
            "role": "Corporate Legal Advisor",
            "departments": [Department.LEGAL],
            "output_types": [OutputType.DOCX, OutputType.TEXT, OutputType.MARKDOWN],
            "specializations": [
                Specialization.CORPORATE_LAW,
                Specialization.CONTRACTS,
                Specialization.LEGAL_COMPLIANCE
            ],
            "required_for_types": ["hr_policy", "contracts"],
            "always_active": False,
            "cost_per_hour": 0,
            "description": "Legal advice and compliance"
        },

        # ===== RESEARCH & ANALYTICS DEPARTMENT (NEW) =====

        "research_001": {
            "class": "ResearchAgent",
            "name": "Research Analyst",
            "role": "Market Research Specialist",
            "departments": [Department.RESEARCH],
            "output_types": [OutputType.MARKDOWN, OutputType.TEXT, OutputType.PDF, OutputType.JSON],
            "specializations": [
                Specialization.MARKET_RESEARCH,
                Specialization.COMPETITIVE_ANALYSIS,
                Specialization.USER_RESEARCH
            ],
            "required_for_types": ["market_research"],
            "always_active": False,
            "cost_per_hour": 0,
            "description": "Market and competitive research"
        },

        "data_analyst_001": {
            "class": "DataAnalystAgent",
            "name": "Data Analyst",
            "role": "Senior Data Analyst",
            "departments": [Department.RESEARCH],
            "output_types": [OutputType.MARKDOWN, OutputType.TEXT, OutputType.JSON, OutputType.XLSX],
            "specializations": [
                Specialization.DATA_ANALYSIS,
                Specialization.ANALYTICS,
                Specialization.DATA_VISUALIZATION,
                Specialization.PYTHON
            ],
            "required_for_types": ["market_research", "financial_analysis"],
            "always_active": False,
            "cost_per_hour": 0,
            "description": "Data analysis and visualization"
        },

        # ===== OPERATIONS DEPARTMENT (NEW AGENTS) =====

        "coo_001": {
            "class": "COOAgent",
            "name": "COO Agent",
            "role": "Chief Operating Officer",
            "departments": [Department.OPERATIONS, Department.EXECUTIVE],
            "output_types": [OutputType.MARKDOWN, OutputType.TEXT, OutputType.PDF],
            "specializations": [
                Specialization.OPERATIONS,
                Specialization.PROCESS_IMPROVEMENT,
                Specialization.STRATEGIC_PLANNING
            ],
            "required_for_types": ["operations_optimization"],
            "always_active": False,
            "cost_per_hour": 0,
            "description": "Operations optimization and efficiency"
        },
    }

    @classmethod
    def get_agent_config(cls, agent_id: str) -> Dict:
        """Get full configuration for a specific agent.

        Args:
            agent_id: The agent ID (e.g., 'ceo_001', 'backend_001')

        Returns:
            Dictionary containing agent configuration

        Raises:
            ValueError: If agent_id not found in catalog
        """
        if agent_id not in cls.AGENT_CATALOG:
            raise ValueError(f"Unknown agent: {agent_id}. Available agents: {list(cls.AGENT_CATALOG.keys())}")
        return cls.AGENT_CATALOG[agent_id]

    @classmethod
    def get_agents_by_department(cls, dept: str) -> List[Dict]:
        """Get all agents in a specific department.

        Supports multi-department agents - an agent will be returned if the
        specified department is in their departments list.

        Args:
            dept: Department name (string or Department enum)

        Returns:
            List of agent configurations that belong to that department
        """
        dept_value = dept.value if isinstance(dept, Department) else dept

        result = []
        for agent_id, config in cls.AGENT_CATALOG.items():
            # Handle both legacy single department and new multi-department format
            agent_departments = config.get("departments") or [config.get("department")]

            # Convert department values to strings for comparison
            dept_values = []
            for d in agent_departments:
                if d is not None:
                    dept_values.append(d.value if isinstance(d, Department) else d)

            # Check if requested department is in agent's departments
            if dept_value in dept_values:
                result.append({"agent_id": agent_id, **config})

        return result

    @classmethod
    def get_required_agents(cls, deliverable_type: str) -> List[str]:
        """Get agents required for a specific deliverable type.

        Always includes:
        - CEO (ceo_001) - Strategic oversight
        - PM (pm_001) - Coordination
        - HR Monitor (hr_monitor_001) - System health

        Plus any agents with this type in their required_for_types.

        Args:
            deliverable_type: The deliverable type ID

        Returns:
            List of agent IDs required for this deliverable type
        """
        required = {"ceo_001", "pm_001", "hr_monitor_001"}  # Always active

        for agent_id, config in cls.AGENT_CATALOG.items():
            if deliverable_type in config.get("required_for_types", []):
                required.add(agent_id)

        return sorted(list(required))

    @classmethod
    def get_agents_by_capability(cls, capability: str) -> List[str]:
        """Get agents with a specific capability/specialization.

        Args:
            capability: Specialization name (string or Specialization enum)

        Returns:
            List of agent IDs with this capability
        """
        capability_value = capability.value if isinstance(capability, Specialization) else capability

        result = []
        for agent_id, config in cls.AGENT_CATALOG.items():
            specializations = config.get("specializations", [])
            spec_values = [s.value if isinstance(s, Specialization) else s for s in specializations]

            if capability_value in spec_values:
                result.append(agent_id)

        return sorted(result)

    @classmethod
    def validate_agent_selection(cls, selected_agents: List[str], deliverable_type: str) -> Tuple[bool, List[str]]:
        """Validate that selected agents include all required agents for a deliverable type.

        Args:
            selected_agents: List of selected agent IDs
            deliverable_type: The deliverable type

        Returns:
            Tuple of (is_valid: bool, missing_agent_ids: List[str])
        """
        required = cls.get_required_agents(deliverable_type)
        selected_set = set(selected_agents)
        required_set = set(required)

        missing = list(required_set - selected_set)

        # Also check for unknown agents
        invalid_agents = [a for a in selected_agents if a not in cls.AGENT_CATALOG]
        if invalid_agents:
            return False, invalid_agents

        return len(missing) == 0, missing

    @classmethod
    def get_agent_output_types(cls, agent_id: str) -> List[str]:
        """Get output types an agent can produce.

        Args:
            agent_id: The agent ID

        Returns:
            List of output types (as strings)
        """
        config = cls.get_agent_config(agent_id)
        output_types = config.get("output_types", [OutputType.TEXT])
        return [t.value if isinstance(t, OutputType) else t for t in output_types]

    @classmethod
    def get_agents_by_specialization(cls, specialization: str) -> List[str]:
        """Alias for get_agents_by_capability - get agents with specific specialization.

        Args:
            specialization: Specialization name

        Returns:
            List of agent IDs with this specialization
        """
        return cls.get_agents_by_capability(specialization)

    @classmethod
    def get_all_agents(cls) -> List[Dict]:
        """Get all agents in the catalog.

        Returns:
            List of all agent configurations
        """
        result = []
        for agent_id, config in cls.AGENT_CATALOG.items():
            result.append({"agent_id": agent_id, **config})
        return sorted(result, key=lambda x: x["agent_id"])

    @classmethod
    def get_always_active_agents(cls) -> List[str]:
        """Get agents that are always active (present in all projects).

        Returns:
            List of always-active agent IDs
        """
        return [
            agent_id for agent_id, config in cls.AGENT_CATALOG.items()
            if config.get("always_active", False)
        ]

    @classmethod
    def agent_exists(cls, agent_id: str) -> bool:
        """Check if an agent exists in the catalog.

        Args:
            agent_id: The agent ID to check

        Returns:
            True if agent exists, False otherwise
        """
        return agent_id in cls.AGENT_CATALOG

    @classmethod
    def count_agents(cls) -> int:
        """Get total number of agents in catalog.

        Returns:
            Total count of agents
        """
        return len(cls.AGENT_CATALOG)

    @classmethod
    def count_agents_by_department(cls, dept: str) -> int:
        """Get count of agents in a specific department.

        Args:
            dept: Department name

        Returns:
            Count of agents in that department
        """
        return len(cls.get_agents_by_department(dept))

    @classmethod
    def get_primary_department(cls, agent_id: str) -> str:
        """Get the primary (first) department for an agent.

        Args:
            agent_id: The agent ID

        Returns:
            Primary department name (as string)

        Raises:
            ValueError: If agent_id not found
        """
        config = cls.get_agent_config(agent_id)
        departments = config.get("departments") or [config.get("department")]

        if departments and departments[0]:
            dept = departments[0]
            return dept.value if isinstance(dept, Department) else dept

        return "unknown"

    @classmethod
    def get_all_departments(cls, agent_id: str) -> List[str]:
        """Get all departments for an agent.

        Args:
            agent_id: The agent ID

        Returns:
            List of department names (as strings)

        Raises:
            ValueError: If agent_id not found
        """
        config = cls.get_agent_config(agent_id)
        departments = config.get("departments") or [config.get("department")]

        result = []
        for dept in departments:
            if dept:
                result.append(dept.value if isinstance(dept, Department) else dept)

        return result
