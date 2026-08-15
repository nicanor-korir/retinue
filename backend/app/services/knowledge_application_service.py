"""
Knowledge Application Service

Applies organizational knowledge to enrich agent contexts automatically.
Implements the context enrichment strategies from INTELLIGENT_KNOWLEDGE_BASE.md:
- Automatic context injection for agents
- User preference application
- Project/task-specific knowledge retrieval
- Conversation-aware knowledge suggestions
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from app.db.knowledge_models import (
    KnowledgeEntry,
    UserKnowledgeProfile,
    UserPreference,
    KnowledgeEntryType,
    UsageType
)
from app.db.models import Project, Task, Agent, Message
from app.services.knowledge_repository_service import get_knowledge_repository_service
from app.services.rag_embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class KnowledgeApplicationService:
    """
    Service for applying knowledge to enrich agent and user contexts.
    """

    def __init__(self):
        """Initialize the knowledge application service."""
        self.repository = get_knowledge_repository_service()
        self.embedding_service = get_embedding_service()

    # ===== AGENT CONTEXT ENRICHMENT =====

    async def enrich_agent_context(
        self,
        db: AsyncSession,
        agent_id: str,
        task: Optional[Task] = None,
        project: Optional[Project] = None,
        conversation_history: Optional[List[Message]] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Enrich agent context with relevant knowledge.

        Args:
            db: Database session
            agent_id: Agent ID
            task: Current task (optional)
            project: Current project (optional)
            conversation_history: Recent messages (optional)
            user_id: User ID for personalization (optional)

        Returns:
            Enriched context with relevant knowledge
        """
        try:
            enriched_context = {
                "relevant_knowledge": [],
                "user_preferences": [],
                "applicable_standards": [],
                "lessons_learned": [],
                "best_practices": []
            }

            # Build context query from available information
            context_query = self._build_context_query(task, project, conversation_history)

            if not context_query:
                return enriched_context

            # Retrieve relevant knowledge
            knowledge_results = await self.repository.hybrid_search(
                db=db,
                query=context_query,
                user_id=user_id,
                agent_id=agent_id,
                top_k=15,
                include_relations=True
            )

            # Categorize by type
            for result in knowledge_results:
                entry_type = result.get("entry_type")

                if entry_type == KnowledgeEntryType.PREFERENCE.value:
                    enriched_context["user_preferences"].append(result)
                elif entry_type == KnowledgeEntryType.STANDARD.value:
                    enriched_context["applicable_standards"].append(result)
                elif entry_type == KnowledgeEntryType.LESSON_LEARNED.value:
                    enriched_context["lessons_learned"].append(result)
                elif entry_type == KnowledgeEntryType.BEST_PRACTICE.value:
                    enriched_context["best_practices"].append(result)
                else:
                    enriched_context["relevant_knowledge"].append(result)

            # Add user-specific preferences if available
            if user_id:
                user_prefs = await self._get_user_preferences(db, user_id, agent_id)
                enriched_context["user_preferences"].extend(user_prefs)

            # Log usage for top results
            for result in knowledge_results[:5]:  # Top 5
                await self.repository.log_knowledge_usage(
                    db=db,
                    entry_id=UUID(result["entry_id"]),
                    agent_id=agent_id,
                    usage_type=UsageType.RETRIEVED_FOR_CONTEXT,
                    context={
                        "task_id": str(task.task_id) if task else None,
                        "project_id": str(project.project_id) if project else None
                    }
                )

            logger.info(
                f"Enriched context for agent {agent_id}: "
                f"{len(knowledge_results)} knowledge items retrieved"
            )

            return enriched_context

        except Exception as e:
            logger.error(f"Error enriching agent context: {e}", exc_info=True)
            return {
                "relevant_knowledge": [],
                "user_preferences": [],
                "applicable_standards": [],
                "lessons_learned": [],
                "best_practices": []
            }

    def _build_context_query(
        self,
        task: Optional[Task],
        project: Optional[Project],
        conversation_history: Optional[List[Message]]
    ) -> str:
        """Build search query from context."""
        query_parts = []

        if project:
            query_parts.append(project.name)
            if project.description:
                query_parts.append(project.description[:200])

        if task:
            query_parts.append(task.title)
            if task.description:
                query_parts.append(task.description[:200])

        if conversation_history and len(conversation_history) > 0:
            # Get recent messages
            recent_messages = conversation_history[-3:]
            for msg in recent_messages:
                query_parts.append(msg.content[:100])

        return " ".join(query_parts)[:1000]  # Limit total length

    async def _get_user_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        agent_id: str
    ) -> List[Dict[str, Any]]:
        """Get user preferences relevant to current agent."""
        try:
            query = select(UserPreference).where(
                and_(
                    UserPreference.user_id == user_id,
                    UserPreference.confidence >= 0.7  # Only high-confidence prefs
                )
            ).limit(10)

            result = await db.execute(query)
            preferences = result.scalars().all()

            formatted = []
            for pref in preferences:
                formatted.append({
                    "entry_id": str(pref.preference_id),
                    "title": f"User preference: {pref.key}",
                    "summary": f"{pref.category} preference",
                    "content": str(pref.value),
                    "entry_type": "preference",
                    "confidence": pref.confidence,
                    "times_confirmed": pref.times_confirmed
                })

            return formatted

        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            return []

    # ===== PROMPT AUGMENTATION =====

    async def augment_agent_prompt(
        self,
        db: AsyncSession,
        base_prompt: str,
        enriched_context: Dict[str, Any],
        max_knowledge_items: int = 5
    ) -> str:
        """
        Augment agent's system prompt with relevant knowledge.

        Args:
            db: Database session
            base_prompt: Original system prompt
            enriched_context: Enriched context from enrich_agent_context
            max_knowledge_items: Max knowledge items to include

        Returns:
            Augmented prompt
        """
        try:
            knowledge_section = self._format_knowledge_for_prompt(
                enriched_context,
                max_knowledge_items
            )

            if not knowledge_section:
                return base_prompt

            # Insert knowledge before the main instructions
            augmented_prompt = f"""{base_prompt}

{knowledge_section}

Use the above organizational knowledge to inform your responses and decisions.
"""

            return augmented_prompt

        except Exception as e:
            logger.error(f"Error augmenting prompt: {e}")
            return base_prompt

    def _format_knowledge_for_prompt(
        self,
        enriched_context: Dict[str, Any],
        max_items: int
    ) -> str:
        """Format knowledge for inclusion in prompt."""
        sections = []

        # User Preferences
        if enriched_context.get("user_preferences"):
            prefs = enriched_context["user_preferences"][:3]
            pref_text = "\n".join([
                f"- {p['title']}: {p.get('summary', p.get('content', ''))[:100]}"
                for p in prefs
            ])
            sections.append(f"## USER PREFERENCES\n{pref_text}")

        # Standards
        if enriched_context.get("applicable_standards"):
            standards = enriched_context["applicable_standards"][:2]
            std_text = "\n".join([
                f"- {s['title']}: {s.get('summary', '')[:150]}"
                for s in standards
            ])
            sections.append(f"## ORGANIZATIONAL STANDARDS\n{std_text}")

        # Best Practices
        if enriched_context.get("best_practices"):
            practices = enriched_context["best_practices"][:2]
            bp_text = "\n".join([
                f"- {bp['title']}: {bp.get('summary', '')[:150]}"
                for bp in practices
            ])
            sections.append(f"## BEST PRACTICES\n{bp_text}")

        # Lessons Learned
        if enriched_context.get("lessons_learned"):
            lessons = enriched_context["lessons_learned"][:2]
            lesson_text = "\n".join([
                f"- {l['title']}: {l.get('summary', '')[:150]}"
                for l in lessons
            ])
            sections.append(f"## LESSONS LEARNED\n{lesson_text}")

        # General Knowledge
        if enriched_context.get("relevant_knowledge"):
            knowledge = enriched_context["relevant_knowledge"][:max_items]
            knowledge_text = "\n".join([
                f"- {k['title']}: {k.get('summary', '')[:150]}"
                for k in knowledge
            ])
            sections.append(f"## RELEVANT KNOWLEDGE\n{knowledge_text}")

        if not sections:
            return ""

        return f"""
## ORGANIZATIONAL KNOWLEDGE CONTEXT

The following knowledge from past projects and interactions is relevant to your current task:

{chr(10).join(sections)}
"""

    # ===== CONVERSATION SUGGESTIONS =====

    async def get_conversation_suggestions(
        self,
        db: AsyncSession,
        conversation_id: UUID,
        recent_messages: List[Message],
        user_id: Optional[UUID] = None
    ) -> List[Dict[str, Any]]:
        """
        Get knowledge suggestions relevant to ongoing conversation.

        Args:
            db: Database session
            conversation_id: Conversation ID
            recent_messages: Recent messages in conversation
            user_id: User ID (optional)

        Returns:
            List of suggested knowledge entries
        """
        try:
            if not recent_messages:
                return []

            # Extract key topics from recent messages
            conversation_text = " ".join([
                msg.content for msg in recent_messages[-5:]
            ])

            # Search for relevant knowledge
            suggestions = await self.repository.hybrid_search(
                db=db,
                query=conversation_text,
                user_id=user_id,
                filters={
                    "min_quality": 0.7,  # Only high-quality suggestions
                },
                top_k=5
            )

            # Filter out already-used knowledge
            # (In production, track which knowledge was already suggested in this conversation)

            return suggestions

        except Exception as e:
            logger.error(f"Error getting conversation suggestions: {e}")
            return []

    # ===== TASK-SPECIFIC KNOWLEDGE =====

    async def get_task_relevant_knowledge(
        self,
        db: AsyncSession,
        task: Task,
        project: Optional[Project] = None
    ) -> Dict[str, Any]:
        """
        Get knowledge specifically relevant to a task.

        Args:
            db: Database session
            task: Task to get knowledge for
            project: Parent project (optional)

        Returns:
            Dict of task-relevant knowledge
        """
        try:
            # Build task query
            task_query = f"{task.title} {task.description or ''}"
            if project:
                task_query = f"{project.name} {task_query}"

            # Search with task-specific filters
            filters = {
                "min_quality": 0.6,
            }

            # Add task-specific entry types
            if "design" in task.title.lower() or "ui" in task.title.lower():
                # Prefer design patterns
                pass  # Could filter by tags or entry types

            knowledge = await self.repository.hybrid_search(
                db=db,
                query=task_query,
                filters=filters,
                top_k=10,
                include_relations=True
            )

            # Categorize knowledge
            categorized = {
                "solutions": [k for k in knowledge if k["entry_type"] == "solution"],
                "patterns": [k for k in knowledge if k["entry_type"] == "pattern"],
                "templates": [k for k in knowledge if k["entry_type"] == "template"],
                "lessons": [k for k in knowledge if k["entry_type"] == "lesson_learned"],
                "other": [k for k in knowledge if k["entry_type"] not in ["solution", "pattern", "template", "lesson_learned"]]
            }

            return categorized

        except Exception as e:
            logger.error(f"Error getting task-relevant knowledge: {e}")
            return {
                "solutions": [],
                "patterns": [],
                "templates": [],
                "lessons": [],
                "other": []
            }

    # ===== PROJECT INITIALIZATION =====

    async def initialize_project_knowledge(
        self,
        db: AsyncSession,
        project: Project
    ) -> Dict[str, Any]:
        """
        Initialize knowledge context for a new project.

        Args:
            db: Database session
            project: New project

        Returns:
            Initial knowledge context
        """
        try:
            # Find similar past projects
            project_query = f"{project.name} {project.description or ''}"

            similar_projects = await self.repository.hybrid_search(
                db=db,
                query=project_query,
                filters={
                    "entry_type": KnowledgeEntryType.PATTERN.value,
                    "min_quality": 0.7
                },
                top_k=5
            )

            # Get project-type specific templates
            templates = await self._get_project_templates(db, project)

            # Get relevant standards
            standards = await self.repository.hybrid_search(
                db=db,
                query=project_query,
                filters={
                    "entry_type": KnowledgeEntryType.STANDARD.value
                },
                top_k=5
            )

            return {
                "similar_projects": similar_projects,
                "templates": templates,
                "standards": standards
            }

        except Exception as e:
            logger.error(f"Error initializing project knowledge: {e}")
            return {
                "similar_projects": [],
                "templates": [],
                "standards": []
            }

    async def _get_project_templates(
        self,
        db: AsyncSession,
        project: Project
    ) -> List[Dict[str, Any]]:
        """Get project-type specific templates."""
        try:
            query = select(KnowledgeEntry).where(
                and_(
                    KnowledgeEntry.entry_type == KnowledgeEntryType.TEMPLATE,
                    KnowledgeEntry.quality_score >= 0.7
                )
            ).limit(5)

            result = await db.execute(query)
            entries = result.scalars().all()

            # Format as dicts
            return [{
                "entry_id": str(e.entry_id),
                "title": e.title,
                "summary": e.summary,
                "content_excerpt": e.content[:200]
            } for e in entries]

        except Exception as e:
            logger.error(f"Error getting project templates: {e}")
            return []


# Singleton instance
_knowledge_application_service: Optional[KnowledgeApplicationService] = None


def get_knowledge_application_service() -> KnowledgeApplicationService:
    """Get or create singleton knowledge application service."""
    global _knowledge_application_service
    if _knowledge_application_service is None:
        _knowledge_application_service = KnowledgeApplicationService()
    return _knowledge_application_service
