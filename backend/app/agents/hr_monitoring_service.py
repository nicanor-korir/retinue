"""
HR Continuous Monitoring Service - Real-Time Agent Health Monitoring

Replaces scheduled HR check cycles with continuous passive monitoring
that observes all agent activity in real-time and intervenes immediately
when issues are detected.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Set
from collections import defaultdict, deque

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.event_bus import get_event_bus, EventType, Event
from app.db.database import AsyncSessionLocal
from app.db.models import AgentStatus, Task, TaskStatus, Availability, Project, ProjectStatus

logger = logging.getLogger(__name__)


class AgentHealthMetrics:
    """Tracks health metrics for a single agent"""

    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.last_activity = datetime.utcnow()
        self.last_event_type: Optional[EventType] = None
        self.current_task_id: Optional[str] = None
        self.task_start_time: Optional[datetime] = None
        self.recent_events: deque = deque(maxlen=50)  # Last 50 events
        self.error_count = 0
        self.last_error_time: Optional[datetime] = None
        self.status: str = "healthy"  # healthy, warning, critical, offline

    def record_event(self, event: Event):
        """Record an event from this agent"""
        self.last_activity = datetime.utcnow()
        self.last_event_type = event.event_type
        self.recent_events.append({
            "event_type": event.event_type.value,
            "timestamp": event.timestamp,
            "data": event.data,
        })

        # Update task tracking
        if event.event_type == EventType.TASK_STARTED:
            self.current_task_id = event.data.get("task_id")
            self.task_start_time = datetime.utcnow()
        elif event.event_type == EventType.TASK_COMPLETED:
            self.current_task_id = None
            self.task_start_time = None

        # Track errors
        if event.event_type == EventType.AGENT_ERROR:
            self.error_count += 1
            self.last_error_time = datetime.utcnow()

    def get_inactive_duration(self) -> timedelta:
        """Get how long the agent has been inactive"""
        return datetime.utcnow() - self.last_activity

    def get_task_duration(self) -> Optional[timedelta]:
        """Get how long the agent has been working on current task"""
        if not self.task_start_time:
            return None
        return datetime.utcnow() - self.task_start_time

    def assess_health(self) -> str:
        """
        Assess agent health status

        Returns:
            "healthy", "warning", "critical", or "offline"
        """
        inactive_duration = self.get_inactive_duration()

        # Offline: No activity for 4+ hours
        if inactive_duration > timedelta(hours=4):
            self.status = "offline"
            return self.status

        # Critical: No activity for 1+ hour OR stuck on task for 8+ hours
        if inactive_duration > timedelta(hours=1):
            self.status = "critical"
            return self.status

        task_duration = self.get_task_duration()
        if task_duration and task_duration > timedelta(hours=8):
            self.status = "critical"
            return self.status

        # Warning: No activity for 30+ minutes OR many recent errors
        if inactive_duration > timedelta(minutes=30):
            self.status = "warning"
            return self.status

        if self.error_count > 5 and self.last_error_time:
            # Check if errors are recent (within last hour)
            if datetime.utcnow() - self.last_error_time < timedelta(hours=1):
                self.status = "warning"
                return self.status

        # Healthy
        self.status = "healthy"
        return self.status


class HRMonitoringService:
    """
    Continuous passive monitoring service for agent health.

    Instead of scheduled checks, this service:
    1. Subscribes to ALL agent events
    2. Builds real-time agent status dashboard
    3. Detects anomalies immediately
    4. Intervenes only when necessary
    """

    def __init__(self):
        self.event_bus = get_event_bus()
        self.agent_metrics: Dict[str, AgentHealthMetrics] = {}
        self.running = False
        self._monitor_task: Optional[asyncio.Task] = None

        # Intervention tracking to avoid spam
        self.last_intervention: Dict[str, datetime] = {}
        self.intervention_cooldown = timedelta(minutes=15)

        # Anomaly detection
        self.anomaly_detectors = [
            self._detect_stuck_agents,
            self._detect_error_patterns,
            self._detect_blocked_tasks,
            self._detect_inactive_agents,
        ]

    async def start(self):
        """Start the continuous monitoring service"""
        if self.running:
            logger.warning("HR Monitoring Service already running")
            return

        logger.info("🏥 Starting HR Continuous Monitoring Service")

        # Subscribe to all agent events
        self._subscribe_to_events()

        # Start background monitoring loop
        self.running = True
        self._monitor_task = asyncio.create_task(self._continuous_monitor())

        logger.info("✅ HR Monitoring Service active")

    async def stop(self):
        """Stop the monitoring service"""
        self.running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass

        logger.info("HR Monitoring Service stopped")

    def _subscribe_to_events(self):
        """Subscribe to all relevant events"""
        # Subscribe to all event types for monitoring
        for event_type in EventType:
            self.event_bus.subscribe(
                event_type=event_type,
                callback=self._on_any_event,
            )

        logger.info("HR Monitoring: Subscribed to all agent events")

    async def _on_any_event(self, event: Event):
        """Handle any event for monitoring purposes"""
        # Update agent metrics if event has a source
        if event.source:
            if event.source not in self.agent_metrics:
                self.agent_metrics[event.source] = AgentHealthMetrics(event.source)

            self.agent_metrics[event.source].record_event(event)

        # Log significant events
        if event.event_type in [
            EventType.AGENT_ERROR,
            EventType.AGENT_BLOCKED,
            EventType.ESCALATION_CREATED,
        ]:
            logger.warning(
                f"⚠️ HR Monitor: {event.event_type.value} from {event.source}"
            )

    async def _continuous_monitor(self):
        """Continuous monitoring loop"""
        while self.running:
            try:
                # Run all anomaly detectors
                for detector in self.anomaly_detectors:
                    await detector()

                # Update agent health assessments
                await self._update_health_assessments()

                # Wait 30 seconds before next check
                # (This is NOT polling agents - we're just analyzing the data
                # we've already collected from events)
                await asyncio.sleep(30)

            except Exception as e:
                logger.error(f"Error in HR monitoring loop: {e}", exc_info=True)
                await asyncio.sleep(60)

    async def _update_health_assessments(self):
        """Update health status for all agents"""
        for agent_id, metrics in self.agent_metrics.items():
            old_status = metrics.status
            new_status = metrics.assess_health()

            # Log status changes
            if old_status != new_status:
                logger.info(
                    f"📊 HR Monitor: {agent_id} status changed: "
                    f"{old_status} → {new_status}"
                )

                # Publish health status event
                await self.event_bus.publish(
                    event_type=EventType.HEALTH_CHECK_FAILED
                    if new_status in ["critical", "offline"]
                    else EventType.AGENT_IDLE,
                    data={
                        "agent_id": agent_id,
                        "old_status": old_status,
                        "new_status": new_status,
                        "inactive_duration_seconds": metrics.get_inactive_duration().total_seconds(),
                    },
                    source="hr_001",
                )

    async def _detect_stuck_agents(self):
        """Detect agents stuck on tasks for too long"""
        for agent_id, metrics in self.agent_metrics.items():
            task_duration = metrics.get_task_duration()

            if task_duration and task_duration > timedelta(hours=2):
                # Agent has been on same task for 2+ hours
                if self._can_intervene(agent_id):
                    logger.warning(
                        f"🚨 HR Monitor: {agent_id} stuck on task for "
                        f"{task_duration.total_seconds() / 3600:.1f} hours"
                    )

                    await self._send_check_in_message(
                        agent_id,
                        f"You've been working on the same task for "
                        f"{task_duration.total_seconds() / 3600:.1f} hours. "
                        f"Do you need assistance?",
                    )

    async def _detect_error_patterns(self):
        """Detect agents with repeated errors"""
        for agent_id, metrics in self.agent_metrics.items():
            # Check for multiple errors in recent events
            recent_errors = [
                e for e in metrics.recent_events
                if e["event_type"] == EventType.AGENT_ERROR.value
            ]

            if len(recent_errors) >= 3:
                # 3+ errors in recent history
                if self._can_intervene(agent_id):
                    logger.warning(
                        f"🚨 HR Monitor: {agent_id} has {len(recent_errors)} "
                        f"recent errors"
                    )

                    await self._send_check_in_message(
                        agent_id,
                        f"I've noticed {len(recent_errors)} errors in your recent "
                        f"activity. Do you need technical assistance?",
                    )

    async def _detect_blocked_tasks(self):
        """Detect tasks blocked for too long"""
        async with AsyncSessionLocal() as session:
            try:
                # Find tasks blocked for 2+ hours
                two_hours_ago = datetime.utcnow() - timedelta(hours=2)

                result = await session.execute(
                    select(Task).where(
                        Task.status == TaskStatus.BLOCKED,
                        Task.updated_at < two_hours_ago,
                    )
                )
                blocked_tasks = result.scalars().all()

                for task in blocked_tasks:
                    if task.assigned_to_agent_id and self._can_intervene(task.assigned_to_agent_id):
                        logger.warning(
                            f"🚨 HR Monitor: Task {task.task_id} blocked for 2+ hours "
                            f"(assigned to {task.assigned_to_agent_id})"
                        )

                        await self._send_check_in_message(
                            task.assigned_to_agent_id,
                            f"Task '{task.title}' has been blocked for over 2 hours. "
                            f"Should we escalate this?",
                        )

            except Exception as e:
                logger.error(f"Error detecting blocked tasks: {e}", exc_info=True)

    async def _detect_inactive_agents(self):
        """Detect agents that have gone inactive unexpectedly"""
        for agent_id, metrics in self.agent_metrics.items():
            inactive_duration = metrics.get_inactive_duration()

            # Warning threshold: 30 minutes
            if (
                inactive_duration > timedelta(minutes=30)
                and inactive_duration < timedelta(hours=1)
                and metrics.status == "warning"
            ):
                if self._can_intervene(agent_id):
                    logger.info(
                        f"⚠️ HR Monitor: {agent_id} inactive for "
                        f"{inactive_duration.total_seconds() / 60:.0f} minutes"
                    )

                    await self._send_check_in_message(
                        agent_id,
                        f"You've been inactive for "
                        f"{inactive_duration.total_seconds() / 60:.0f} minutes. "
                        f"Is everything okay?",
                    )

            # Critical threshold: 1+ hour
            elif inactive_duration > timedelta(hours=1):
                if self._can_intervene(agent_id):
                    logger.error(
                        f"🚨 HR Monitor: {agent_id} inactive for "
                        f"{inactive_duration.total_seconds() / 3600:.1f} hours"
                    )

                    # Escalate to CEO
                    await self._escalate_to_ceo(
                        agent_id,
                        f"Agent {agent_id} has been inactive for "
                        f"{inactive_duration.total_seconds() / 3600:.1f} hours. "
                        f"May need investigation.",
                    )

    def _can_intervene(self, agent_id: str) -> bool:
        """Check if we can intervene (not in cooldown period)"""
        if agent_id not in self.last_intervention:
            self.last_intervention[agent_id] = datetime.utcnow()
            return True

        time_since_last = datetime.utcnow() - self.last_intervention[agent_id]
        if time_since_last > self.intervention_cooldown:
            self.last_intervention[agent_id] = datetime.utcnow()
            return True

        return False

    async def _has_active_work(self) -> bool:
        """
        Check if there are any projects or tasks in review or in-progress status.

        Returns True if there are active projects/tasks, False otherwise.
        """
        async with AsyncSessionLocal() as session:
            try:
                # Check for projects in review or in-progress
                project_result = await session.execute(
                    select(Project).where(
                        or_(
                            Project.status == ProjectStatus.IN_PROGRESS,
                            Project.status == ProjectStatus.REVIEW,
                        )
                    ).limit(1)
                )
                active_project = project_result.scalar_one_or_none()

                if active_project:
                    return True

                # Check for tasks in review or in-progress
                task_result = await session.execute(
                    select(Task).where(
                        or_(
                            Task.status == TaskStatus.IN_PROGRESS,
                            Task.status == TaskStatus.REVIEW,
                        )
                    ).limit(1)
                )
                active_task = task_result.scalar_one_or_none()

                if active_task:
                    return True

                return False

            except Exception as e:
                logger.error(f"Error checking active work: {e}", exc_info=True)
                # On error, assume there might be active work (fail-safe)
                return True

    async def _send_check_in_message(self, agent_id: str, message: str):
        """Send a check-in message to an agent"""
        # Only send messages if there are active projects/tasks
        if not await self._has_active_work():
            logger.info(
                f"⏭️ HR Monitor: Skipping check-in to {agent_id} - "
                f"no active projects/tasks in review or in-progress"
            )
            return

        async with AsyncSessionLocal() as session:
            try:
                from app.db.models import Message, MessageType, Priority

                new_message = Message(
                    from_agent_id="hr_001",
                    to_agent_id=agent_id,
                    content=message,
                    message_type=MessageType.ALERT,
                    priority=Priority.MEDIUM,
                )

                session.add(new_message)
                await session.commit()

                logger.info(f"💬 HR Monitor: Sent check-in to {agent_id}")

            except Exception as e:
                logger.error(f"Error sending check-in message: {e}", exc_info=True)

    async def _escalate_to_ceo(self, agent_id: str, reason: str):
        """Escalate an issue to the CEO"""
        # Only escalate if there are active projects/tasks
        if not await self._has_active_work():
            logger.info(
                f"⏭️ HR Monitor: Skipping escalation for {agent_id} - "
                f"no active projects/tasks in review or in-progress"
            )
            return

        async with AsyncSessionLocal() as session:
            try:
                from app.db.models import Message, MessageType, Priority

                new_message = Message(
                    from_agent_id="hr_001",
                    to_agent_id="ceo_001",
                    content=f"ESCALATION: {reason}",
                    message_type=MessageType.ALERT,
                    priority=Priority.HIGH,
                )

                session.add(new_message)
                await session.commit()

                # Also publish escalation event
                await self.event_bus.publish(
                    event_type=EventType.ESCALATION_CREATED,
                    data={
                        "escalated_by": "hr_001",
                        "escalated_to": "ceo_001",
                        "reason": reason,
                        "related_agent": agent_id,
                    },
                    source="hr_001",
                    target="ceo_001",
                    priority=1,
                )

                logger.warning(f"🚨 HR Monitor: Escalated {agent_id} issue to CEO")

            except Exception as e:
                logger.error(f"Error escalating to CEO: {e}", exc_info=True)

    def get_dashboard_data(self) -> Dict:
        """
        Get real-time dashboard data for all agents

        Returns:
            Dictionary with agent health metrics for visualization
        """
        dashboard = {
            "timestamp": datetime.utcnow().isoformat(),
            "agents": {},
            "summary": {
                "total": len(self.agent_metrics),
                "healthy": 0,
                "warning": 0,
                "critical": 0,
                "offline": 0,
            },
        }

        for agent_id, metrics in self.agent_metrics.items():
            status = metrics.assess_health()
            dashboard["summary"][status] += 1

            dashboard["agents"][agent_id] = {
                "status": status,
                "last_activity": metrics.last_activity.isoformat(),
                "inactive_duration_seconds": metrics.get_inactive_duration().total_seconds(),
                "last_event_type": metrics.last_event_type.value
                if metrics.last_event_type
                else None,
                "current_task_id": metrics.current_task_id,
                "task_duration_seconds": metrics.get_task_duration().total_seconds()
                if metrics.get_task_duration()
                else None,
                "error_count": metrics.error_count,
                "recent_events_count": len(metrics.recent_events),
            }

        return dashboard


# Global instance
_hr_monitoring_service: Optional[HRMonitoringService] = None


def get_hr_monitoring_service() -> HRMonitoringService:
    """Get the global HR monitoring service"""
    global _hr_monitoring_service
    if _hr_monitoring_service is None:
        _hr_monitoring_service = HRMonitoringService()
    return _hr_monitoring_service


async def start_hr_monitoring():
    """Start the global HR monitoring service"""
    service = get_hr_monitoring_service()
    await service.start()
    logger.info("Global HR monitoring service started")


async def stop_hr_monitoring():
    """Stop the global HR monitoring service"""
    service = get_hr_monitoring_service()
    await service.stop()
    logger.info("Global HR monitoring service stopped")
