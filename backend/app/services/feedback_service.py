"""Service for managing user feedback and context updates."""
import logging
from typing import Dict, Any, Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.db.feedback_models import (
    ProjectFeedback, TaskFeedback, AgentFeedback, ContextUpdate, SystemLearning,
    FeedbackType, FeedbackSource, FeedbackStatus
)
from app.db.models import Project, Task, Agent, Decision, Message, MessageType, Priority
from app.exceptions import ValidationError, NotFoundError, ConflictError
from app.utils.db_error_handler import DatabaseErrorHandler, handle_database_error

logger = logging.getLogger(__name__)


class FeedbackService:
    """Service for managing feedback and context."""

    def __init__(self, session: AsyncSession):
        """Initialize feedback service.

        Args:
            session: Database session
        """
        self.session = session

    # ==================== PROJECT FEEDBACK ====================

    async def create_project_feedback(
        self,
        project_id: UUID,
        feedback_type: FeedbackType,
        title: str,
        description: str,
        quality_rating: Optional[int] = None,
        satisfaction_rating: Optional[int] = None,
        confidence_level: Optional[int] = None,
        suggested_actions: Optional[List[str]] = None,
        priority: str = "medium",
        context: Optional[Dict[str, Any]] = None,
        created_by_user: Optional[str] = None,
    ) -> ProjectFeedback:
        """Create feedback for a project.

        Args:
            project_id: Project to provide feedback on
            feedback_type: Type of feedback
            title: Brief feedback title
            description: Detailed feedback
            quality_rating: 1-5 rating
            satisfaction_rating: 1-5 rating
            confidence_level: Confidence in the feedback
            suggested_actions: List of suggested actions
            priority: low, medium, high, critical
            context: Additional context
            created_by_user: User creating feedback

        Returns:
            Created ProjectFeedback instance

        Raises:
            ValidationError: If project doesn't exist
            DatabaseError: If database operation fails
        """
        # Validate project exists
        project = await self.session.get(Project, project_id)
        if not project:
            raise NotFoundError(
                message=f"Project '{project_id}' not found.",
                resource_type="Project",
                resource_id=str(project_id)
            )

        # Validate title and description
        if not title or not title.strip():
            raise ValidationError(
                message="Feedback title is required.",
                field="title"
            )

        if not description or not description.strip():
            raise ValidationError(
                message="Feedback description is required.",
                field="description"
            )

        # Validate ratings if provided
        if quality_rating is not None and (quality_rating < 1 or quality_rating > 5):
            raise ValidationError(
                message="Quality rating must be between 1 and 5.",
                field="quality_rating"
            )

        if satisfaction_rating is not None and (satisfaction_rating < 1 or satisfaction_rating > 5):
            raise ValidationError(
                message="Satisfaction rating must be between 1 and 5.",
                field="satisfaction_rating"
            )

        # Create with error handling
        with DatabaseErrorHandler("create_project_feedback"):
            feedback = ProjectFeedback(
                project_id=project_id,
                feedback_type=feedback_type,
                source=FeedbackSource.USER,
                status=FeedbackStatus.PENDING,
                title=title,
                description=description,
                quality_rating=quality_rating,
                satisfaction_rating=satisfaction_rating,
                confidence_level=confidence_level,
                suggested_actions=suggested_actions or [],
                priority=priority,
                context=context or {},
                created_by_user=created_by_user,
            )

            self.session.add(feedback)
            await self.session.commit()
            await self.session.refresh(feedback)

            logger.info(f"Created project feedback {feedback.feedback_id} for project {project_id}")

            # Process feedback intelligently
            await self._process_project_feedback(feedback)

            return feedback

    async def _process_project_feedback(self, feedback: ProjectFeedback) -> None:
        """Process project feedback intelligently.

        Args:
            feedback: ProjectFeedback to process
        """
        try:
            # Update feedback status to acknowledged
            feedback.status = FeedbackStatus.ACKNOWLEDGED
            await self.session.commit()

            # Extract key insights from feedback
            insights = self._extract_insights(feedback.description)

            # If blocking issue, create escalation
            if feedback.feedback_type == FeedbackType.BLOCKING_ISSUE:
                await self._create_escalation_from_feedback(feedback)

            # If direction/enhancement, add as context
            if feedback.feedback_type in [FeedbackType.DIRECTION, FeedbackType.ENHANCEMENT]:
                await self._create_context_update(
                    entity_type="project",
                    entity_id=feedback.project_id,
                    title=feedback.title,
                    content=feedback.description,
                    related_feedback_id=feedback.feedback_id,
                    context_tags=self._infer_tags(feedback.feedback_type),
                )

            # Assign to project owner for action
            project = await self.session.get(Project, feedback.project_id)
            if project:
                feedback.assigned_to_agent_id = project.owner_agent_id
                await self.session.commit()

                # Send notification to agent
                await self._notify_agent_of_feedback(
                    project.owner_agent_id,
                    f"New feedback on project: {feedback.title}",
                    feedback.feedback_id,
                )

            logger.info(f"Processed project feedback {feedback.feedback_id}")

        except Exception as e:
            logger.error(f"Error processing project feedback: {e}")
            # Don't raise - feedback was created successfully

    # ==================== TASK FEEDBACK ====================

    async def create_task_feedback(
        self,
        task_id: UUID,
        project_id: Optional[UUID] = None,
        feedback_type: FeedbackType = FeedbackType.GENERAL,
        title: str = "",
        description: str = "",
        output_quality: Optional[int] = None,
        correctness: Optional[int] = None,
        completeness: Optional[int] = None,
        implementation_quality: Optional[int] = None,
        code_review_feedback: Optional[str] = None,
        suggested_improvements: Optional[List[str]] = None,
        action_items: Optional[List[str]] = None,
        priority: str = "medium",
        context: Optional[Dict[str, Any]] = None,
        created_by_user: Optional[str] = None,
    ) -> TaskFeedback:
        """Create feedback for a task.

        Args:
            task_id: Task to provide feedback on
            project_id: Parent project ID (optional, will be fetched from task if not provided)
            feedback_type: Type of feedback
            title: Brief title
            description: Detailed feedback
            output_quality: 1-5 rating
            correctness: 1-5 rating
            completeness: 1-5 rating
            implementation_quality: 1-5 rating
            code_review_feedback: Code review comments
            suggested_improvements: List of improvements
            action_items: List of action items
            priority: Priority level
            context: Additional context
            created_by_user: User creating feedback

        Returns:
            Created TaskFeedback instance
        """
        try:
            # If project_id not provided, fetch from task
            if project_id is None:
                task = await self.session.get(Task, task_id)
                if not task:
                    raise NotFoundError(
                        message=f"Task '{task_id}' not found.",
                        resource_type="Task",
                        resource_id=str(task_id)
                    )
                project_id = task.project_id

            feedback = TaskFeedback(
                task_id=task_id,
                project_id=project_id,
                feedback_type=feedback_type,
                source=FeedbackSource.USER,
                status=FeedbackStatus.PENDING,
                title=title,
                description=description,
                output_quality=output_quality,
                correctness=correctness,
                completeness=completeness,
                implementation_quality=implementation_quality,
                code_review_feedback=code_review_feedback,
                suggested_improvements=suggested_improvements or [],
                action_items=action_items or [],
                priority=priority,
                context=context or {},
                created_by_user=created_by_user,
            )

            self.session.add(feedback)
            await self.session.commit()
            await self.session.refresh(feedback)

            logger.info(f"Created task feedback {feedback.feedback_id} for task {task_id}")

            # Process feedback
            await self._process_task_feedback(feedback)

            return feedback

        except Exception as e:
            logger.error(f"Error creating task feedback: {e}")
            await self.session.rollback()
            raise

    async def _process_task_feedback(self, feedback: TaskFeedback) -> None:
        """Process task feedback intelligently.

        Args:
            feedback: TaskFeedback to process
        """
        try:
            feedback.status = FeedbackStatus.ACKNOWLEDGED
            await self.session.commit()

            # Get task to understand what was done
            task = await self.session.get(Task, feedback.task_id)
            if not task:
                return

            # Assess overall quality
            avg_quality = self._calculate_average_quality(
                feedback.output_quality,
                feedback.correctness,
                feedback.completeness,
                feedback.implementation_quality,
            )

            # If quality is low or issues found
            if avg_quality is not None and avg_quality < 3:
                # Create improvement plan
                await self._create_improvement_plan(feedback)

            # If has action items, create context
            if feedback.action_items:
                await self._create_context_update(
                    entity_type="task",
                    entity_id=feedback.task_id,
                    title=f"Action Items: {feedback.title}",
                    content="\n".join(feedback.action_items),
                    related_feedback_id=feedback.feedback_id,
                    context_tags=["action_items", "follow_up"],
                )

            # Assign to task agent
            feedback.assigned_to_agent_id = task.assigned_to_agent_id
            await self.session.commit()

            # Notify agent
            await self._notify_agent_of_feedback(
                task.assigned_to_agent_id,
                f"Feedback received on task: {feedback.title}",
                feedback.feedback_id,
            )

            logger.info(f"Processed task feedback {feedback.feedback_id}")

        except Exception as e:
            logger.error(f"Error processing task feedback: {e}")

    # ==================== AGENT FEEDBACK ====================

    async def create_agent_feedback(
        self,
        agent_id: str,
        feedback_type: FeedbackType,
        title: str,
        description: str,
        decision_quality: Optional[int] = None,
        execution_quality: Optional[int] = None,
        communication_clarity: Optional[int] = None,
        problem_solving: Optional[int] = None,
        efficiency: Optional[int] = None,
        behavior_observations: Optional[str] = None,
        recommended_improvements: Optional[List[str]] = None,
        strengths_noted: Optional[List[str]] = None,
        suggested_system_prompt_updates: Optional[str] = None,
        priority: str = "medium",
        related_task_id: Optional[UUID] = None,
        related_project_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None,
        created_by_user: Optional[str] = None,
    ) -> AgentFeedback:
        """Create feedback for an agent.

        Args:
            agent_id: Agent receiving feedback
            feedback_type: Type of feedback
            title: Brief title
            description: Detailed feedback
            decision_quality: 1-5 rating
            execution_quality: 1-5 rating
            communication_clarity: 1-5 rating
            problem_solving: 1-5 rating
            efficiency: 1-5 rating
            behavior_observations: Behavioral notes
            recommended_improvements: List of improvements
            strengths_noted: What the agent does well
            suggested_system_prompt_updates: Prompt changes
            priority: Priority level
            related_task_id: Related task if applicable
            related_project_id: Related project if applicable
            context: Additional context
            created_by_user: User creating feedback

        Returns:
            Created AgentFeedback instance
        """
        try:
            feedback = AgentFeedback(
                agent_id=agent_id,
                feedback_type=feedback_type,
                source=FeedbackSource.USER,
                status=FeedbackStatus.PENDING,
                title=title,
                description=description,
                decision_quality=decision_quality,
                execution_quality=execution_quality,
                communication_clarity=communication_clarity,
                problem_solving=problem_solving,
                efficiency=efficiency,
                behavior_observations=behavior_observations,
                recommended_improvements=recommended_improvements or [],
                strengths_noted=strengths_noted or [],
                suggested_system_prompt_updates=suggested_system_prompt_updates,
                priority=priority,
                related_task_id=related_task_id,
                related_project_id=related_project_id,
                context=context or {},
                created_by_user=created_by_user,
            )

            self.session.add(feedback)
            await self.session.commit()
            await self.session.refresh(feedback)

            logger.info(f"Created agent feedback {feedback.feedback_id} for agent {agent_id}")

            # Process feedback
            await self._process_agent_feedback(feedback)

            return feedback

        except Exception as e:
            logger.error(f"Error creating agent feedback: {e}")
            await self.session.rollback()
            raise

    async def _process_agent_feedback(self, feedback: AgentFeedback) -> None:
        """Process agent feedback for system learning.

        Args:
            feedback: AgentFeedback to process
        """
        try:
            feedback.acknowledged_by_system = True
            feedback.status = FeedbackStatus.ACKNOWLEDGED
            await self.session.commit()

            # Calculate overall performance
            avg_performance = self._calculate_average_quality(
                feedback.decision_quality,
                feedback.execution_quality,
                feedback.communication_clarity,
                feedback.problem_solving,
                feedback.efficiency,
            )

            # If suggested system prompt updates, create learning
            if feedback.suggested_system_prompt_updates:
                await self._create_system_learning(
                    learning_type="improvement",
                    title=f"Agent Enhancement: {feedback.title}",
                    description=feedback.suggested_system_prompt_updates,
                    source_feedback_ids=[str(feedback.feedback_id)],
                    affected_agent_ids=[feedback.agent_id],
                    system_prompt_update=feedback.suggested_system_prompt_updates,
                )

            # Store behavior insights as system learning
            if feedback.recommended_improvements or feedback.strengths_noted:
                await self._create_system_learning(
                    learning_type="pattern",
                    title=f"Agent Behavior Pattern: {feedback.title}",
                    description=feedback.description,
                    source_feedback_ids=[str(feedback.feedback_id)],
                    affected_agent_ids=[feedback.agent_id],
                )

            logger.info(f"Processed agent feedback {feedback.feedback_id}")

        except Exception as e:
            logger.error(f"Error processing agent feedback: {e}")

    # ==================== CONTEXT UPDATES ====================

    async def _create_context_update(
        self,
        entity_type: str,
        entity_id: UUID,
        title: str,
        content: str,
        context_tags: Optional[List[str]] = None,
        related_feedback_id: Optional[UUID] = None,
        source: str = "user",
        created_by_user: Optional[str] = None,
    ) -> ContextUpdate:
        """Create a context update for an entity.

        Args:
            entity_type: 'project', 'task', or 'agent'
            entity_id: ID of the entity
            title: Context title
            content: Context content
            context_tags: Tags for the context
            related_feedback_id: Related feedback ID
            source: Source of context
            created_by_user: User creating context

        Returns:
            Created ContextUpdate instance
        """
        try:
            context = ContextUpdate(
                entity_type=entity_type,
                entity_id=entity_id,
                title=title,
                content=content,
                context_tags=context_tags or [],
                related_feedback_id=related_feedback_id,
                source=source,
                created_by_user=created_by_user,
            )

            self.session.add(context)
            await self.session.commit()
            await self.session.refresh(context)

            logger.info(f"Created context update {context.context_id} for {entity_type} {entity_id}")
            return context

        except Exception as e:
            logger.error(f"Error creating context update: {e}")
            await self.session.rollback()
            raise

    # ==================== SYSTEM LEARNING ====================

    async def _create_system_learning(
        self,
        learning_type: str,
        title: str,
        description: str,
        source_feedback_ids: Optional[List[str]] = None,
        affected_agent_ids: Optional[List[str]] = None,
        affected_task_types: Optional[List[str]] = None,
        system_prompt_update: Optional[str] = None,
        priority: str = "medium",
    ) -> SystemLearning:
        """Create a system learning from feedback.

        Args:
            learning_type: Type of learning
            title: Learning title
            description: Learning description
            source_feedback_ids: Source feedback IDs
            affected_agent_ids: Which agents are affected
            affected_task_types: Which task types are affected
            system_prompt_update: System prompt changes
            priority: Priority level

        Returns:
            Created SystemLearning instance
        """
        try:
            learning = SystemLearning(
                learning_type=learning_type,
                title=title,
                description=description,
                source_feedback_ids=source_feedback_ids or [],
                affected_agent_ids=affected_agent_ids or [],
                affected_task_types=affected_task_types or [],
                system_prompt_update=system_prompt_update,
                status="proposed",
                priority=priority,
            )

            self.session.add(learning)
            await self.session.commit()
            await self.session.refresh(learning)

            logger.info(f"Created system learning {learning.learning_id}")
            return learning

        except Exception as e:
            logger.error(f"Error creating system learning: {e}")
            await self.session.rollback()
            raise

    # ==================== HELPER METHODS ====================

    async def _create_escalation_from_feedback(self, feedback: ProjectFeedback) -> None:
        """Create an escalation from blocking issue feedback.

        Args:
            feedback: ProjectFeedback of blocking issue type
        """
        try:
            from app.db.models import Escalation
            from app.db.models import Priority

            project = await self.session.get(Project, feedback.project_id)
            if not project:
                return

            escalation = Escalation(
                issue_type=feedback.feedback_type.value,
                severity=Priority.HIGH,
                escalated_by_agent_id=project.owner_agent_id,
                escalated_to_agent_id=project.owner_agent_id,  # Escalate to same agent initially
                related_project_id=feedback.project_id,
                description=f"{feedback.title}: {feedback.description}",
                status="open",
            )

            self.session.add(escalation)
            await self.session.commit()

            logger.info(f"Created escalation from feedback {feedback.feedback_id}")

        except Exception as e:
            logger.error(f"Error creating escalation: {e}")

    async def _create_improvement_plan(self, feedback: TaskFeedback) -> None:
        """Create improvement plan for low-quality task.

        Args:
            feedback: TaskFeedback with quality issues
        """
        try:
            plan_content = f"""
Improvement Plan for Task Feedback: {feedback.title}

Quality Assessment:
- Output Quality: {feedback.output_quality}/5
- Correctness: {feedback.correctness}/5
- Completeness: {feedback.completeness}/5
- Implementation: {feedback.implementation_quality}/5

Feedback:
{feedback.description}

Suggested Improvements:
{chr(10).join(f"- {item}" for item in feedback.suggested_improvements)}

Action Items:
{chr(10).join(f"- {item}" for item in feedback.action_items)}
            """.strip()

            await self._create_context_update(
                entity_type="task",
                entity_id=feedback.task_id,
                title="Improvement Plan",
                content=plan_content,
                related_feedback_id=feedback.feedback_id,
                context_tags=["improvement_plan", "quality_issue"],
            )

        except Exception as e:
            logger.error(f"Error creating improvement plan: {e}")

    async def _notify_agent_of_feedback(
        self,
        agent_id: str,
        message_content: str,
        feedback_id: UUID,
    ) -> None:
        """Notify an agent of feedback.

        Args:
            agent_id: Agent to notify
            message_content: Message content
            feedback_id: Related feedback ID
        """
        try:
            # Use HR agent (or CEO if available) to send notification
            # instead of non-existent "system" agent
            from_agent = "hr_001"  # HR agent typically handles notifications

            # Verify the sending agent exists
            sender = await self.session.get(Agent, from_agent)
            if not sender:
                # Fall back to CEO if HR doesn't exist
                from_agent = "ceo_001"
                sender = await self.session.get(Agent, from_agent)

            if not sender:
                # No valid sender found, skip notification
                logger.warning(f"No valid agent found to send feedback notification to {agent_id}")
                return

            message = Message(
                from_agent_id=from_agent,
                to_agent_id=agent_id,
                content=f"{message_content}\n\nFeedback ID: {feedback_id}",
                message_type=MessageType.ALERT,
                priority=Priority.MEDIUM,
                meta_data={"feedback_id": str(feedback_id), "notification": True},
            )

            self.session.add(message)
            await self.session.commit()

            logger.info(f"Sent feedback notification to agent {agent_id}")

        except Exception as e:
            logger.error(f"Error notifying agent: {e}")
            # Don't raise - notification is non-critical
            await self.session.rollback()

    @staticmethod
    def _extract_insights(text: str) -> Dict[str, Any]:
        """Extract key insights from feedback text.

        Args:
            text: Feedback text

        Returns:
            Dictionary of extracted insights
        """
        # Simple keyword-based extraction
        # Could be enhanced with NLP/ML models
        keywords = {
            "blocking": ["blocked", "blocking", "stuck", "unable", "can't"],
            "quality": ["quality", "poorly", "bad", "good", "excellent"],
            "incomplete": ["incomplete", "missing", "incomplete", "unfinished"],
            "unclear": ["unclear", "confusing", "ambiguous", "not clear"],
        }

        insights = {}
        text_lower = text.lower()

        for insight, keys in keywords.items():
            if any(key in text_lower for key in keys):
                insights[insight] = True

        return insights

    @staticmethod
    def _infer_tags(feedback_type: FeedbackType) -> List[str]:
        """Infer context tags from feedback type.

        Args:
            feedback_type: Type of feedback

        Returns:
            List of tags
        """
        tag_map = {
            FeedbackType.DIRECTION: ["direction", "strategy"],
            FeedbackType.ENHANCEMENT: ["enhancement", "feature"],
            FeedbackType.IMPLEMENTATION: ["implementation", "technical"],
            FeedbackType.BLOCKING_ISSUE: ["blocking", "critical"],
            FeedbackType.BUG_REPORT: ["bug", "issue"],
            FeedbackType.QUALITY: ["quality", "improvement"],
        }

        return tag_map.get(feedback_type, [feedback_type.value])

    @staticmethod
    def _calculate_average_quality(*ratings: Optional[int]) -> Optional[float]:
        """Calculate average quality from ratings.

        Args:
            *ratings: Variable number of ratings

        Returns:
            Average rating or None
        """
        valid_ratings = [r for r in ratings if r is not None]
        if not valid_ratings:
            return None

        return sum(valid_ratings) / len(valid_ratings)

    async def get_project_feedback(self, project_id: UUID) -> List[ProjectFeedback]:
        """Get all feedback for a project.

        Args:
            project_id: Project ID

        Returns:
            List of ProjectFeedback instances
        """
        query = select(ProjectFeedback).where(
            ProjectFeedback.project_id == project_id
        ).order_by(ProjectFeedback.created_at.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_task_feedback(self, task_id: UUID) -> List[TaskFeedback]:
        """Get all feedback for a task.

        Args:
            task_id: Task ID

        Returns:
            List of TaskFeedback instances
        """
        query = select(TaskFeedback).where(
            TaskFeedback.task_id == task_id
        ).order_by(TaskFeedback.created_at.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_agent_feedback(self, agent_id: str) -> List[AgentFeedback]:
        """Get all feedback for an agent.

        Args:
            agent_id: Agent ID

        Returns:
            List of AgentFeedback instances
        """
        query = select(AgentFeedback).where(
            AgentFeedback.agent_id == agent_id
        ).order_by(AgentFeedback.created_at.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_context_updates(
        self,
        entity_type: str,
        entity_id: UUID,
    ) -> List[ContextUpdate]:
        """Get context updates for an entity.

        Args:
            entity_type: Type of entity
            entity_id: Entity ID

        Returns:
            List of ContextUpdate instances
        """
        query = select(ContextUpdate).where(
            (ContextUpdate.entity_type == entity_type) &
            (ContextUpdate.entity_id == entity_id)
        ).order_by(ContextUpdate.created_at.desc())

        result = await self.session.execute(query)
        return result.scalars().all()

    async def update_feedback_status(
        self,
        feedback_id: UUID,
        status: FeedbackStatus,
        implementation_notes: Optional[str] = None,
    ) -> bool:
        """Update status of feedback.

        Args:
            feedback_id: Feedback ID
            status: New status
            implementation_notes: Notes on implementation

        Returns:
            True if successful
        """
        try:
            # Try project feedback first
            project_feedback = await self.session.get(ProjectFeedback, feedback_id)
            if project_feedback:
                project_feedback.status = status
                if implementation_notes:
                    project_feedback.implementation_notes = implementation_notes
                await self.session.commit()
                return True

            # Try task feedback
            task_feedback = await self.session.get(TaskFeedback, feedback_id)
            if task_feedback:
                task_feedback.status = status
                if implementation_notes:
                    task_feedback.implementation_plan = implementation_notes
                await self.session.commit()
                return True

            # Try agent feedback
            agent_feedback = await self.session.get(AgentFeedback, feedback_id)
            if agent_feedback:
                agent_feedback.status = status
                if implementation_notes:
                    agent_feedback.system_response = implementation_notes
                await self.session.commit()
                return True

            return False

        except Exception as e:
            logger.error(f"Error updating feedback status: {e}")
            await self.session.rollback()
            return False
