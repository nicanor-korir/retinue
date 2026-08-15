"""Dynamic Prompt Builder Service for creating context-aware system prompts.

This service builds enhanced system prompts for agents by injecting:
- Business domain context
- Current conversation context
- Historical context from RAG
- Project/task specific information
"""

import logging
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Agent, Project, Task
from app.services.business_domain_service import BusinessDomainService
from app.services.rag_service import RAGService

logger = logging.getLogger(__name__)


class DynamicPromptBuilder:
    """Build context-aware system prompts for agents."""

    BASE_TEMPLATE = """You are {agent_name}, {agent_role} at Retinue AI.

{business_context}

{conversation_context}

{historical_context}

{interaction_guidelines}
"""

    def __init__(
        self,
        business_domain_service: Optional[BusinessDomainService] = None,
        rag_service: Optional[RAGService] = None
    ):
        """
        Initialize dynamic prompt builder.

        Args:
            business_domain_service: Business domain service instance
            rag_service: RAG service instance
        """
        self.business_service = business_domain_service or BusinessDomainService()
        self.rag_service = rag_service or RAGService()

    async def build_enhanced_prompt(
        self,
        agent: Agent,
        conversation_id: str,
        extracted_context: Dict,
        db: AsyncSession
    ) -> str:
        """
        Build complete enhanced prompt for agent.

        Args:
            agent: The agent responding
            conversation_id: Current conversation ID
            extracted_context: Context from ContextIntelligenceService
            db: Database session

        Returns:
            Enhanced system prompt string
        """
        # Start with agent's base system prompt (if exists)
        base_prompt = agent.system_prompt or ""

        # Build sections
        business_context = await self._build_business_context(agent, extracted_context, db)
        conversation_context = await self._build_conversation_context(
            conversation_id, extracted_context, db
        )
        historical_context = await self._build_historical_context(
            agent, extracted_context, db
        )
        interaction_guidelines = self._build_interaction_guidelines(agent)

        # Render template
        enhanced_prompt = self.BASE_TEMPLATE.format(
            agent_name=agent.name,
            agent_role=agent.role,
            business_context=business_context,
            conversation_context=conversation_context,
            historical_context=historical_context,
            interaction_guidelines=interaction_guidelines
        )

        # Prepend base prompt if exists
        if base_prompt:
            enhanced_prompt = f"{base_prompt}\n\n{enhanced_prompt}"

        # Optimize token count (keep under 2000 tokens for system prompt)
        enhanced_prompt = self._optimize_prompt(enhanced_prompt, max_tokens=2000)

        return enhanced_prompt

    async def _build_business_context(
        self,
        agent: Agent,
        extracted_context: Dict,
        db: AsyncSession
    ) -> str:
        """Build business domain context section."""
        try:
            # Get all departments for the agent (supports multi-department)
            from app.agents.agent_registry import AgentRegistry

            # Get departments from agent's metadata or default to agent.department
            agent_departments = []
            if hasattr(agent, 'meta_data') and agent.meta_data:
                agent_departments = agent.meta_data.get('departments', [])

            # Fallback to single department if no departments array
            if not agent_departments and hasattr(agent, 'department'):
                agent_departments = [agent.department]

            # Build query with all departments for richer context
            dept_query = " ".join(agent_departments) if agent_departments else agent.department
            query = f"{agent.role} {dept_query}"

            # Get relevant business knowledge
            knowledge_docs = await self.business_service.get_relevant_knowledge(
                query=query,
                limit=3
            )

            if not knowledge_docs:
                return ""

            context_parts = ["BUSINESS CONTEXT:"]

            # Add department context if multi-department
            if len(agent_departments) > 1:
                context_parts.append(f"- Your role spans {len(agent_departments)} departments: {', '.join(agent_departments)}")

            for doc in knowledge_docs:
                title = doc.get("title", "")
                summary = doc.get("summary", "")
                if title and summary:
                    context_parts.append(f"- {title}: {summary}")

            return "\n".join(context_parts) if len(context_parts) > 1 else ""

        except Exception:
            return ""

    async def _build_conversation_context(
        self,
        conversation_id: str,
        extracted_context: Dict,
        db: AsyncSession
    ) -> str:
        """Build current conversation context section."""
        try:
            from app.db.conversation_models import Conversation
            from sqlalchemy import select

            entities = extracted_context.get("entities", {})
            intent = extracted_context.get("intent", "discussion")

            context_parts = ["CURRENT CONVERSATION CONTEXT:"]
            context_parts.append(f"- User intent: {intent}")

            # Get the conversation to check for associated project
            result = await db.execute(
                select(Conversation).where(Conversation.conversation_id == conversation_id)
            )
            conversation = result.scalar_one_or_none()

            # ALWAYS include project context if conversation has a project
            if conversation and conversation.project_id:
                project = await self._get_project(str(conversation.project_id), db)
                if project:
                    context_parts.append(f"\nPROJECT CONTEXT:")
                    context_parts.append(f"- Project: {project.name}")
                    context_parts.append(f"- Status: {project.status}")
                    if project.description:
                        # Truncate description to keep prompt concise
                        desc = project.description[:200] + "..." if len(project.description) > 200 else project.description
                        context_parts.append(f"- Description: {desc}")

                    # Get project tasks
                    project_tasks = await self._get_project_tasks(str(conversation.project_id), db)
                    if project_tasks:
                        context_parts.append(f"\nPROJECT TASKS ({len(project_tasks)} tasks):")
                        for task in project_tasks[:5]:  # Show up to 5 tasks
                            context_parts.append(
                                f"  • {task.title} - {task.status} "
                                f"(Priority: {task.priority}, Assigned: {task.assigned_agent_id or 'Unassigned'})"
                            )
                        if len(project_tasks) > 5:
                            context_parts.append(f"  ... and {len(project_tasks) - 5} more tasks")

            # Add additional detected project context if different from conversation project
            projects = entities.get("projects", [])
            for project_id in projects[:2]:  # Limit to 2 projects
                if not conversation or str(project_id) != str(conversation.project_id):
                    project = await self._get_project(project_id, db)
                    if project:
                        context_parts.append(
                            f"- Also discussing project: {project.name} (Status: {project.status})"
                        )

            # Add task context if detected
            tasks = entities.get("tasks", [])
            for task_id in tasks[:2]:  # Limit to 2 tasks
                task = await self._get_task(task_id, db)
                if task:
                    context_parts.append(
                        f"- Discussing task: {task.title} (Status: {task.status})"
                    )

            # Add agent mentions
            agents = entities.get("agents", [])
            if agents:
                context_parts.append(f"- Mentioned agents: {', '.join(agents[:3])}")

            # Only return if we have meaningful context
            return "\n".join(context_parts) if len(context_parts) > 2 else ""

        except Exception as e:
            logger.error(f"Error building conversation context: {e}", exc_info=True)
            return ""

    async def _build_historical_context(
        self,
        agent: Agent,
        extracted_context: Dict,
        db: AsyncSession
    ) -> str:
        """Build historical context section using RAG."""
        try:
            # Get query from extracted context
            entities = extracted_context.get("entities", {})
            query_parts = []

            # Build query from entities
            if entities.get("projects"):
                query_parts.append(f"project {entities['projects'][0]}")
            if entities.get("tasks"):
                query_parts.append(f"task {entities['tasks'][0]}")

            # If no entities, use semantic context
            if not query_parts:
                semantic = extracted_context.get("semantic", {})
                summary = semantic.get("summary", "")
                if summary:
                    query_parts.append(summary[:100])

            if not query_parts:
                return ""

            query = " ".join(query_parts)

            # Retrieve relevant context from RAG
            rag_results = await self.rag_service.retrieve_context(
                query=query,
                collections=["tasks", "decisions"],
                top_k=3
            )

            if not rag_results:
                return ""

            context_parts = ["RELEVANT HISTORICAL CONTEXT:"]

            # Process results from each collection
            for collection_name, results in rag_results.items():
                for result in results[:2]:  # Limit to 2 per collection
                    doc = result.get("document", "")
                    score = result.get("score", 0)
                    metadata = result.get("metadata", {})

                    # Create summary based on collection type
                    if collection_name == "tasks":
                        title = metadata.get("title", "Related task")
                        summary = f"{title}: {doc[:100]}..."
                    elif collection_name == "decisions":
                        summary = f"Past decision: {doc[:100]}..."
                    else:
                        summary = doc[:100] + "..."

                    context_parts.append(f"- {summary} (Relevance: {score:.2f})")

            return "\n".join(context_parts) if len(context_parts) > 1 else ""

        except Exception:
            return ""

    def _build_interaction_guidelines(self, agent: Agent) -> str:
        """Build interaction guidelines section."""
        guidelines = [
            "INTERACTION GUIDELINES:",
            "- Be concise and direct in your responses",
            "- Provide actionable insights when possible",
            "- Ask clarifying questions if context is unclear",
            "- Reference specific tasks/projects when relevant",
            "- Use your domain expertise to provide valuable guidance",
            "",
            "MULTI-AGENT CONVERSATION RULES (CRITICAL):",
            "- NEVER announce that an agent 'has joined the conversation' - the system handles join notifications automatically",
            "- NEVER write messages like '**Agent Name** has joined' or 'Agent X is now here' - this is false information",
            "- NEVER pretend to invite, approve, or add agents to the conversation - you cannot do this",
            "- If you think another agent's expertise would be helpful, simply say 'This topic might benefit from [role]'s input' - the system will handle agent suggestions",
            "- Only speak for yourself - never roleplay or speak as other agents",
            "- If asked about bringing in other agents, explain that the system automatically detects when specialists are needed"
        ]

        # Add role-specific guidelines
        role = agent.role.lower()
        if "manager" in role:
            guidelines.append("- Focus on planning, coordination, and stakeholder communication")
        elif "developer" in role or "engineer" in role:
            guidelines.append("- Focus on technical implementation and code quality")
        elif "designer" in role:
            guidelines.append("- Focus on user experience and visual consistency")
        elif "qa" in role or "tester" in role:
            guidelines.append("- Focus on quality assurance and testing coverage")

        return "\n".join(guidelines)

    def _optimize_prompt(self, prompt: str, max_tokens: int) -> str:
        """
        Optimize prompt to fit within token limit.

        Simple implementation: truncate if too long.
        Better implementation: prioritize sections and intelligently compress.

        Args:
            prompt: The prompt to optimize
            max_tokens: Maximum token count

        Returns:
            Optimized prompt
        """
        # Rough estimate: 4 characters per token
        max_chars = max_tokens * 4

        if len(prompt) <= max_chars:
            return prompt

        # Truncate with message
        return prompt[:max_chars] + "\n\n[Context truncated to fit token limit]"

    async def _get_project(self, project_id: str, db: AsyncSession) -> Optional[Project]:
        """Get project by ID."""
        try:
            result = await db.execute(
                select(Project).where(Project.project_id == project_id)
            )
            return result.scalar_one_or_none()
        except Exception:
            return None

    async def _get_task(self, task_id: str, db: AsyncSession) -> Optional[Task]:
        """Get task by ID."""
        try:
            result = await db.execute(
                select(Task).where(Task.task_id == task_id)
            )
            return result.scalar_one_or_none()
        except Exception:
            return None

    async def _get_project_tasks(self, project_id: str, db: AsyncSession) -> List[Task]:
        """Get all tasks for a project."""
        try:
            from uuid import UUID
            result = await db.execute(
                select(Task)
                .where(Task.project_id == UUID(project_id))
                .order_by(Task.priority.desc(), Task.created_at.desc())
            )
            return result.scalars().all()
        except Exception:
            return []


# Singleton instance
_dynamic_prompt_builder = None


def get_dynamic_prompt_builder() -> DynamicPromptBuilder:
    """Get singleton instance of dynamic prompt builder."""
    global _dynamic_prompt_builder
    if _dynamic_prompt_builder is None:
        _dynamic_prompt_builder = DynamicPromptBuilder()
    return _dynamic_prompt_builder
