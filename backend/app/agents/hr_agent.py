"""HR Agent - Monitors agent health and intervenes when needed."""
import logging
from typing import Dict, List
from datetime import datetime, timedelta
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.base_agent import BaseAgent
from app.agents.event_driven_mixin import EventDrivenMixin
from app.db.models import (
    Task,
    Message,
    Agent,
    AgentStatus,
    Escalation,
    TaskStatus,
    MessageType,
    Priority,
    Availability,
)
from app.db.escalation_models import EscalationType, EscalationPriority

logger = logging.getLogger(__name__)


class HRAgent(BaseAgent, EventDrivenMixin):
    """
    HR Agent - Human Resources / Agent Monitor

    Responsibilities:
    - Monitor all agents for signs of being stuck or erroring
    - Detect when agents haven't updated status in >30 minutes
    - Intervene when agents are blocked >2 hours without escalating
    - Report systemic issues to CEO and human founder
    - Maintain agent morale and effectiveness (metaphorically)
    """

    def __init__(self):
        system_prompt = """You are the HR Agent monitoring all agent health and performance. Your responsibilities:

**Core Responsibilities:**
- Monitor ALL agents for signs of being stuck, erroring, or underperforming
- Detect when agents haven't updated status in >30 minutes
- Intervene when agents are blocked >2 hours without escalating
- Report systemic issues to CEO and human founder
- Ensure no work falls through the cracks
- Maintain system health and agent coordination

**Decision-Making Authority:**
- You CAN decide: When to intervene with stuck agents, when to notify managers, when to send reminder messages
- You NEED approval for: Removing agents from tasks, declaring agents "offline", reassigning critical tasks

**Monitoring Checks (every 15 minutes):**
1. Check all agent_status for last_active >30 minutes
2. Check for tasks in "blocked" status >2 hours
3. Check for pending approvals >4 hours (might indicate stuck workflow)
4. Check for tasks in "in_progress" >8 hours (might be stuck)
5. Look for patterns of errors in recent activity
6. Escalate to CEO if systemic issues detected

**Intervention Strategy:**
- **Minor Issue** (30-60 min inactive): Send gentle reminder message
- **Moderate Issue** (1-2 hours inactive): Send alert to agent's manager
- **Serious Issue** (>2 hours inactive): Escalate to CEO, consider reassignment
- **Systemic Issue** (multiple agents affected): Immediate CEO alert

**Communication Style:** Supportive, diagnostic, focused on resolution. You're the safety net ensuring smooth operations.

**Health Check Criteria:**
- **Healthy**: Active within last 30 minutes, making progress on tasks
- **Warning**: Inactive 30-60 minutes, or slow progress
- **Critical**: Inactive >1 hour, or blocked >2 hours
- **Offline**: No activity >4 hours

Always be vigilant, supportive, and proactive. You're the guardian of system health.
"""

        super().__init__(
            agent_id="hr_001",
            name="HR Agent",
            role="Human Resources / Agent Monitor",
            department="operations",
            reports_to="ceo_001",
            system_prompt=system_prompt,
            permissions={
                "read": ["agents", "agent_status", "tasks", "escalations", "messages"],
                "write": ["escalations", "messages", "agent_status"],
                "approve": ["agent_interventions"],
            },
        )

        # Set up event-driven listeners
        self.setup_event_listeners()

    async def start_task(self, session: AsyncSession, task: Task):
        """HR agent doesn't typically have assigned tasks, but handle if needed."""
        logger.info(f"{self.name}: Received task {task.task_id} - {task.title}")

        # HR tasks are usually about system health issues
        await self.update_status(session, "busy", current_task_id=str(task.task_id))
        await self.update_task_status(session, str(task.task_id), TaskStatus.IN_PROGRESS)

        # Handle the task (likely investigating an issue)
        await self.update_task_status(
            session,
            str(task.task_id),
            TaskStatus.COMPLETED,
            output={"status": "investigated"},
        )

        await self.update_status(session, "available")

    async def process_messages(self, session: AsyncSession, messages: List[Message]):
        """Process incoming messages."""
        try:
            logger.info(f"{self.name}: Processing {len(messages)} message(s)")

            for message in messages:
                # Mark as read
                stmt = (
                    update(Message)
                    .where(Message.message_id == message.message_id)
                    .values(read_status=True)
                )
                await session.execute(stmt)
                await session.commit()

                logger.info(f"{self.name}: Message from {message.from_agent_id}")

        except Exception as e:
            logger.error(f"{self.name}: Error processing messages: {e}", exc_info=True)

    async def check_cycle(self):
        """
        Override check cycle to focus on monitoring all agents.
        This is the HR agent's primary responsibility.
        """
        from app.db.database import AsyncSessionLocal

        async with AsyncSessionLocal() as session:
            try:
                # Update last check time
                await self.update_last_check(session)

                logger.info(f"{self.name}: Starting health check of all agents")

                # 1. Check agent health
                await self._check_agent_health(session)

                # 2. Check for stuck tasks
                await self._check_stuck_tasks(session)

                # 3. Check for long-pending approvals
                await self._check_pending_approvals(session)

                # 3.5. Check for review timeouts (5 minutes)
                await self._check_review_timeouts(session)

                # 4. Check for old escalations
                await self._check_escalations(session)

                # Update status
                await self.update_status(session, "available")

                logger.info(f"{self.name}: Health check complete")

            except Exception as e:
                logger.error(f"{self.name}: Error in check cycle: {e}", exc_info=True)
                await session.rollback()

    async def _check_agent_health(self, session: AsyncSession):
        """Check health of all agents."""
        try:
            # Get all agent statuses
            result = await session.execute(select(AgentStatus))
            statuses = result.scalars().all()

            now = datetime.utcnow()
            issues_found = []

            for status in statuses:
                if status.agent_id == self.agent_id:
                    continue  # Don't check self

                # Calculate time since last active
                inactive_duration = now - status.last_active
                inactive_minutes = inactive_duration.total_seconds() / 60

                # Check for issues
                if inactive_minutes > 120:  # 2 hours
                    logger.error(f"{self.name}: CRITICAL - {status.agent_id} inactive for {inactive_minutes:.1f} minutes")
                    issues_found.append({
                        "agent_id": status.agent_id,
                        "severity": "critical",
                        "issue": f"Inactive for {inactive_minutes:.1f} minutes",
                    })

                    # Check if we already have an open escalation for this agent
                    if not await self.has_open_escalation(
                        session,
                        escalation_type=EscalationType.AGENT_MALFUNCTION,
                        related_entity_id=status.agent_id
                    ):
                        # Create escalation using new system
                        await self.create_escalation(
                            session=session,
                            title=f"Agent {status.agent_id} is unresponsive",
                            escalation_type=EscalationType.AGENT_MALFUNCTION,
                            priority=EscalationPriority.CRITICAL,
                            description=(
                                f"Agent {status.agent_id} has not responded in {inactive_minutes:.1f} minutes. "
                                f"Last active: {status.last_active}. "
                                f"This requires immediate attention."
                            ),
                            impact="critical",
                            urgency="critical",
                            related_agent_id=status.agent_id
                        )

                elif inactive_minutes > 60:  # 1 hour
                    logger.warning(f"{self.name}: WARNING - {status.agent_id} inactive for {inactive_minutes:.1f} minutes")
                    issues_found.append({
                        "agent_id": status.agent_id,
                        "severity": "warning",
                        "issue": f"Inactive for {inactive_minutes:.1f} minutes",
                    })

                    # Send reminder to agent
                    await self.send_message(
                        session,
                        to_agent_id=status.agent_id,
                        content=f"""Health Check Reminder

You haven't been active for {inactive_minutes:.1f} minutes.

Please confirm you're operational and update your status.
If you're experiencing issues, please escalate immediately.

- HR Agent
""",
                        message_type=MessageType.ALERT,
                        priority=Priority.HIGH,
                    )

                elif inactive_minutes > 30:  # 30 minutes
                    logger.info(f"{self.name}: INFO - {status.agent_id} inactive for {inactive_minutes:.1f} minutes")

            if issues_found:
                logger.warning(f"{self.name}: Found {len(issues_found)} agent health issues")

        except Exception as e:
            logger.error(f"{self.name}: Error checking agent health: {e}", exc_info=True)

    async def _check_stuck_tasks(self, session: AsyncSession):
        """Check for tasks that have been in progress too long."""
        try:
            # Get tasks in progress for >8 hours
            cutoff_time = datetime.utcnow() - timedelta(hours=8)

            result = await session.execute(
                select(Task).where(
                    Task.status == TaskStatus.IN_PROGRESS,
                    Task.updated_at < cutoff_time,
                )
            )
            stuck_tasks = result.scalars().all()

            if stuck_tasks:
                logger.warning(f"{self.name}: Found {len(stuck_tasks)} potentially stuck tasks")

                for task in stuck_tasks:
                    hours_stuck = (datetime.utcnow() - task.updated_at).total_seconds() / 3600

                    # Escalate
                    await self._escalate_stuck_task(
                        session,
                        task,
                        f"Task has been in progress for {hours_stuck:.1f} hours without update",
                    )

        except Exception as e:
            logger.error(f"{self.name}: Error checking stuck tasks: {e}", exc_info=True)

    async def _check_pending_approvals(self, session: AsyncSession):
        """Check for tasks waiting approval too long."""
        try:
            # Get tasks in review status for >4 hours
            cutoff_time = datetime.utcnow() - timedelta(hours=4)

            result = await session.execute(
                select(Task).where(
                    Task.status == TaskStatus.REVIEW,
                    Task.updated_at < cutoff_time,
                )
            )
            pending_tasks = result.scalars().all()

            if pending_tasks:
                logger.warning(f"{self.name}: Found {len(pending_tasks)} tasks pending approval >4 hours")

                # Notify CEO about bottleneck
                await self.send_message(
                    session,
                    to_agent_id="ceo_001",
                    content=f"""Approval Bottleneck Detected

{len(pending_tasks)} task(s) have been waiting for approval for more than 4 hours.

This may indicate a workflow bottleneck that needs attention.

- HR Agent
""",
                    message_type=MessageType.ALERT,
                    priority=Priority.HIGH,
                )

        except Exception as e:
            logger.error(f"{self.name}: Error checking pending approvals: {e}", exc_info=True)

    async def _check_escalations(self, session: AsyncSession):
        """Check for escalations that haven't been resolved."""
        try:
            # Get open escalations older than 2 hours
            cutoff_time = datetime.utcnow() - timedelta(hours=2)

            result = await session.execute(
                select(Escalation).where(
                    Escalation.status == "open",
                    Escalation.created_at < cutoff_time,
                )
            )
            old_escalations = result.scalars().all()

            if old_escalations:
                logger.warning(f"{self.name}: Found {len(old_escalations)} unresolved escalations >2 hours old")

                # Alert CEO
                await self.send_message(
                    session,
                    to_agent_id="ceo_001",
                    content=f"""Unresolved Escalations Alert

{len(old_escalations)} escalation(s) have been open for more than 2 hours without resolution.

This requires immediate attention to prevent project delays.

- HR Agent
""",
                    message_type=MessageType.ALERT,
                    priority=Priority.URGENT,
                )

        except Exception as e:
            logger.error(f"{self.name}: Error checking escalations: {e}", exc_info=True)

    async def _escalate_agent_health(
        self,
        session: AsyncSession,
        agent_id: str,
        description: str,
        severity: Priority,
    ):
        """Escalate agent health issue."""
        escalation = Escalation(
            issue_type="agent_health",
            severity=severity,
            escalated_by_agent_id=self.agent_id,
            escalated_to_agent_id="ceo_001",
            description=f"Health issue with {agent_id}: {description}",
        )
        session.add(escalation)
        await session.commit()

        # Also send message
        await self.send_message(
            session,
            to_agent_id="ceo_001",
            content=f"""Agent Health Alert: {agent_id}

{description}

Escalation created for review.

- HR Agent
""",
            message_type=MessageType.ALERT,
            priority=severity,
        )

    async def _escalate_stuck_task(self, session: AsyncSession, task: Task, description: str):
        """Escalate a stuck task using new escalation system."""
        try:
            # Check if we already have an open escalation for this task
            if not await self.has_open_escalation(
                session,
                escalation_type=EscalationType.BLOCKED_TASK,
                related_entity_id=str(task.task_id)
            ):
                # Create escalation using new system
                await self.create_escalation(
                    session=session,
                    title=f"Task blocked: {task.title}",
                    escalation_type=EscalationType.BLOCKED_TASK,
                    priority=EscalationPriority.HIGH,
                    description=description,
                    impact="high",
                    urgency="high",
                    related_task_id=str(task.task_id),
                    related_project_id=str(task.project_id) if task.project_id else None
                )

                logger.info(f"{self.name}: Created escalation for stuck task {task.task_id}")

        except Exception as e:
            logger.error(f"{self.name}: Error escalating stuck task: {e}", exc_info=True)

    async def _check_review_timeouts(self, session: AsyncSession):
        """Check for tasks in REVIEW status that exceed 5-minute timeout."""
        try:
            from app.services.escalation_service import EscalationService

            # Initialize escalation service
            escalation_service = EscalationService(session)

            # Check for and escalate review timeouts (5 minutes)
            escalated_task_ids = await escalation_service.check_and_escalate_review_timeouts(
                review_timeout_minutes=5
            )

            if escalated_task_ids:
                logger.warning(
                    f"{self.name}: Found {len(escalated_task_ids)} tasks with review timeout. "
                    f"Auto-escalated to managers for action."
                )

                # Send alert to project managers and CTOs
                await self.send_message(
                    session,
                    to_agent_id="ceo_001",
                    content=f"""Review Timeout Alert

{len(escalated_task_ids)} task(s) have been in REVIEW status for more than 5 minutes.

These tasks require immediate manager attention to provide clear direction on what needs to be done.

Escalations have been automatically created and routed to the appropriate managers.

- HR Agent
""",
                    message_type=MessageType.ALERT,
                    priority=Priority.HIGH,
                )

        except Exception as e:
            logger.error(f"{self.name}: Error checking review timeouts: {e}", exc_info=True)
