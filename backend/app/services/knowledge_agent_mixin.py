"""
Knowledge-Aware Agent Mixin

Provides easy integration of the intelligent knowledge system into existing agents.
Agents can inherit from this mixin to automatically gain knowledge-aware capabilities.
"""

import logging
from typing import List, Dict, Any, Optional
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Task, Project
from app.services.knowledge_application_service import get_knowledge_application_service
from app.services.knowledge_extraction_service import get_knowledge_extraction_service

logger = logging.getLogger(__name__)


class KnowledgeAwareMixin:
    """
    Mixin to make agents knowledge-aware.

    Usage:
        class MyAgent(BaseAgent, KnowledgeAwareMixin):
            async def work_on_task(self, db, task):
                # Get knowledge context
                context = await self.get_knowledge_context(db, task=task)

                # Augment prompt with knowledge
                prompt = await self.augment_prompt_with_knowledge(
                    db, self.system_prompt, task=task
                )

                # ... rest of agent logic ...
    """

    def __init__(self):
        """Initialize knowledge-aware mixin."""
        self.knowledge_app_service = get_knowledge_application_service()
        self.knowledge_extraction_service = get_knowledge_extraction_service()

    # ===== CONTEXT ENRICHMENT =====

    async def get_knowledge_context(
        self,
        db: AsyncSession,
        task: Optional[Task] = None,
        project: Optional[Project] = None,
        user_id: Optional[UUID] = None
    ) -> Dict[str, Any]:
        """
        Get relevant knowledge context for the agent's current work.

        Args:
            db: Database session
            task: Current task (optional)
            project: Current project (optional)
            user_id: User ID for personalization (optional)

        Returns:
            Enriched context dict with categorized knowledge
        """
        try:
            agent_id = getattr(self, 'agent_id', 'unknown')

            context = await self.knowledge_app_service.enrich_agent_context(
                db=db,
                agent_id=agent_id,
                task=task,
                project=project,
                user_id=user_id
            )

            logger.info(
                f"Agent {agent_id} retrieved knowledge context: "
                f"{len(context.get('relevant_knowledge', []))} items"
            )

            return context

        except Exception as e:
            logger.error(f"Error getting knowledge context: {e}")
            return {
                "relevant_knowledge": [],
                "user_preferences": [],
                "applicable_standards": [],
                "lessons_learned": [],
                "best_practices": []
            }

    async def augment_prompt_with_knowledge(
        self,
        db: AsyncSession,
        base_prompt: str,
        task: Optional[Task] = None,
        project: Optional[Project] = None,
        user_id: Optional[UUID] = None,
        max_knowledge_items: int = 5
    ) -> str:
        """
        Augment agent's prompt with relevant knowledge.

        Args:
            db: Database session
            base_prompt: Original system prompt
            task: Current task (optional)
            project: Current project (optional)
            user_id: User ID (optional)
            max_knowledge_items: Max knowledge items to include

        Returns:
            Augmented prompt with knowledge context
        """
        try:
            # Get enriched context
            context = await self.get_knowledge_context(
                db=db,
                task=task,
                project=project,
                user_id=user_id
            )

            # Augment prompt
            augmented_prompt = await self.knowledge_app_service.augment_agent_prompt(
                db=db,
                base_prompt=base_prompt,
                enriched_context=context,
                max_knowledge_items=max_knowledge_items
            )

            return augmented_prompt

        except Exception as e:
            logger.error(f"Error augmenting prompt: {e}")
            return base_prompt

    # ===== KNOWLEDGE EXTRACTION =====

    async def extract_knowledge_from_work(
        self,
        db: AsyncSession,
        task: Task,
        output: str,
        success: bool = True
    ) -> None:
        """
        Extract knowledge from completed work.

        Call this after completing a task to automatically extract learnings.

        Args:
            db: Database session
            task: Completed task
            output: Task output/result
            success: Whether task was successful
        """
        try:
            agent_id = getattr(self, 'agent_id', 'unknown')

            # Prepare extraction context
            extraction_context = {
                "task_id": task.task_id,
                "project_id": task.project_id,
                "agent_id": agent_id,
                "success": success
            }

            # Extract knowledge
            from app.db.knowledge_models import ExtractionTriggerType

            # Build extraction content
            content = f"""
Task: {task.title}
Description: {task.description or 'N/A'}
Output: {output[:1000]}  # Limit length
Success: {success}
"""

            extraction_data = {
                "type": "lesson_learned" if not success else "solution",
                "title": f"{'Failed' if not success else 'Completed'}: {task.title}",
                "summary": task.description[:200] if task.description else "",
                "content": content,
                "confidence": 0.8 if success else 0.6,
                "novelty": 0.5,
                "relevance": 0.7,
                "tags": [agent_id, "task_completion"],
                "applicable_scenarios": [task.title]
            }

            # Create extraction candidate
            candidate = await self.knowledge_extraction_service.create_extraction_candidate(
                db=db,
                extraction_data=extraction_data,
                trigger_type=ExtractionTriggerType.PROBLEM_SOLVED if success else ExtractionTriggerType.CORRECTION_MADE,
                source_context=extraction_context
            )

            if candidate:
                logger.info(
                    f"Agent {agent_id} created extraction candidate {candidate.candidate_id} "
                    f"from task {task.task_id}"
                )

        except Exception as e:
            logger.error(f"Error extracting knowledge from work: {e}")

    # ===== HELPER METHODS =====

    async def search_knowledge(
        self,
        db: AsyncSession,
        query: str,
        filters: Optional[Dict[str, Any]] = None,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search knowledge base.

        Args:
            db: Database session
            query: Search query
            filters: Optional filters
            top_k: Number of results

        Returns:
            List of knowledge entries
        """
        try:
            from app.services.knowledge_repository_service import get_knowledge_repository_service

            repository = get_knowledge_repository_service()
            agent_id = getattr(self, 'agent_id', None)

            results = await repository.hybrid_search(
                db=db,
                query=query,
                agent_id=agent_id,
                filters=filters,
                top_k=top_k
            )

            return results

        except Exception as e:
            logger.error(f"Error searching knowledge: {e}")
            return []

    async def get_task_knowledge(
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
            Categorized task-relevant knowledge
        """
        try:
            knowledge = await self.knowledge_app_service.get_task_relevant_knowledge(
                db=db,
                task=task,
                project=project
            )

            return knowledge

        except Exception as e:
            logger.error(f"Error getting task knowledge: {e}")
            return {
                "solutions": [],
                "patterns": [],
                "templates": [],
                "lessons": [],
                "other": []
            }

    async def apply_user_preferences(
        self,
        db: AsyncSession,
        user_id: UUID,
        response: str
    ) -> str:
        """
        Apply user preferences to format response.

        Args:
            db: Database session
            user_id: User ID
            response: Original response

        Returns:
            Formatted response according to user preferences
        """
        try:
            from app.db.knowledge_models import UserKnowledgeProfile
            from sqlalchemy import select

            # Get user profile
            query = select(UserKnowledgeProfile).where(
                UserKnowledgeProfile.user_id == user_id
            )

            result = await db.execute(query)
            profile = result.scalar_one_or_none()

            if not profile:
                return response

            # Apply preferences
            # (Simplified - in production, use more sophisticated formatting)

            # Response length preference
            if profile.preferred_response_length == "brief" and len(response) > 500:
                # Shorten response (simplified)
                response = response[:500] + "..."

            # Technical depth
            # (Would need NLP to adjust complexity level)

            return response

        except Exception as e:
            logger.error(f"Error applying user preferences: {e}")
            return response


# Helper function for easy integration
def make_agent_knowledge_aware(agent_class):
    """
    Decorator to make an agent class knowledge-aware.

    Usage:
        @make_agent_knowledge_aware
        class MyAgent(BaseAgent):
            ...
    """
    class KnowledgeAwareAgent(agent_class, KnowledgeAwareMixin):
        def __init__(self, *args, **kwargs):
            agent_class.__init__(self, *args, **kwargs)
            KnowledgeAwareMixin.__init__(self)

    KnowledgeAwareAgent.__name__ = agent_class.__name__
    KnowledgeAwareAgent.__qualname__ = agent_class.__qualname__

    return KnowledgeAwareAgent
