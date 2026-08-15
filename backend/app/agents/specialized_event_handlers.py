"""
Specialized Event Handlers for CEO, CTO, and PM Agents

These handlers enable instant event-driven responses for the key
management agents that orchestrate project workflow.
"""

import logging
from typing import Optional

from app.services.event_bus import get_event_bus, EventType, Event
from app.db.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class CEOEventHandler:
    """
    Event-driven handler for CEO Agent.

    Responds instantly to:
    - New project creation
    - Budget approval requests
    - Critical escalations
    - Project status changes
    """

    def __init__(self, ceo_agent):
        self.agent = ceo_agent
        self.event_bus = get_event_bus()

    def setup_listeners(self):
        """Set up CEO-specific event listeners"""
        # Project creation - highest priority
        self.event_bus.subscribe(
            event_type=EventType.PROJECT_CREATED,
            callback=self._on_project_created,
        )

        # Escalations to CEO
        self.event_bus.subscribe(
            event_type=EventType.ESCALATION_CREATED,
            callback=self._on_escalation,
        )

        # Approval requests
        self.agent.register_event_handler(
            event_type=EventType.APPROVAL_REQUESTED,
            handler=self._on_approval_requested,
        )

        logger.info(f"✅ {self.agent.name}: CEO event handlers registered")

    async def _on_project_created(self, event: Event):
        """Handle new project creation - start evaluation immediately"""
        project_id = event.data.get("project_id")

        if not project_id:
            logger.error("Project created event missing project_id")
            return

        logger.info(
            f"🆕 {self.agent.name}: New project {project_id} created, "
            f"starting evaluation immediately"
        )

        # Start project evaluation immediately (no 15-minute wait!)
        async with AsyncSessionLocal() as session:
            try:
                from app.db.models import Project
                from sqlalchemy import select

                result = await session.execute(
                    select(Project).where(Project.project_id == project_id)
                )
                project = result.scalar_one_or_none()

                if not project:
                    logger.error(f"Project {project_id} not found")
                    return

                # Evaluate project using CEO's existing logic
                if hasattr(self.agent, "evaluate_project"):
                    await self.agent.evaluate_project(session, project)
                else:
                    logger.warning(
                        f"{self.agent.name}: evaluate_project method not found"
                    )

            except Exception as e:
                logger.error(
                    f"{self.agent.name}: Error evaluating project: {e}",
                    exc_info=True
                )

    async def _on_escalation(self, event: Event):
        """Handle escalations to CEO"""
        if event.data.get("escalated_to") != self.agent.agent_id:
            return

        escalation_id = event.data.get("escalation_id")
        escalated_by = event.data.get("escalated_by")
        reason = event.data.get("reason")

        logger.warning(
            f"🚨 {self.agent.name}: Escalation from {escalated_by} - {reason}"
        )

        # Handle escalation immediately
        async with AsyncSessionLocal() as session:
            try:
                if hasattr(self.agent, "handle_escalation"):
                    await self.agent.handle_escalation(session, escalation_id)

            except Exception as e:
                logger.error(
                    f"{self.agent.name}: Error handling escalation: {e}",
                    exc_info=True
                )

    async def _on_approval_requested(self, event: Event):
        """Handle approval requests"""
        if event.data.get("approver_id") != self.agent.agent_id:
            return

        approval_id = event.data.get("approval_id")
        requester = event.data.get("requester_id")
        request_type = event.data.get("request_type")

        logger.info(
            f"✋ {self.agent.name}: Approval request from {requester} "
            f"(type: {request_type})"
        )

        # Process approval immediately
        async with AsyncSessionLocal() as session:
            try:
                if hasattr(self.agent, "process_approval"):
                    await self.agent.process_approval(session, approval_id)

            except Exception as e:
                logger.error(
                    f"{self.agent.name}: Error processing approval: {e}",
                    exc_info=True
                )


class CTOEventHandler:
    """
    Event-driven handler for CTO Agent.

    Responds instantly to:
    - CEO project approvals
    - Technical escalations
    - Architecture decision requests
    """

    def __init__(self, cto_agent):
        self.agent = cto_agent
        self.event_bus = get_event_bus()

    def setup_listeners(self):
        """Set up CTO-specific event listeners"""
        # CEO approvals that need CTO review
        self.event_bus.subscribe(
            event_type=EventType.PROJECT_APPROVED,
            callback=self._on_project_approved,
        )

        # Technical escalations
        self.agent.register_event_handler(
            event_type=EventType.ESCALATION_CREATED,
            handler=self._on_technical_escalation,
        )

        logger.info(f"✅ {self.agent.name}: CTO event handlers registered")

    async def _on_project_approved(self, event: Event):
        """Handle CEO project approval - start technical evaluation immediately"""
        project_id = event.data.get("project_id")

        if not project_id:
            logger.error("Project approved event missing project_id")
            return

        logger.info(
            f"✅ {self.agent.name}: Project {project_id} approved by CEO, "
            f"starting technical evaluation immediately"
        )

        # Start technical evaluation immediately
        async with AsyncSessionLocal() as session:
            try:
                from app.db.models import Project
                from sqlalchemy import select

                result = await session.execute(
                    select(Project).where(Project.project_id == project_id)
                )
                project = result.scalar_one_or_none()

                if not project:
                    logger.error(f"Project {project_id} not found")
                    return

                # Perform technical evaluation
                if hasattr(self.agent, "evaluate_technical_requirements"):
                    await self.agent.evaluate_technical_requirements(
                        session, project
                    )
                else:
                    logger.warning(
                        f"{self.agent.name}: evaluate_technical_requirements "
                        f"method not found"
                    )

            except Exception as e:
                logger.error(
                    f"{self.agent.name}: Error evaluating project: {e}",
                    exc_info=True
                )

    async def _on_technical_escalation(self, event: Event):
        """Handle technical escalations"""
        if event.data.get("escalated_to") != self.agent.agent_id:
            return

        escalation_id = event.data.get("escalation_id")
        reason = event.data.get("reason")

        logger.warning(
            f"🔧 {self.agent.name}: Technical escalation - {reason}"
        )

        # Handle escalation immediately
        async with AsyncSessionLocal() as session:
            try:
                if hasattr(self.agent, "handle_technical_escalation"):
                    await self.agent.handle_technical_escalation(
                        session, escalation_id
                    )

            except Exception as e:
                logger.error(
                    f"{self.agent.name}: Error handling escalation: {e}",
                    exc_info=True
                )


