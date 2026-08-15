"""
Event Service for managing real-time agent activities and broadcasting updates.

This service handles:
- Creating and tracking agent activities
- Broadcasting events via WebSocket
- Managing event lifecycle
- Querying event history
"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
from sqlalchemy import select, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.event_models import (
    AgentActivity,
    AgentThought,
    LLMInteraction,
    AgentHandoff,
    ContentGeneration,
    DecisionPoint,
    EventTimeline,
    ActivityType,
    ThoughtType,
    LLMProvider,
    HandoffStatus,
)

logger = logging.getLogger(__name__)


class EventService:
    """Service for managing real-time agent events."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ============================================================================
    # ACTIVITY TRACKING
    # ============================================================================

    async def create_activity(
        self,
        agent_id: str,
        activity_type: ActivityType,
        title: str,
        description: Optional[str] = None,
        project_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
        stage: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> AgentActivity:
        """Create a new agent activity and broadcast it."""
        activity = AgentActivity(
            agent_id=agent_id,
            project_id=project_id,
            task_id=task_id,
            activity_type=activity_type,
            title=title,
            description=description,
            stage=stage,
            is_active=True,
            progress_percentage=0,
            metadata=metadata or {},
        )

        self.db.add(activity)
        await self.db.commit()
        await self.db.refresh(activity)

        logger.info(
            f"Created activity: {activity.activity_id} - {agent_id} - {title}"
        )

        return activity

    async def update_activity_progress(
        self,
        activity_id: UUID,
        progress: int,
        stage: Optional[str] = None,
        description: Optional[str] = None,
    ) -> AgentActivity:
        """Update activity progress."""
        result = await self.db.execute(
            select(AgentActivity).where(AgentActivity.activity_id == activity_id)
        )
        activity = result.scalar_one_or_none()

        if not activity:
            raise ValueError(f"Activity {activity_id} not found")

        activity.progress_percentage = progress
        if stage:
            activity.stage = stage
        if description:
            activity.description = description

        await self.db.commit()
        await self.db.refresh(activity)

        return activity

    async def complete_activity(
        self, activity_id: UUID, metadata: Optional[Dict[str, Any]] = None
    ) -> AgentActivity:
        """Mark activity as completed."""
        result = await self.db.execute(
            select(AgentActivity).where(AgentActivity.activity_id == activity_id)
        )
        activity = result.scalar_one_or_none()

        if not activity:
            raise ValueError(f"Activity {activity_id} not found")

        activity.is_active = False
        activity.completed_at = datetime.utcnow()
        activity.progress_percentage = 100

        if metadata:
            activity.metadata.update(metadata)

        await self.db.commit()
        await self.db.refresh(activity)

        logger.info(f"Completed activity: {activity_id}")

        return activity

    async def get_active_activities(
        self, project_id: Optional[UUID] = None, agent_id: Optional[str] = None
    ) -> List[AgentActivity]:
        """Get all active activities."""
        query = select(AgentActivity).where(AgentActivity.is_active == True)

        if project_id:
            query = query.where(AgentActivity.project_id == project_id)
        if agent_id:
            query = query.where(AgentActivity.agent_id == agent_id)

        query = query.order_by(desc(AgentActivity.created_at))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_project_activities(
        self,
        project_id: UUID,
        limit: int = 50,
        offset: int = 0,
        activity_type: Optional[ActivityType] = None,
    ) -> List[AgentActivity]:
        """Get activities for a project."""
        query = select(AgentActivity).where(AgentActivity.project_id == project_id)

        if activity_type:
            query = query.where(AgentActivity.activity_type == activity_type)

        query = query.order_by(desc(AgentActivity.created_at)).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return result.scalars().all()

    # ============================================================================
    # THOUGHT TRACKING
    # ============================================================================

    async def record_thought(
        self,
        agent_id: str,
        thought_type: ThoughtType,
        content: str,
        project_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
        activity_id: Optional[UUID] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> AgentThought:
        """Record an agent's thought."""
        thought = AgentThought(
            agent_id=agent_id,
            activity_id=activity_id,
            project_id=project_id,
            task_id=task_id,
            thought_type=thought_type,
            content=content,
            context=context or {},
        )

        self.db.add(thought)
        await self.db.commit()
        await self.db.refresh(thought)

        return thought

    async def get_agent_thoughts(
        self,
        agent_id: str,
        project_id: Optional[UUID] = None,
        limit: int = 20,
    ) -> List[AgentThought]:
        """Get recent thoughts from an agent."""
        query = select(AgentThought).where(AgentThought.agent_id == agent_id)

        if project_id:
            query = query.where(AgentThought.project_id == project_id)

        query = query.order_by(desc(AgentThought.created_at)).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    # ============================================================================
    # LLM INTERACTION TRACKING
    # ============================================================================

    async def start_llm_interaction(
        self,
        agent_id: str,
        provider: LLMProvider,
        model: str,
        prompt: str,
        system_prompt: Optional[str] = None,
        project_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
        activity_id: Optional[UUID] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMInteraction:
        """Start tracking an LLM interaction."""
        interaction = LLMInteraction(
            agent_id=agent_id,
            activity_id=activity_id,
            project_id=project_id,
            task_id=task_id,
            provider=provider,
            model=model,
            prompt=prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens,
            status="pending",
        )

        self.db.add(interaction)
        await self.db.commit()
        await self.db.refresh(interaction)

        return interaction

    async def complete_llm_interaction(
        self,
        interaction_id: UUID,
        response: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency_ms: int,
        finish_reason: Optional[str] = None,
        cost: Optional[float] = None,
    ) -> LLMInteraction:
        """Complete an LLM interaction with results."""
        result = await self.db.execute(
            select(LLMInteraction).where(
                LLMInteraction.interaction_id == interaction_id
            )
        )
        interaction = result.scalar_one_or_none()

        if not interaction:
            raise ValueError(f"LLM interaction {interaction_id} not found")

        interaction.response = response
        interaction.prompt_tokens = prompt_tokens
        interaction.completion_tokens = completion_tokens
        interaction.total_tokens = prompt_tokens + completion_tokens
        interaction.latency_ms = latency_ms
        interaction.finish_reason = finish_reason
        interaction.cost = cost
        interaction.status = "completed"
        interaction.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(interaction)

        return interaction

    async def fail_llm_interaction(
        self, interaction_id: UUID, error_message: str
    ) -> LLMInteraction:
        """Mark an LLM interaction as failed."""
        result = await self.db.execute(
            select(LLMInteraction).where(
                LLMInteraction.interaction_id == interaction_id
            )
        )
        interaction = result.scalar_one_or_none()

        if not interaction:
            raise ValueError(f"LLM interaction {interaction_id} not found")

        interaction.status = "error"
        interaction.error_message = error_message
        interaction.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(interaction)

        return interaction

    async def get_llm_interactions(
        self,
        project_id: Optional[UUID] = None,
        agent_id: Optional[str] = None,
        limit: int = 20,
    ) -> List[LLMInteraction]:
        """Get recent LLM interactions."""
        query = select(LLMInteraction)

        if project_id:
            query = query.where(LLMInteraction.project_id == project_id)
        if agent_id:
            query = query.where(LLMInteraction.agent_id == agent_id)

        query = query.order_by(desc(LLMInteraction.started_at)).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    # ============================================================================
    # HANDOFF TRACKING
    # ============================================================================

    async def create_handoff(
        self,
        from_agent_id: str,
        to_agent_id: str,
        project_id: UUID,
        handoff_type: str,
        message: str,
        task_id: Optional[UUID] = None,
        attachments: Optional[List[Dict[str, Any]]] = None,
    ) -> AgentHandoff:
        """Create a new agent handoff."""
        handoff = AgentHandoff(
            from_agent_id=from_agent_id,
            to_agent_id=to_agent_id,
            project_id=project_id,
            task_id=task_id,
            handoff_type=handoff_type,
            message=message,
            attachments=attachments or [],
            status=HandoffStatus.INITIATED,
        )

        self.db.add(handoff)
        await self.db.commit()
        await self.db.refresh(handoff)

        logger.info(
            f"Created handoff: {from_agent_id} -> {to_agent_id} for project {project_id}"
        )

        return handoff

    async def update_handoff_status(
        self,
        handoff_id: UUID,
        status: HandoffStatus,
        response: Optional[str] = None,
    ) -> AgentHandoff:
        """Update handoff status."""
        result = await self.db.execute(
            select(AgentHandoff).where(AgentHandoff.handoff_id == handoff_id)
        )
        handoff = result.scalar_one_or_none()

        if not handoff:
            raise ValueError(f"Handoff {handoff_id} not found")

        handoff.status = status

        if status == HandoffStatus.RECEIVED and not handoff.received_at:
            handoff.received_at = datetime.utcnow()
        elif status in [HandoffStatus.ACCEPTED, HandoffStatus.REJECTED]:
            handoff.completed_at = datetime.utcnow()

        if response:
            handoff.response = response

        await self.db.commit()
        await self.db.refresh(handoff)

        return handoff

    async def get_project_handoffs(
        self, project_id: UUID, limit: int = 50
    ) -> List[AgentHandoff]:
        """Get handoffs for a project."""
        result = await self.db.execute(
            select(AgentHandoff)
            .where(AgentHandoff.project_id == project_id)
            .order_by(desc(AgentHandoff.initiated_at))
            .limit(limit)
        )
        return result.scalars().all()

    # ============================================================================
    # DECISION TRACKING
    # ============================================================================

    async def create_decision_point(
        self,
        agent_id: str,
        title: str,
        question: str,
        project_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
        activity_id: Optional[UUID] = None,
        options: Optional[List[str]] = None,
        rationale: Optional[str] = None,
        requires_approval: bool = False,
        impact: Optional[str] = None,
        risk_level: Optional[str] = None,
    ) -> DecisionPoint:
        """Create a decision point."""
        decision_point = DecisionPoint(
            agent_id=agent_id,
            activity_id=activity_id,
            project_id=project_id,
            task_id=task_id,
            title=title,
            question=question,
            options=options or [],
            rationale=rationale,
            requires_approval=requires_approval,
            impact=impact,
            risk_level=risk_level,
            approval_status="pending" if requires_approval else "not_required",
        )

        self.db.add(decision_point)
        await self.db.commit()
        await self.db.refresh(decision_point)

        return decision_point

    async def resolve_decision_point(
        self,
        decision_point_id: UUID,
        chosen_option: str,
        approved_by: Optional[str] = None,
        approval_status: str = "approved",
    ) -> DecisionPoint:
        """Resolve a decision point."""
        result = await self.db.execute(
            select(DecisionPoint).where(
                DecisionPoint.decision_point_id == decision_point_id
            )
        )
        decision_point = result.scalar_one_or_none()

        if not decision_point:
            raise ValueError(f"Decision point {decision_point_id} not found")

        decision_point.chosen_option = chosen_option
        decision_point.decided_at = datetime.utcnow()
        decision_point.approval_status = approval_status

        if approved_by:
            decision_point.approved_by = approved_by

        await self.db.commit()
        await self.db.refresh(decision_point)

        return decision_point

    async def get_pending_decisions(
        self, project_id: Optional[UUID] = None
    ) -> List[DecisionPoint]:
        """Get pending decision points requiring approval."""
        query = select(DecisionPoint).where(
            and_(
                DecisionPoint.requires_approval == True,
                DecisionPoint.approval_status == "pending",
            )
        )

        if project_id:
            query = query.where(DecisionPoint.project_id == project_id)

        query = query.order_by(desc(DecisionPoint.created_at))

        result = await self.db.execute(query)
        return result.scalars().all()

    # ============================================================================
    # CONTENT GENERATION
    # ============================================================================

    async def start_content_generation(
        self,
        agent_id: str,
        content_type: str,
        title: str,
        project_id: Optional[UUID] = None,
        task_id: Optional[UUID] = None,
        activity_id: Optional[UUID] = None,
    ) -> ContentGeneration:
        """Start tracking content generation."""
        generation = ContentGeneration(
            agent_id=agent_id,
            activity_id=activity_id,
            project_id=project_id,
            task_id=task_id,
            content_type=content_type,
            title=title,
            is_complete=False,
        )

        self.db.add(generation)
        await self.db.commit()
        await self.db.refresh(generation)

        return generation

    async def append_content_chunk(
        self, generation_id: UUID, chunk: str
    ) -> ContentGeneration:
        """Append a chunk of generated content (for streaming)."""
        result = await self.db.execute(
            select(ContentGeneration).where(
                ContentGeneration.generation_id == generation_id
            )
        )
        generation = result.scalar_one_or_none()

        if not generation:
            raise ValueError(f"Content generation {generation_id} not found")

        # Append to content chunks for streaming visualization
        if generation.content_chunks is None:
            generation.content_chunks = []
        
        generation.content_chunks.append(
            {"chunk": chunk, "timestamp": datetime.utcnow().isoformat()}
        )

        # Update full content
        if generation.content is None:
            generation.content = chunk
        else:
            generation.content += chunk

        generation.tokens_generated = len(generation.content.split())

        await self.db.commit()
        await self.db.refresh(generation)

        return generation

    async def complete_content_generation(
        self, generation_id: UUID
    ) -> ContentGeneration:
        """Mark content generation as complete."""
        result = await self.db.execute(
            select(ContentGeneration).where(
                ContentGeneration.generation_id == generation_id
            )
        )
        generation = result.scalar_one_or_none()

        if not generation:
            raise ValueError(f"Content generation {generation_id} not found")

        generation.is_complete = True
        generation.completed_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(generation)

        return generation

    # ============================================================================
    # EVENT TIMELINE
    # ============================================================================

    async def add_timeline_event(
        self,
        project_id: UUID,
        event_type: str,
        title: str,
        description: Optional[str] = None,
        agent_id: Optional[str] = None,
        event_category: Optional[str] = None,
        is_highlight: bool = False,
        highlight_type: Optional[str] = None,
        related_activity_id: Optional[UUID] = None,
        related_task_id: Optional[UUID] = None,
    ) -> EventTimeline:
        """Add an event to the project timeline."""
        event = EventTimeline(
            project_id=project_id,
            agent_id=agent_id,
            event_type=event_type,
            event_category=event_category,
            title=title,
            description=description,
            related_activity_id=related_activity_id,
            related_task_id=related_task_id,
            is_highlight=is_highlight,
            highlight_type=highlight_type,
            event_timestamp=datetime.utcnow(),
        )

        self.db.add(event)
        await self.db.commit()
        await self.db.refresh(event)

        return event

    async def get_project_timeline(
        self,
        project_id: UUID,
        limit: int = 100,
        highlights_only: bool = False,
    ) -> List[EventTimeline]:
        """Get project timeline events."""
        query = select(EventTimeline).where(EventTimeline.project_id == project_id)

        if highlights_only:
            query = query.where(EventTimeline.is_highlight == True)

        query = query.order_by(desc(EventTimeline.event_timestamp)).limit(limit)

        result = await self.db.execute(query)
        return result.scalars().all()

    # ============================================================================
    # CONVENIENCE METHODS
    # ============================================================================

    async def get_project_stream(
        self, project_id: UUID, limit: int = 50
    ) -> Dict[str, Any]:
        """Get complete project stream including all event types."""
        activities = await self.get_project_activities(project_id, limit=limit)
        handoffs = await self.get_project_handoffs(project_id, limit=limit)
        timeline = await self.get_project_timeline(project_id, limit=limit)
        pending_decisions = await self.get_pending_decisions(project_id)

        return {
            "activities": activities,
            "handoffs": handoffs,
            "timeline": timeline,
            "pending_decisions": pending_decisions,
        }

    async def get_agent_stream(
        self, agent_id: str, project_id: Optional[UUID] = None, limit: int = 20
    ) -> Dict[str, Any]:
        """Get complete agent stream."""
        activities = await self.get_active_activities(
            project_id=project_id, agent_id=agent_id
        )
        thoughts = await self.get_agent_thoughts(
            agent_id=agent_id, project_id=project_id, limit=limit
        )
        llm_interactions = await self.get_llm_interactions(
            project_id=project_id, agent_id=agent_id, limit=limit
        )

        return {
            "activities": activities,
            "thoughts": thoughts,
            "llm_interactions": llm_interactions,
        }
