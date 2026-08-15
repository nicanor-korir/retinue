"""Per-agent RAG retrieval strategies - customized context for each agent type."""

import logging
from typing import Any, Dict, Optional
from enum import Enum

from app.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)


class AgentType(str, Enum):
    """Agent types with specialized retrieval strategies."""
    CEO = "ceo_001"
    CTO = "cto_001"
    PM = "pm_001"
    HR = "hr_001"
    BACKEND_ENGINEER = "backend_001"
    FRONTEND_ENGINEER = "frontend_001"
    DESIGNER = "designer_001"


class AgentRetrievalStrategy:
    """Base class for agent-specific retrieval strategies."""

    def __init__(self, agent_id: str, agent_type: str):
        """Initialize strategy."""
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.rag_service = get_rag_service()

    async def retrieve_context(
        self,
        query: str,
        project_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Retrieve context using agent-specific strategy.

        Args:
            query: The query string
            project_id: Optional project ID for filtering
            **kwargs: Additional parameters

        Returns:
            Retrieved context results
        """
        raise NotImplementedError

    async def format_for_prompt(self, results: Dict[str, Any]) -> str:
        """
        Format retrieved results for agent's system prompt.

        Args:
            results: Retrieved context

        Returns:
            Formatted context string
        """
        return await self.rag_service.format_context_for_prompt(results)


class CEOAgentStrategy(AgentRetrievalStrategy):
    """CEO Agent: Focus on strategic decisions and project outcomes."""

    async def retrieve_context(
        self,
        query: str,
        project_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Retrieve strategic decisions and project patterns."""
        try:
            # Retrieve decisions (strategic context)
            results = await self.rag_service.retrieve_context(
                query=query,
                agent_id=None,  # CEO sees all decisions (cross-agent)
                project_id=project_id,
                collections=["decisions", "projects"],  # Decisions + project outcomes
                top_k=5
            )

            logger.info(f"CEO retrieved {sum(len(v.get('ids', [])) for v in results.values())} items")
            return results

        except Exception as e:
            logger.error(f"Error in CEO retrieval strategy: {e}")
            return {}


class CTOAgentStrategy(AgentRetrievalStrategy):
    """CTO Agent: Focus on technical decisions, architecture, and code reviews."""

    async def retrieve_context(
        self,
        query: str,
        project_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Retrieve technical decisions and code patterns."""
        try:
            # Retrieve decisions + tasks (technical focus)
            results = await self.rag_service.retrieve_context(
                query=query,
                agent_id=None,  # CTO reviews all technical work
                project_id=project_id,
                collections=["decisions", "tasks"],  # Architecture + implementations
                top_k=5
            )

            logger.info(f"CTO retrieved {sum(len(v.get('ids', [])) for v in results.values())} items")
            return results

        except Exception as e:
            logger.error(f"Error in CTO retrieval strategy: {e}")
            return {}


class PMAgentStrategy(AgentRetrievalStrategy):
    """PM Agent: Focus on project structure, task breakdown, and dependencies."""

    async def retrieve_context(
        self,
        query: str,
        project_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Retrieve project patterns and task structures."""
        try:
            # Retrieve projects + tasks (planning focus)
            results = await self.rag_service.retrieve_context(
                query=query,
                agent_id=None,  # PM learns from all project structures
                project_id=project_id,
                collections=["projects", "tasks"],  # Project patterns + task breakdowns
                top_k=5
            )

            logger.info(f"PM retrieved {sum(len(v.get('ids', [])) for v in results.values())} items")
            return results

        except Exception as e:
            logger.error(f"Error in PM retrieval strategy: {e}")
            return {}


class HRAgentStrategy(AgentRetrievalStrategy):
    """HR Agent: Focus on escalations, blockages, and resolution strategies."""

    async def retrieve_context(
        self,
        query: str,
        project_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Retrieve escalation patterns and resolution strategies."""
        try:
            # Retrieve escalations + decisions (problem-solution focus)
            results = await self.rag_service.retrieve_context(
                query=query,
                agent_id=None,  # HR sees all escalations
                project_id=project_id,
                collections=["decisions", "messages"],  # Resolutions + communications
                top_k=5
            )

            logger.info(f"HR retrieved {sum(len(v.get('ids', [])) for v in results.values())} items")
            return results

        except Exception as e:
            logger.error(f"Error in HR retrieval strategy: {e}")
            return {}


class BackendEngineerStrategy(AgentRetrievalStrategy):
    """Backend Engineer: Focus on code patterns, API designs, and implementations."""

    async def retrieve_context(
        self,
        query: str,
        project_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Retrieve backend code patterns and API designs."""
        try:
            # Retrieve own past tasks + shared knowledge
            results = await self.rag_service.retrieve_context(
                query=query,
                agent_id=self.agent_id,  # Filter by own work (personalized)
                project_id=project_id,
                collections=["tasks", "knowledge_base"],  # Code + best practices
                top_k=5
            )

            logger.info(f"Backend Engineer retrieved {sum(len(v.get('ids', [])) for v in results.values())} items")
            return results

        except Exception as e:
            logger.error(f"Error in Backend Engineer retrieval strategy: {e}")
            return {}


class FrontendEngineerStrategy(AgentRetrievalStrategy):
    """Frontend Engineer: Focus on component patterns and UI implementations."""

    async def retrieve_context(
        self,
        query: str,
        project_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Retrieve frontend component patterns and implementations."""
        try:
            # Retrieve own past tasks + shared knowledge
            results = await self.rag_service.retrieve_context(
                query=query,
                agent_id=self.agent_id,  # Filter by own work
                project_id=project_id,
                collections=["tasks", "knowledge_base"],  # Components + best practices
                top_k=5
            )

            logger.info(f"Frontend Engineer retrieved {sum(len(v.get('ids', [])) for v in results.values())} items")
            return results

        except Exception as e:
            logger.error(f"Error in Frontend Engineer retrieval strategy: {e}")
            return {}


class DesignerStrategy(AgentRetrievalStrategy):
    """Designer: Focus on design patterns and UI/UX guidelines."""

    async def retrieve_context(
        self,
        query: str,
        project_id: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Retrieve design patterns and guidelines."""
        try:
            # Retrieve own past work + shared knowledge
            results = await self.rag_service.retrieve_context(
                query=query,
                agent_id=self.agent_id,  # Filter by own work
                project_id=project_id,
                collections=["tasks", "knowledge_base"],  # Designs + guidelines
                top_k=5
            )

            logger.info(f"Designer retrieved {sum(len(v.get('ids', [])) for v in results.values())} items")
            return results

        except Exception as e:
            logger.error(f"Error in Designer retrieval strategy: {e}")
            return {}


# Strategy registry
STRATEGIES = {
    AgentType.CEO.value: CEOAgentStrategy,
    AgentType.CTO.value: CTOAgentStrategy,
    AgentType.PM.value: PMAgentStrategy,
    AgentType.HR.value: HRAgentStrategy,
    AgentType.BACKEND_ENGINEER.value: BackendEngineerStrategy,
    AgentType.FRONTEND_ENGINEER.value: FrontendEngineerStrategy,
    AgentType.DESIGNER.value: DesignerStrategy,
}


def get_retrieval_strategy(agent_id: str) -> AgentRetrievalStrategy:
    """
    Get the appropriate retrieval strategy for an agent.

    Args:
        agent_id: The agent ID

    Returns:
        Configured strategy instance
    """
    # Determine agent type from agent_id
    agent_type = agent_id

    strategy_class = STRATEGIES.get(agent_type)

    if strategy_class is None:
        logger.warning(f"No strategy for agent {agent_id}, using default")
        # Return generic strategy that uses agent's own work
        return AgentRetrievalStrategy(agent_id, agent_type)

    return strategy_class(agent_id, agent_type)


async def retrieve_agent_context(
    agent_id: str,
    query: str,
    project_id: Optional[str] = None,
    **kwargs
) -> Dict[str, Any]:
    """
    Retrieve context using the appropriate agent strategy.

    Args:
        agent_id: The agent ID
        query: The query string
        project_id: Optional project ID
        **kwargs: Additional parameters

    Returns:
        Retrieved context
    """
    try:
        strategy = get_retrieval_strategy(agent_id)
        return await strategy.retrieve_context(query, project_id, **kwargs)
    except Exception as e:
        logger.error(f"Error retrieving context for agent {agent_id}: {e}")
        return {}


async def format_agent_context(
    agent_id: str,
    results: Dict[str, Any]
) -> str:
    """
    Format context using agent's strategy.

    Args:
        agent_id: The agent ID
        results: Retrieved context results

    Returns:
        Formatted context string
    """
    try:
        strategy = get_retrieval_strategy(agent_id)
        return await strategy.format_for_prompt(results)
    except Exception as e:
        logger.error(f"Error formatting context for agent {agent_id}: {e}")
        return "No relevant context available"
