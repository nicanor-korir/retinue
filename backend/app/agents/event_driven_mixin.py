"""
Event-Driven Agent Mixin - Real-Time Agent Execution

This mixin adds event-driven execution capabilities to agents, replacing
the polling-based check cycle with instant event-driven responses.

Agents with this mixin respond to events within <100ms, enabling
real-time agent-to-agent collaboration without any waiting time.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.event_bus import get_event_bus, EventType, Event
from app.db.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class EventDrivenMixin:
    """
    Mixin that adds event-driven execution capabilities to agents.

    Usage:
        class MyAgent(BaseAgent, EventDrivenMixin):
            def __init__(self, ...):
                super().__init__(...)
                self.setup_event_listeners()

            async def on_task_assigned(self, event: Event):
                # Custom handler for task assignment
                await self.handle_task(event.data["task_id"])
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_bus = get_event_bus()
        self._event_listeners_registered = False
        self._event_handlers: Dict[EventType, Callable] = {}

    def setup_event_listeners(self):
        """
        Set up event listeners for this agent.

        This should be called after agent initialization to start
        listening for events.
        """
        if self._event_listeners_registered:
            logger.warning(f"{self.name}: Event listeners already registered")
            return

        # Subscribe to agent-specific events
        self.event_bus.subscribe_agent(
            agent_id=self.agent_id,
            callback=self._on_agent_event,
        )

        # Subscribe to task events
        self.event_bus.subscribe(
            event_type=EventType.TASK_ASSIGNED,
            callback=self._on_task_assigned_event,
        )

        self.event_bus.subscribe(
            event_type=EventType.TASK_DEPENDENCY_RESOLVED,
            callback=self._on_dependency_resolved_event,
        )

        # Subscribe to message events
        self.event_bus.subscribe(
            event_type=EventType.MESSAGE_RECEIVED,
            callback=self._on_message_received_event,
        )

        # Subscribe to approval events
        self.event_bus.subscribe(
            event_type=EventType.APPROVAL_REQUESTED,
            callback=self._on_approval_requested_event,
        )

        self.event_bus.subscribe(
            event_type=EventType.APPROVAL_GIVEN,
            callback=self._on_approval_given_event,
        )

        # Subscribe to escalation events
        self.event_bus.subscribe(
            event_type=EventType.ESCALATION_CREATED,
            callback=self._on_escalation_created_event,
        )

        self._event_listeners_registered = True
        logger.info(f"✅ {self.name}: Event listeners registered")

    def register_event_handler(
        self,
        event_type: EventType,
        handler: Callable[[Event], Any],
    ):
        """
        Register a custom event handler for specific event types.

        Args:
            event_type: The type of event to handle
            handler: Async function to call when event occurs
        """
        self._event_handlers[event_type] = handler
        self.event_bus.subscribe(event_type, handler)
        logger.debug(f"{self.name}: Registered custom handler for {event_type.value}")

    # ============================================================================
    # EVENT HANDLERS
    # ============================================================================

    async def _on_agent_event(self, event: Event):
        """Handle events targeted directly at this agent"""
        logger.info(
            f"📨 {self.name}: Received event {event.event_type.value} "
            f"from {event.source}"
        )

        # Check for custom handlers
        if event.event_type in self._event_handlers:
            await self._event_handlers[event.event_type](event)
            return

        # Default handling based on event type
        if event.event_type == EventType.MESSAGE_RECEIVED:
            await self._handle_message_event(event)
        elif event.event_type == EventType.APPROVAL_REQUESTED:
            await self._handle_approval_request_event(event)
        elif event.event_type == EventType.ESCALATION_CREATED:
            await self._handle_escalation_event(event)

    async def _on_task_assigned_event(self, event: Event):
        """Handle task assignment events"""
        # Only process if assigned to this agent
        if event.data.get("assigned_to") != self.agent_id:
            return

        if event.target and event.target != self.agent_id:
            return

        logger.info(
            f"🎯 {self.name}: New task assigned - {event.data.get('task_id')}"
        )

        # Start task immediately
        await self._start_task_from_event(event)

    async def _on_dependency_resolved_event(self, event: Event):
        """Handle task dependency resolution events"""
        completed_task_id = event.data.get("completed_task_id")
        project_id = event.data.get("project_id")

        logger.debug(
            f"{self.name}: Dependency resolved - task {completed_task_id} completed"
        )

        # Check if any of our blocked tasks can now proceed
        await self._check_unblocked_tasks(project_id)

    async def _on_message_received_event(self, event: Event):
        """Handle incoming message events"""
        # Only process if message is for this agent
        if event.data.get("to_agent_id") != self.agent_id:
            return

        logger.info(
            f"💬 {self.name}: Message from {event.data.get('from_agent_id')}"
        )

        await self._handle_message_event(event)

    async def _on_approval_requested_event(self, event: Event):
        """Handle approval request events"""
        # Only process if approval is for this agent
        if event.data.get("approver_id") != self.agent_id:
            return

        logger.info(
            f"✋ {self.name}: Approval requested by {event.data.get('requester_id')}"
        )

        await self._handle_approval_request_event(event)

    async def _on_approval_given_event(self, event: Event):
        """Handle approval given events"""
        # Only process if we requested this approval
        if event.data.get("requester_id") != self.agent_id:
            return

        logger.info(
            f"✅ {self.name}: Approval received from {event.data.get('approver_id')}"
        )

        # Continue with approved work
        await self._continue_after_approval(event)

    async def _on_escalation_created_event(self, event: Event):
        """Handle escalation events"""
        # Only process if escalation is for this agent
        if event.data.get("escalated_to") != self.agent_id:
            return

        logger.warning(
            f"⚠️ {self.name}: Escalation from {event.data.get('escalated_by')}"
        )

        await self._handle_escalation_event(event)

    # ============================================================================
    # EVENT PROCESSING METHODS
    # ============================================================================

    async def _start_task_from_event(self, event: Event):
        """Start a task immediately when assigned"""
        task_id = event.data.get("task_id")
        project_id = event.data.get("project_id")

        if not task_id:
            logger.error(f"{self.name}: Task event missing task_id")
            return

        async with AsyncSessionLocal() as session:
            try:
                # Get the task
                from app.db.models import Task
                from sqlalchemy import select

                result = await session.execute(
                    select(Task).where(Task.task_id == task_id)
                )
                task = result.scalar_one_or_none()

                if not task:
                    logger.error(f"{self.name}: Task {task_id} not found")
                    return

                # Check dependencies
                if task.dependencies:
                    # Check if all dependencies are completed
                    dependencies_met = await self._check_dependencies(
                        session, task.dependencies
                    )
                    if not dependencies_met:
                        logger.info(
                            f"{self.name}: Task {task_id} has unmet dependencies, waiting"
                        )
                        return

                # Start the task using the agent's existing start_task method
                await self.start_task(session, task)

            except Exception as e:
                logger.error(
                    f"{self.name}: Error starting task from event: {e}",
                    exc_info=True
                )
                await session.rollback()

    async def _check_dependencies(
        self,
        session: AsyncSession,
        dependencies: list
    ) -> bool:
        """Check if all task dependencies are met"""
        from app.db.models import Task, TaskStatus
        from sqlalchemy import select

        for dep_id in dependencies:
            result = await session.execute(
                select(Task).where(Task.task_id == dep_id)
            )
            dep_task = result.scalar_one_or_none()

            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False

        return True

    async def _check_unblocked_tasks(self, project_id: str):
        """Check for tasks that can now proceed after dependency resolution"""
        async with AsyncSessionLocal() as session:
            try:
                from app.db.models import Task, TaskStatus
                from sqlalchemy import select

                # Get blocked tasks for this project assigned to this agent
                result = await session.execute(
                    select(Task).where(
                        Task.project_id == project_id,
                        Task.assigned_to_agent_id == self.agent_id,
                        Task.status == TaskStatus.PENDING,
                    )
                )
                tasks = result.scalars().all()

                for task in tasks:
                    if task.dependencies:
                        # Check if all dependencies are now met
                        dependencies_met = await self._check_dependencies(
                            session, task.dependencies
                        )
                        if dependencies_met:
                            logger.info(
                                f"✅ {self.name}: Task {task.task_id} dependencies resolved, starting"
                            )
                            await self.start_task(session, task)
                            return  # Start one task at a time

            except Exception as e:
                logger.error(
                    f"{self.name}: Error checking unblocked tasks: {e}",
                    exc_info=True
                )

    async def _handle_message_event(self, event: Event):
        """Handle an incoming message"""
        message_id = event.data.get("message_id")

        async with AsyncSessionLocal() as session:
            try:
                from app.db.models import Message
                from sqlalchemy import select

                result = await session.execute(
                    select(Message).where(Message.message_id == message_id)
                )
                message = result.scalar_one_or_none()

                if not message:
                    logger.error(f"{self.name}: Message {message_id} not found")
                    return

                # Process the message using existing logic
                await self.process_messages(session, [message])

            except Exception as e:
                logger.error(
                    f"{self.name}: Error handling message: {e}",
                    exc_info=True
                )

    async def _handle_approval_request_event(self, event: Event):
        """Handle an approval request"""
        approval_id = event.data.get("approval_id")

        async with AsyncSessionLocal() as session:
            try:
                from app.db.models import Approval
                from sqlalchemy import select

                result = await session.execute(
                    select(Approval).where(Approval.id == approval_id)
                )
                approval = result.scalar_one_or_none()

                if not approval:
                    logger.error(f"{self.name}: Approval {approval_id} not found")
                    return

                # Process approval using existing logic
                # (agents should override this method if they handle approvals)
                if hasattr(self, "process_approval_request"):
                    await self.process_approval_request(session, approval)

            except Exception as e:
                logger.error(
                    f"{self.name}: Error handling approval request: {e}",
                    exc_info=True
                )

    async def _continue_after_approval(self, event: Event):
        """Continue work after receiving approval"""
        approval_id = event.data.get("approval_id")
        task_id = event.data.get("task_id")

        async with AsyncSessionLocal() as session:
            try:
                # Get the approved item and continue work
                approved_items = await self.get_approved_items(session)
                if approved_items:
                    await self.continue_approved_work(session, approved_items[0])

            except Exception as e:
                logger.error(
                    f"{self.name}: Error continuing after approval: {e}",
                    exc_info=True
                )

    async def _handle_escalation_event(self, event: Event):
        """Handle an escalation"""
        escalation_id = event.data.get("escalation_id")

        async with AsyncSessionLocal() as session:
            try:
                from app.db.models import Escalation
                from sqlalchemy import select

                result = await session.execute(
                    select(Escalation).where(Escalation.escalation_id == escalation_id)
                )
                escalation = result.scalar_one_or_none()

                if not escalation:
                    logger.error(f"{self.name}: Escalation {escalation_id} not found")
                    return

                # Process escalation using existing logic
                # (agents should override this method if they handle escalations)
                if hasattr(self, "process_escalation"):
                    await self.process_escalation(session, escalation)

            except Exception as e:
                logger.error(
                    f"{self.name}: Error handling escalation: {e}",
                    exc_info=True
                )

    # ============================================================================
    # HELPER METHODS
    # ============================================================================

    async def emit_agent_event(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        target: Optional[str] = None,
        project_id: Optional[str] = None,
        priority: int = 5,
    ) -> str:
        """
        Emit an event from this agent.

        Args:
            event_type: Type of event to emit
            data: Event data payload
            target: Target agent ID (None = broadcast)
            project_id: Related project ID
            priority: Event priority (1=highest, 10=lowest)

        Returns:
            Event ID
        """
        return await self.event_bus.publish(
            event_type=event_type,
            data=data,
            source=self.agent_id,
            target=target,
            project_id=project_id,
            priority=priority,
        )

    async def start_event_driven_mode(self):
        """
        Start the agent in event-driven mode.

        This replaces the polling-based check cycle with event-driven execution.
        The agent will respond instantly to events instead of checking every 15 minutes.
        """
        logger.info(f"🚀 {self.name}: Starting in event-driven mode")

        # Set up event listeners
        self.setup_event_listeners()

        # Emit agent started event
        await self.emit_agent_event(
            event_type=EventType.AGENT_STARTED,
            data={
                "agent_id": self.agent_id,
                "name": self.name,
                "role": self.role,
            },
        )

        # Don't block on starting pending tasks - let them be picked up by event listeners
        # This prevents blocking during application startup
        logger.info(f"✅ {self.name}: Event-driven mode active, listening for events")

    async def run_hybrid_mode(self):
        """
        Run in hybrid mode: event-driven + periodic health checks.

        This mode uses event-driven execution for normal work but still performs
        periodic health checks every 30 minutes to catch any edge cases.
        """
        logger.info(f"🔄 {self.name}: Starting in hybrid mode")

        # Start event-driven mode
        await self.start_event_driven_mode()

        # Run periodic health checks
        while True:
            await asyncio.sleep(1800)  # 30 minutes

            async with AsyncSessionLocal() as session:
                try:
                    # Health check: Look for stuck work
                    await self.update_last_check(session)

                    # Check if blocked too long
                    if await self.is_blocked_too_long(session):
                        logger.warning(f"{self.name}: Health check - blocked too long")
                        await self.escalate_blockage(session)

                except Exception as e:
                    logger.error(
                        f"{self.name}: Error in health check: {e}",
                        exc_info=True
                    )
