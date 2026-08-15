"""
Database Event Publisher - Automatic Event Emission on Database Changes

This module hooks into SQLAlchemy events to automatically publish events
to the event bus when database records are created, updated, or deleted.

This enables instant agent notification with zero polling delay.
"""

import logging
from typing import Any, Dict, Optional
from sqlalchemy import event
from sqlalchemy.orm import Session

from app.db.models import (
    Project,
    Task,
    AgentStatus,
    Message,
    Decision,
    Escalation,
    ProjectStatus as ProjectStatusEnum,
    TaskStatus,
    Availability,
)
from app.services.event_bus import get_event_bus, EventType

logger = logging.getLogger(__name__)


class DatabaseEventPublisher:
    """
    Publishes events to the event bus based on database changes

    This class hooks into SQLAlchemy's event system to detect when
    important records are created or updated, then immediately publishes
    corresponding events to the event bus for instant agent notification.
    """

    def __init__(self):
        self.event_bus = get_event_bus()
        self._registered = False

    def register_all_listeners(self):
        """Register all database event listeners"""
        if self._registered:
            logger.warning("Database event listeners already registered")
            return

        # Project events
        event.listen(Project, "after_insert", self._on_project_created)
        event.listen(Project, "after_update", self._on_project_updated)

        # Task events
        event.listen(Task, "after_insert", self._on_task_created)
        event.listen(Task, "after_update", self._on_task_updated)

        # Agent status events
        event.listen(AgentStatus, "after_update", self._on_agent_status_updated)

        # Message events
        event.listen(Message, "after_insert", self._on_message_created)

        # Decision events (for approval tracking)
        event.listen(Decision, "after_insert", self._on_decision_created)
        event.listen(Decision, "after_update", self._on_decision_updated)

        # Escalation events
        event.listen(Escalation, "after_insert", self._on_escalation_created)
        event.listen(Escalation, "after_update", self._on_escalation_updated)

        self._registered = True
        logger.info("Database event listeners registered successfully")

    # ============================================================================
    # PROJECT EVENTS
    # ============================================================================

    def _on_project_created(self, mapper, connection, target: Project):
        """Fires when a new project is created"""
        logger.info(f"Project created: {target.project_id} - Publishing event")

        # Schedule async event publication
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            logger.warning("No event loop available, skipping event publication")
            return

        loop.create_task(
            self.event_bus.publish(
                event_type=EventType.PROJECT_CREATED,
                data={
                    "project_id": target.project_id,
                    "name": target.name,
                    "description": target.description,
                    "owner_id": target.owner_agent_id,
                    "status": target.status.value if target.status else None,
                },
                project_id=target.project_id,
                priority=1,  # Highest priority
            )
        )

    def _on_project_updated(self, mapper, connection, target: Project):
        """Fires when a project is updated"""
        # Get the session to check what changed
        session = Session.object_session(target)
        if session is None:
            return

        # Check if status changed
        history = session.identity_map.get(target)
        if history and hasattr(history, "_sa_instance_state"):
            state = history._sa_instance_state
            if "status" in state.committed_state:
                old_status = state.committed_state["status"]
                new_status = target.status

                if old_status != new_status:
                    self._publish_project_status_change(target, old_status, new_status)

    def _publish_project_status_change(
        self,
        project: Project,
        old_status: ProjectStatusEnum,
        new_status: ProjectStatusEnum
    ):
        """Publish event when project status changes"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return

        event_type = None
        if new_status == ProjectStatusEnum.COMPLETED:
            event_type = EventType.PROJECT_COMPLETED
        elif new_status == ProjectStatusEnum.CANCELLED:
            event_type = EventType.PROJECT_CANCELLED

        if event_type:
            logger.info(f"Project status changed: {project.project_id} -> {new_status.value}")
            loop.create_task(
                self.event_bus.publish(
                    event_type=event_type,
                    data={
                        "project_id": project.project_id,
                        "old_status": old_status.value,
                        "new_status": new_status.value,
                    },
                    project_id=project.project_id,
                    priority=2,
                )
            )

    # ============================================================================
    # TASK EVENTS
    # ============================================================================

    def _on_task_created(self, mapper, connection, target: Task):
        """Fires when a new task is created"""
        logger.info(f"Task created: {target.task_id} - Publishing event")

        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return

        # Determine event type based on whether task is assigned
        event_type = EventType.TASK_ASSIGNED if target.assigned_to_agent_id else EventType.TASK_CREATED

        # Publish event
        loop.create_task(
            self.event_bus.publish(
                event_type=event_type,
                data={
                    "task_id": target.task_id,
                    "project_id": target.project_id,
                    "title": target.title,
                    "description": target.description,
                    "assigned_to": target.assigned_to_agent_id,
                    "status": target.status.value if target.status else None,
                    "dependencies": target.dependencies or [],
                },
                source="system",
                target=target.assigned_to_agent_id,  # Send directly to assigned agent
                project_id=target.project_id,
                priority=5,  # Default priority for task events
            )
        )

    def _on_task_updated(self, mapper, connection, target: Task):
        """Fires when a task is updated"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return

        # Detect status changes
        session = Session.object_session(target)
        if session is None:
            return

        # Check what changed
        state = session.identity_map.get(target)
        if state and hasattr(state, "_sa_instance_state"):
            inst_state = state._sa_instance_state
            committed = inst_state.committed_state

            # Status change
            if "status" in committed and committed["status"] != target.status:
                self._publish_task_status_change(
                    target,
                    committed["status"],
                    target.status
                )

            # Assignment change
            if "assigned_to_agent_id" in committed and committed["assigned_to_agent_id"] != target.assigned_to_agent_id:
                loop.create_task(
                    self.event_bus.publish(
                        event_type=EventType.TASK_ASSIGNED,
                        data={
                            "task_id": target.task_id,
                            "project_id": target.project_id,
                            "old_assignee": committed["assigned_to_agent_id"],
                            "new_assignee": target.assigned_to_agent_id,
                        },
                        target=target.assigned_to_agent_id,
                        project_id=target.project_id,
                        priority=2,
                    )
                )

    def _publish_task_status_change(
        self,
        task: Task,
        old_status: TaskStatus,
        new_status: TaskStatus
    ):
        """Publish event when task status changes"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return

        event_type_map = {
            TaskStatus.IN_PROGRESS: EventType.TASK_STARTED,
            TaskStatus.COMPLETED: EventType.TASK_COMPLETED,
            TaskStatus.BLOCKED: EventType.TASK_BLOCKED,
            TaskStatus.CANCELLED: EventType.TASK_CANCELLED,
        }

        event_type = event_type_map.get(new_status)
        if event_type:
            logger.info(f"Task status changed: {task.task_id} -> {new_status.value}")

            # Special handling for task completion - notify dependent tasks
            if new_status == TaskStatus.COMPLETED:
                # This will trigger dependency resolution
                loop.create_task(
                    self.event_bus.publish(
                        event_type=EventType.TASK_DEPENDENCY_RESOLVED,
                        data={
                            "completed_task_id": task.task_id,
                            "project_id": task.project_id,
                        },
                        project_id=task.project_id,
                        priority=1,  # High priority for unblocking
                    )
                )

            # Publish status change event
            loop.create_task(
                self.event_bus.publish(
                    event_type=event_type,
                    data={
                        "task_id": task.task_id,
                        "project_id": task.project_id,
                        "old_status": old_status.value,
                        "new_status": new_status.value,
                        "assigned_to": task.assigned_to_agent_id,
                    },
                    target=task.assigned_to_agent_id,
                    project_id=task.project_id,
                    priority=2,
                )
            )

    # ============================================================================
    # AGENT STATUS EVENTS
    # ============================================================================

    def _on_agent_status_updated(self, mapper, connection, target: AgentStatus):
        """Fires when agent status is updated"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return

        # Get what changed
        session = Session.object_session(target)
        if session is None:
            return

        state = session.identity_map.get(target)
        if state and hasattr(state, "_sa_instance_state"):
            inst_state = state._sa_instance_state
            committed = inst_state.committed_state

            # Availability change
            if "availability" in committed and committed["availability"] != target.availability:
                event_type_map = {
                    Availability.AVAILABLE: EventType.AGENT_IDLE,
                    Availability.BUSY: EventType.AGENT_BUSY,
                    Availability.BLOCKED: EventType.AGENT_BLOCKED,
                }

                event_type = event_type_map.get(target.availability)
                if event_type:
                    loop.create_task(
                        self.event_bus.publish(
                            event_type=event_type,
                            data={
                                "agent_id": target.agent_id,
                                "old_availability": committed["availability"].value,
                                "new_availability": target.availability.value,
                                "current_task_id": target.current_task_id,
                            },
                            source=target.agent_id,
                            priority=3,
                        )
                    )

    # ============================================================================
    # MESSAGE EVENTS
    # ============================================================================

    def _on_message_created(self, mapper, connection, target: Message):
        """Fires when a new message is created"""
        logger.info(f"Message created: {target.message_id} (to: {target.to_agent_id})")

        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return

        # Publish to receiving agent immediately
        loop.create_task(
            self.event_bus.publish(
                event_type=EventType.MESSAGE_RECEIVED,
                data={
                    "message_id": target.message_id,
                    "from_agent_id": target.from_agent_id,
                    "to_agent_id": target.to_agent_id,
                    "content": target.content,
                    "message_type": target.message_type.value if target.message_type else None,
                    "priority": target.priority.value if target.priority else None,
                    "related_task_id": target.related_task_id,
                },
                source=target.from_agent_id,
                target=target.to_agent_id,  # Direct to receiving agent
                priority=1 if target.priority and target.priority.value == "HIGH" else 3,
            )
        )

    # ============================================================================
    # DECISION EVENTS (Approval/Decision tracking)
    # ============================================================================

    def _on_decision_created(self, mapper, connection, target: Decision):
        """Fires when a decision is created (can be used for approval tracking)"""
        logger.info(f"Decision created: {target.decision_id} by {target.made_by_agent_id}")

        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return

        # If this decision requires approval, publish approval requested event
        if target.approved is None:  # Pending approval
            loop.create_task(
                self.event_bus.publish(
                    event_type=EventType.APPROVAL_REQUESTED,
                    data={
                        "decision_id": str(target.decision_id),
                        "project_id": str(target.project_id) if target.project_id else None,
                        "task_id": str(target.task_id) if target.task_id else None,
                        "made_by": target.made_by_agent_id,
                        "decision_type": target.decision_type,
                        "question": target.question,
                        "decision": target.decision,
                    },
                    source=target.made_by_agent_id,
                    project_id=str(target.project_id) if target.project_id else None,
                    priority=1,
                )
            )

    def _on_decision_updated(self, mapper, connection, target: Decision):
        """Fires when a decision is updated (approved/rejected)"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return

        # Check if approval status changed
        session = Session.object_session(target)
        if session is None:
            return

        state = session.identity_map.get(target)
        if state and hasattr(state, "_sa_instance_state"):
            inst_state = state._sa_instance_state
            committed = inst_state.committed_state

            if "approved" in committed and committed["approved"] != target.approved:
                if target.approved is True:
                    event_type = EventType.APPROVAL_GIVEN
                elif target.approved is False:
                    event_type = EventType.APPROVAL_REJECTED
                else:
                    return

                logger.info(f"Decision {target.decision_id} approval status: {target.approved}")

                loop.create_task(
                    self.event_bus.publish(
                        event_type=event_type,
                        data={
                            "decision_id": str(target.decision_id),
                            "project_id": str(target.project_id) if target.project_id else None,
                            "task_id": str(target.task_id) if target.task_id else None,
                            "made_by": target.made_by_agent_id,
                            "approved_by": target.approved_by,
                            "approved": target.approved,
                            "decision_type": target.decision_type,
                        },
                        source=target.approved_by if target.approved_by else "system",
                        target=target.made_by_agent_id,
                        project_id=str(target.project_id) if target.project_id else None,
                        priority=1,
                    )
                )

    # ============================================================================
    # ESCALATION EVENTS
    # ============================================================================

    def _on_escalation_created(self, mapper, connection, target: Escalation):
        """Fires when an escalation is created"""
        logger.warning(f"Escalation created: {target.escalation_id} (to: {target.escalated_to_agent_id})")

        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return

        loop.create_task(
            self.event_bus.publish(
                event_type=EventType.ESCALATION_CREATED,
                data={
                    "escalation_id": target.escalation_id,
                    "project_id": target.related_project_id,
                    "task_id": target.related_task_id,
                    "escalated_by": target.escalated_by_agent_id,
                    "escalated_to": target.escalated_to_agent_id,
                    "reason": target.issue_type,
                    "details": target.description,
                },
                source=target.escalated_by_agent_id,
                target=target.escalated_to_agent_id,
                project_id=target.related_project_id,
                priority=1,  # Critical priority
            )
        )

    def _on_escalation_updated(self, mapper, connection, target: Escalation):
        """Fires when an escalation is updated (resolved)"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return

        # Check if resolved
        session = Session.object_session(target)
        if session is None:
            return

        state = session.identity_map.get(target)
        if state and hasattr(state, "_sa_instance_state"):
            inst_state = state._sa_instance_state
            committed = inst_state.committed_state

            if "status" in committed and target.status == "resolved":
                logger.info(f"Escalation {target.escalation_id} resolved")

                loop.create_task(
                    self.event_bus.publish(
                        event_type=EventType.ESCALATION_RESOLVED,
                        data={
                            "escalation_id": target.escalation_id,
                            "project_id": target.related_project_id,
                            "task_id": target.related_task_id,
                            "escalated_by": target.escalated_by_agent_id,
                            "resolution": target.resolution,
                        },
                        source=target.escalated_to_agent_id,
                        target=target.escalated_by_agent_id,
                        project_id=target.related_project_id,
                        priority=2,
                    )
                )


# Global instance
_db_event_publisher: Optional[DatabaseEventPublisher] = None


def get_db_event_publisher() -> DatabaseEventPublisher:
    """Get the global database event publisher"""
    global _db_event_publisher
    if _db_event_publisher is None:
        _db_event_publisher = DatabaseEventPublisher()
    return _db_event_publisher


def register_db_event_listeners():
    """Register all database event listeners"""
    publisher = get_db_event_publisher()
    publisher.register_all_listeners()
    logger.info("Database event listeners registered")
