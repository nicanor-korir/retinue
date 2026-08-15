"""
Event emission mixin for agents to broadcast real-time activity.

This mixin provides helper methods that agents can use to emit events
for the Glass Box AI visualization feature.
"""
import time
import uuid
from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.event_service import EventService
from app.services.websocket_manager import broadcast_activity
from app.db.event_models import (
    ActivityType,
    ThoughtType,
    LLMProvider,
    HandoffStatus,
)

import logging

logger = logging.getLogger(__name__)


class AgentEventMixin:
    """
    Mixin to add real-time event emission capabilities to agents.
    
    Usage:
        class MyAgent(BaseAgent, AgentEventMixin):
            async def start_task(self, session, task):
                activity = await self.emit_activity_start(
                    session,
                    activity_type=ActivityType.THINKING,
                    title="Analyzing requirements",
                    project_id=task.project_id,
                    task_id=task.task_id
                )
                # ... do work ...
                await self.emit_activity_complete(session, activity.activity_id)
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._current_activity_id: Optional[uuid.UUID] = None
        self._llm_interaction_start: Optional[float] = None
    
    async def emit_activity_start(
        self,
        session: AsyncSession,
        activity_type: ActivityType,
        title: str,
        description: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
        task_id: Optional[uuid.UUID] = None,
    ) -> Any:
        """
        Start a new activity and broadcast it.
        
        Returns the created activity object.
        """
        try:
            event_service = EventService(session)
            
            activity = await event_service.create_activity(
                agent_id=self.agent_id,
                activity_type=activity_type,
                title=title,
                description=description or f"{self.name} is {activity_type.value}",
                project_id=project_id,
                task_id=task_id,
            )
            
            # Store current activity ID
            self._current_activity_id = activity.activity_id
            
            # Broadcast to WebSocket subscribers
            if project_id:
                await broadcast_activity(
                    project_id=str(project_id),
                    agent_id=self.agent_id,
                    event_type="activity_created",
                    data={
                        "activity_id": str(activity.activity_id),
                        "agent_id": self.agent_id,
                        "activity_type": activity_type.value,
                        "title": title,
                        "description": description,
                        "is_active": True,
                        "progress_percentage": 0,
                        "created_at": activity.created_at.isoformat(),
                    }
                )
            
            logger.debug(f"{self.name}: Started activity - {title}")
            return activity
            
        except Exception as e:
            logger.error(f"{self.name}: Failed to emit activity start: {e}")
            # Don't fail the agent if event emission fails
            return None
    
    async def emit_activity_progress(
        self,
        session: AsyncSession,
        activity_id: uuid.UUID,
        progress: int,
        stage: Optional[str] = None,
        project_id: Optional[uuid.UUID] = None,
    ):
        """Update activity progress and broadcast."""
        try:
            event_service = EventService(session)
            
            activity = await event_service.update_activity_progress(
                activity_id=activity_id,
                progress=progress,
                stage=stage,
            )
            
            # Broadcast update
            if project_id and activity:
                await broadcast_activity(
                    project_id=str(project_id),
                    agent_id=self.agent_id,
                    event_type="activity_updated",
                    data={
                        "activity_id": str(activity_id),
                        "progress_percentage": progress,
                        "stage": stage,
                    }
                )
            
            logger.debug(f"{self.name}: Updated activity progress to {progress}%")
            
        except Exception as e:
            logger.error(f"{self.name}: Failed to emit activity progress: {e}")
    
    async def emit_activity_complete(
        self,
        session: AsyncSession,
        activity_id: uuid.UUID,
        project_id: Optional[uuid.UUID] = None,
    ):
        """Mark activity as complete and broadcast."""
        try:
            event_service = EventService(session)
            
            activity = await event_service.complete_activity(activity_id)
            
            # Broadcast completion
            if project_id and activity:
                await broadcast_activity(
                    project_id=str(project_id),
                    agent_id=self.agent_id,
                    event_type="activity_completed",
                    data={
                        "activity_id": str(activity_id),
                        "is_active": False,
                        "completed_at": activity.completed_at.isoformat() if activity.completed_at else None,
                    }
                )
            
            # Clear current activity
            if self._current_activity_id == activity_id:
                self._current_activity_id = None
            
            logger.debug(f"{self.name}: Completed activity {activity_id}")
            
        except Exception as e:
            logger.error(f"{self.name}: Failed to emit activity complete: {e}")
    
    async def emit_thought(
        self,
        session: AsyncSession,
        thought_type: ThoughtType,
        content: str,
        project_id: Optional[uuid.UUID] = None,
        task_id: Optional[uuid.UUID] = None,
        context: Optional[Dict] = None,
    ):
        """Record a thought and broadcast it."""
        try:
            event_service = EventService(session)
            
            thought = await event_service.record_thought(
                agent_id=self.agent_id,
                thought_type=thought_type,
                content=content,
                project_id=project_id,
                task_id=task_id,
                activity_id=self._current_activity_id,
                context=context,
            )
            
            # Broadcast thought
            if project_id:
                await broadcast_activity(
                    project_id=str(project_id),
                    agent_id=self.agent_id,
                    event_type="thought_recorded",
                    data={
                        "thought_id": str(thought.thought_id),
                        "agent_id": self.agent_id,
                        "thought_type": thought_type.value,
                        "content": content,
                        "activity_id": str(self._current_activity_id) if self._current_activity_id else None,
                        "created_at": thought.created_at.isoformat(),
                    }
                )
            
            logger.debug(f"{self.name}: Recorded thought - {content[:50]}...")
            
        except Exception as e:
            logger.error(f"{self.name}: Failed to emit thought: {e}")
    
    async def emit_llm_call_start(
        self,
        session: AsyncSession,
        prompt: str,
        model: str,
        project_id: Optional[uuid.UUID] = None,
        task_id: Optional[uuid.UUID] = None,
        system_prompt: Optional[str] = None,
    ) -> Optional[uuid.UUID]:
        """Record start of LLM interaction."""
        try:
            event_service = EventService(session)
            
            # Store start time for latency calculation
            self._llm_interaction_start = time.time()
            
            interaction = await event_service.start_llm_interaction(
                agent_id=self.agent_id,
                provider=LLMProvider.ANTHROPIC,  # Default, can be parameterized
                model=model,
                prompt=prompt,
                system_prompt=system_prompt,
                project_id=project_id,
                task_id=task_id,
                activity_id=self._current_activity_id,
            )
            
            logger.debug(f"{self.name}: Started LLM interaction with {model}")
            return interaction.interaction_id
            
        except Exception as e:
            logger.error(f"{self.name}: Failed to emit LLM call start: {e}")
            return None
    
    async def emit_llm_call_complete(
        self,
        session: AsyncSession,
        interaction_id: uuid.UUID,
        response: str,
        prompt_tokens: int,
        completion_tokens: int,
        project_id: Optional[uuid.UUID] = None,
    ):
        """Record completion of LLM interaction."""
        try:
            event_service = EventService(session)
            
            # Calculate latency
            latency_ms = None
            if self._llm_interaction_start:
                latency_ms = int((time.time() - self._llm_interaction_start) * 1000)
                self._llm_interaction_start = None
            
            interaction = await event_service.complete_llm_interaction(
                interaction_id=interaction_id,
                response=response,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                latency_ms=latency_ms,
            )
            
            # Broadcast LLM interaction
            if project_id and interaction:
                await broadcast_activity(
                    project_id=str(project_id),
                    agent_id=self.agent_id,
                    event_type="llm_interaction",
                    data={
                        "interaction_id": str(interaction_id),
                        "agent_id": self.agent_id,
                        "model": interaction.model,
                        "total_tokens": prompt_tokens + completion_tokens,
                        "latency_ms": latency_ms,
                        "status": "completed",
                        "activity_id": str(self._current_activity_id) if self._current_activity_id else None,
                    }
                )
            
            logger.debug(f"{self.name}: Completed LLM interaction ({latency_ms}ms)")
            
        except Exception as e:
            logger.error(f"{self.name}: Failed to emit LLM call complete: {e}")
    
    async def emit_handoff(
        self,
        session: AsyncSession,
        to_agent_id: str,
        message: str,
        project_id: uuid.UUID,
        task_id: Optional[uuid.UUID] = None,
        handoff_type: str = "task_assignment",
        attachments: Optional[List[Dict]] = None,
    ):
        """Record and broadcast agent handoff."""
        try:
            event_service = EventService(session)
            
            handoff = await event_service.create_handoff(
                from_agent_id=self.agent_id,
                to_agent_id=to_agent_id,
                project_id=project_id,
                task_id=task_id,
                handoff_type=handoff_type,
                message=message,
                attachments=attachments or [],
            )
            
            # Broadcast handoff
            await broadcast_activity(
                project_id=str(project_id),
                agent_id=self.agent_id,
                event_type="agent_handoff",
                data={
                    "handoff_id": str(handoff.handoff_id),
                    "from_agent_id": self.agent_id,
                    "to_agent_id": to_agent_id,
                    "handoff_type": handoff_type,
                    "message": message,
                    "status": HandoffStatus.INITIATED.value,
                    "initiated_at": handoff.initiated_at.isoformat(),
                }
            )
            
            logger.info(f"{self.name}: Handed off to {to_agent_id} - {message}")
            
        except Exception as e:
            logger.error(f"{self.name}: Failed to emit handoff: {e}")
    
    async def emit_timeline_event(
        self,
        session: AsyncSession,
        event_type: str,
        title: str,
        project_id: uuid.UUID,
        description: Optional[str] = None,
        is_highlight: bool = False,
        highlight_type: Optional[str] = None,
    ):
        """Add event to project timeline."""
        try:
            event_service = EventService(session)
            
            await event_service.add_timeline_event(
                project_id=project_id,
                agent_id=self.agent_id,
                event_type=event_type,
                title=title,
                description=description,
                is_highlight=is_highlight,
                highlight_type=highlight_type,
            )
            
            logger.debug(f"{self.name}: Added timeline event - {title}")
            
        except Exception as e:
            logger.error(f"{self.name}: Failed to emit timeline event: {e}")
    
    async def call_llm_with_tracking(
        self,
        session: AsyncSession,
        prompt: str,
        context: Optional[Dict] = None,
        max_tokens: int = 4000,
        project_id: Optional[uuid.UUID] = None,
        task_id: Optional[uuid.UUID] = None,
        stream: bool = True,  # Enable streaming by default for better UX
        use_rag: bool = True,  # Use RAG by default
    ) -> str:
        """
        Call LLM with automatic event tracking and optional streaming.

        When stream=True, the LLM response will be broadcast in real-time
        as it's being generated, allowing users to see the AI "thinking".
        When use_rag=True, enriches the prompt with relevant context from past work.
        """
        # Start LLM interaction tracking
        interaction_id = await self.emit_llm_call_start(
            session=session,
            prompt=prompt,
            model=self.llm_model,
            project_id=project_id,
            task_id=task_id,
            system_prompt=self.system_prompt,
        )

        try:
            # Call LLM with RAG and streaming support
            if use_rag:
                response = await self.call_llm_with_rag(
                    prompt=prompt,
                    context=context,
                    max_tokens=max_tokens,
                    stream=stream,
                    project_id=str(project_id) if project_id else None,
                    agent_specific_filter=True,
                )
            else:
                response = await self.call_llm(
                    prompt=prompt,
                    context=context,
                    max_tokens=max_tokens,
                    stream=stream,
                    project_id=str(project_id) if project_id and stream else None,
                )

            # Complete LLM interaction tracking
            if interaction_id:
                # Note: Token counts are rough estimates
                # In production, extract from API response metadata
                await self.emit_llm_call_complete(
                    session=session,
                    interaction_id=interaction_id,
                    response=response,
                    prompt_tokens=len(prompt) // 4,  # Rough estimate
                    completion_tokens=len(response) // 4,  # Rough estimate
                    project_id=project_id,
                )

            return response

        except Exception as e:
            logger.error(f"{self.name}: LLM call failed: {e}")
            # Mark interaction as failed if we tracked it
            if interaction_id:
                try:
                    event_service = EventService(session)
                    await event_service.fail_llm_interaction(
                        interaction_id=interaction_id,
                        error_message=str(e),
                    )
                except:
                    pass
            raise