class PMEventHandler:
    """
    Event-driven handler for PM (Project Manager) Agent.

    Responds instantly to:
    - CTO technical approval
    - Task status changes
    - Agent status updates
    - Project progress events
    """

    def __init__(self, pm_agent):
        self.agent = pm_agent
        self.event_bus = get_event_bus()

    def setup_listeners(self):
        """Set up PM-specific event listeners"""
        # CTO approval - create tasks immediately
        self.agent.register_event_handler(
            event_type=EventType.APPROVAL_GIVEN,
            handler=self._on_cto_approval,
        )

        # Task completions - check project progress
        self.event_bus.subscribe(
            event_type=EventType.TASK_COMPLETED,
            callback=self._on_task_completed,
        )

        # Task blocked - may need intervention
        self.event_bus.subscribe(
            event_type=EventType.TASK_BLOCKED,
            callback=self._on_task_blocked,
        )

        logger.info(f"✅ {self.agent.name}: PM event handlers registered")

    async def _on_cto_approval(self, event: Event):
        """Handle CTO approval - create tasks immediately"""
        # Check if this is a CTO approval for a project
        approval_id = event.data.get("approval_id")
        project_id = event.data.get("project_id")
        approver = event.data.get("approver_id")

        if approver != "cto_001":
            return

        if not project_id:
            return

        logger.info(
            f"✅ {self.agent.name}: CTO approved project {project_id}, "
            f"creating tasks immediately"
        )

        # Create tasks immediately (no 15-minute wait!)
        async with AsyncSessionLocal() as session:
            try:
                from app.db.models import Project
                from sqlalchemy import select

                result = await session.execute(
                    select(Project).where(Project.project_id == project_id)
                )
                project = result.scalar_one_or_none()

                if not project:
                    logger.error(f"Project {project_id} not found")
                    return

                # Break down project into tasks
                if hasattr(self.agent, "create_project_tasks"):
                    await self.agent.create_project_tasks(session, project)
                else:
                    logger.warning(
                        f"{self.agent.name}: create_project_tasks method not found"
                    )

            except Exception as e:
                logger.error(
                    f"{self.agent.name}: Error creating tasks: {e}",
                    exc_info=True
                )

    async def _on_task_completed(self, event: Event):
        """Handle task completion - check project progress"""
        task_id = event.data.get("task_id")
        project_id = event.data.get("project_id")

        logger.info(
            f"✅ {self.agent.name}: Task {task_id} completed, "
            f"checking project progress"
        )

        # Check if project is complete
        async with AsyncSessionLocal() as session:
            try:
                if hasattr(self.agent, "check_project_completion"):
                    await self.agent.check_project_completion(
                        session, project_id
                    )

            except Exception as e:
                logger.error(
                    f"{self.agent.name}: Error checking project completion: {e}",
                    exc_info=True
                )

    async def _on_task_blocked(self, event: Event):
        """Handle task blocked event"""
        task_id = event.data.get("task_id")
        assigned_to = event.data.get("assigned_to")

        logger.warning(
            f"⚠️ {self.agent.name}: Task {task_id} blocked "
            f"(assigned to {assigned_to})"
        )

        # May need to reassign or escalate
        # For now, just log - PM can decide on intervention


def setup_specialized_handlers(ceo_agent, cto_agent, pm_agent):
    """
    Set up all specialized event handlers for management agents.

    Args:
        ceo_agent: CEO agent instance
        cto_agent: CTO agent instance
        pm_agent: PM agent instance
    """
    # Set up CEO handlers
    ceo_handler = CEOEventHandler(ceo_agent)
    ceo_handler.setup_listeners()

    # Set up CTO handlers
    cto_handler = CTOEventHandler(cto_agent)
    cto_handler.setup_listeners()

    # Set up PM handlers
    pm_handler = PMEventHandler(pm_agent)
    pm_handler.setup_listeners()

    logger.info("✅ All specialized event handlers configured")

    return {
        "ceo": ceo_handler,
        "cto": cto_handler,
        "pm": pm_handler,
    }
