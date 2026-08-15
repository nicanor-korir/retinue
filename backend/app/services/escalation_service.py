"""
Core Escalation Management Service.

This service handles all business logic for creating, updating, resolving,
and managing escalations including auto-routing, SLA tracking, and notifications.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4

from sqlalchemy import select, and_, or_, func, desc, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.escalation_models import (
    AdvancedEscalation,
    EscalationTimelineEvent,
    EscalationComment,
    EscalationNotification,
    EscalationCollaboration,
    EscalationSLAConfig,
    EscalationTemplate,
    EscalationPlaybook,
    EscalationWatchlist,
    EscalationAnalytics,
    EscalationType,
    EscalationPriority,
    EscalationStatus,
    EscalationLevel,
    EscalationEventType,
    ResolutionType,
    ImpactLevel,
    UrgencyLevel,
)
from app.db.models import Agent, Task, Project, Priority

logger = logging.getLogger(__name__)


class EscalationService:
    """Service for managing escalations with comprehensive features."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== CORE ESCALATION OPERATIONS ====================

    async def create_escalation(
        self,
        title: str,
        description: str,
        escalation_type: EscalationType,
        priority: EscalationPriority,
        impact: ImpactLevel,
        urgency: UrgencyLevel,
        created_by_type: str,
        created_by_id: str,
        related_task_id: Optional[UUID] = None,
        related_project_id: Optional[UUID] = None,
        related_agent_id: Optional[str] = None,
        conflict_parties: Optional[List[Dict]] = None,
        department: Optional[str] = None,
        tags: Optional[List[str]] = None,
        due_date: Optional[datetime] = None,
    ) -> AdvancedEscalation:
        """
        Create a new escalation with automatic routing and SLA calculation.
        """
        # Generate escalation number
        escalation_number = await self._generate_escalation_number()

        # Get SLA configuration
        sla_config = await self._get_sla_config(escalation_type, priority)
        sla_deadline = datetime.utcnow() + timedelta(minutes=sla_config.time_to_resolution)

        # Auto-assign based on escalation matrix
        assigned_to_type, assigned_to_id, level = await self._auto_route_escalation(
            escalation_type, priority, department
        )

        # Create escalation
        escalation = AdvancedEscalation(
            id=uuid4(),
            escalation_number=escalation_number,
            title=title,
            description=description,
            escalation_type=escalation_type,
            priority=priority,
            status=EscalationStatus.OPEN,
            level=level,
            created_by_type=created_by_type,
            created_by_id=created_by_id,
            assigned_to_type=assigned_to_type,
            assigned_to_id=assigned_to_id,
            assigned_at=datetime.utcnow() if assigned_to_id else None,
            escalation_path=[{
                "assigned_to_type": assigned_to_type,
                "assigned_to_id": assigned_to_id,
                "level": level.value,
                "timestamp": datetime.utcnow().isoformat(),
            }] if assigned_to_id else [],
            related_task_id=related_task_id,
            related_project_id=related_project_id,
            related_agent_id=related_agent_id,
            conflict_parties=conflict_parties or [],
            sla_deadline=sla_deadline,
            due_date=due_date,
            impact_assessment=impact,
            urgency=urgency,
            department=department,
            tags=tags or [],
        )

        self.db.add(escalation)
        await self.db.flush()

        # Create timeline event
        await self._create_timeline_event(
            escalation_id=escalation.id,
            event_type=EscalationEventType.CREATED,
            actor_type=created_by_type,
            actor_id=created_by_id,
            description=f"Escalation created: {title}",
            new_state={"status": EscalationStatus.OPEN.value, "priority": priority.value},
        )

        # Create assignment event if auto-assigned
        if assigned_to_id:
            await self._create_timeline_event(
                escalation_id=escalation.id,
                event_type=EscalationEventType.ASSIGNED,
                actor_type="system",
                actor_id="auto_router",
                description=f"Auto-assigned to {assigned_to_id} ({assigned_to_type})",
                new_state={"assigned_to": assigned_to_id},
            )

        await self.db.commit()

        # Send notifications asynchronously
        asyncio.create_task(self._send_escalation_notifications(escalation.id, "created"))

        # Attempt auto-resolution
        asyncio.create_task(self._attempt_auto_resolution(escalation.id))

        logger.info(f"Created escalation {escalation_number} of type {escalation_type.value}")
        return escalation

    async def update_escalation(
        self,
        escalation_id: UUID,
        actor_type: str,
        actor_id: str,
        **updates
    ) -> AdvancedEscalation:
        """Update escalation fields with timeline tracking."""
        escalation = await self.get_escalation(escalation_id)
        if not escalation:
            raise ValueError(f"Escalation {escalation_id} not found")

        # Track changes
        previous_state = {}
        new_state = {}

        for key, value in updates.items():
            if hasattr(escalation, key):
                old_value = getattr(escalation, key)
                if old_value != value:
                    previous_state[key] = str(old_value) if old_value else None
                    new_state[key] = str(value) if value else None
                    setattr(escalation, key, value)

        escalation.updated_at = datetime.utcnow()

        # Create timeline event for significant changes
        if new_state:
            event_type = EscalationEventType.STATUS_CHANGED
            description = f"Updated: {', '.join(new_state.keys())}"

            if "status" in new_state:
                description = f"Status changed to {new_state['status']}"
            elif "priority" in new_state:
                event_type = EscalationEventType.PRIORITY_CHANGED
                description = f"Priority changed to {new_state['priority']}"

            await self._create_timeline_event(
                escalation_id=escalation.id,
                event_type=event_type,
                actor_type=actor_type,
                actor_id=actor_id,
                description=description,
                previous_state=previous_state,
                new_state=new_state,
            )

        await self.db.commit()
        return escalation

    async def resolve_escalation(
        self,
        escalation_id: UUID,
        resolution_type: ResolutionType,
        resolution_notes: str,
        resolved_by_type: str,
        resolved_by_id: str,
    ) -> AdvancedEscalation:
        """Resolve an escalation."""
        escalation = await self.get_escalation(escalation_id)
        if not escalation:
            raise ValueError(f"Escalation {escalation_id} not found")

        now = datetime.utcnow()
        escalation.status = EscalationStatus.RESOLVED
        escalation.resolved_at = now
        escalation.resolution_type = resolution_type
        escalation.resolution_notes = resolution_notes
        escalation.resolved_by_type = resolved_by_type
        escalation.resolved_by_id = resolved_by_id

        # Calculate resolution time
        time_to_resolution = int((now - escalation.created_at).total_seconds() / 60)
        escalation.time_to_resolution = time_to_resolution

        # Create timeline event
        await self._create_timeline_event(
            escalation_id=escalation.id,
            event_type=EscalationEventType.RESOLVED,
            actor_type=resolved_by_type,
            actor_id=resolved_by_id,
            description=f"Escalation resolved via {resolution_type.value}",
            new_state={
                "status": EscalationStatus.RESOLVED.value,
                "resolution_type": resolution_type.value,
                "time_to_resolution": time_to_resolution,
            },
        )

        await self.db.commit()

        # Send resolution notifications
        asyncio.create_task(self._send_escalation_notifications(escalation.id, "resolved"))

        logger.info(f"Resolved escalation {escalation.escalation_number} in {time_to_resolution} minutes")
        return escalation

    async def escalate_to_next_level(
        self,
        escalation_id: UUID,
        actor_type: str,
        actor_id: str,
        reason: str,
    ) -> AdvancedEscalation:
        """Escalate to the next hierarchical level."""
        escalation = await self.get_escalation(escalation_id)
        if not escalation:
            raise ValueError(f"Escalation {escalation_id} not found")

        # Determine next level
        current_level = escalation.level
        if current_level == EscalationLevel.DEPARTMENT:
            next_level = EscalationLevel.EXECUTIVE
        elif current_level == EscalationLevel.EXECUTIVE:
            next_level = EscalationLevel.HUMAN
        else:
            raise ValueError("Already at highest escalation level")

        # Get new assignee for the level
        new_assigned_to_type, new_assigned_to_id = await self._get_assignee_for_level(
            escalation.escalation_type, next_level
        )

        # Update escalation
        escalation.level = next_level
        escalation.assigned_to_type = new_assigned_to_type
        escalation.assigned_to_id = new_assigned_to_id
        escalation.assigned_at = datetime.utcnow()
        escalation.status = EscalationStatus.ESCALATED

        # Update escalation path
        escalation.escalation_path.append({
            "assigned_to_type": new_assigned_to_type,
            "assigned_to_id": new_assigned_to_id,
            "level": next_level.value,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason,
        })

        # Create timeline event
        await self._create_timeline_event(
            escalation_id=escalation.id,
            event_type=EscalationEventType.ESCALATED_TO_HIGHER_LEVEL,
            actor_type=actor_type,
            actor_id=actor_id,
            description=f"Escalated from {current_level.value} to {next_level.value}: {reason}",
            previous_state={"level": current_level.value},
            new_state={"level": next_level.value, "assigned_to": new_assigned_to_id},
        )

        await self.db.commit()

        # Send escalation notifications
        asyncio.create_task(self._send_escalation_notifications(escalation.id, "escalated"))

        logger.info(f"Escalated {escalation.escalation_number} to {next_level.value}")
        return escalation

    async def reassign_escalation(
        self,
        escalation_id: UUID,
        new_assigned_to_type: str,
        new_assigned_to_id: str,
        actor_type: str,
        actor_id: str,
        reason: Optional[str] = None,
    ) -> AdvancedEscalation:
        """Reassign escalation to a different handler."""
        escalation = await self.get_escalation(escalation_id)
        if not escalation:
            raise ValueError(f"Escalation {escalation_id} not found")

        old_assigned = f"{escalation.assigned_to_type}:{escalation.assigned_to_id}"
        new_assigned = f"{new_assigned_to_type}:{new_assigned_to_id}"

        escalation.assigned_to_type = new_assigned_to_type
        escalation.assigned_to_id = new_assigned_to_id
        escalation.assigned_at = datetime.utcnow()

        # Update escalation path
        escalation.escalation_path.append({
            "assigned_to_type": new_assigned_to_type,
            "assigned_to_id": new_assigned_to_id,
            "level": escalation.level.value,
            "timestamp": datetime.utcnow().isoformat(),
            "reason": reason or "Manual reassignment",
        })

        # Create timeline event
        await self._create_timeline_event(
            escalation_id=escalation.id,
            event_type=EscalationEventType.REASSIGNED,
            actor_type=actor_type,
            actor_id=actor_id,
            description=f"Reassigned from {old_assigned} to {new_assigned}",
            details={"reason": reason} if reason else {},
            previous_state={"assigned_to": old_assigned},
            new_state={"assigned_to": new_assigned},
        )

        await self.db.commit()

        # Send reassignment notifications
        asyncio.create_task(self._send_escalation_notifications(escalation.id, "reassigned"))

        return escalation

    # ==================== QUERY OPERATIONS ====================

    async def get_escalation(self, escalation_id: UUID) -> Optional[AdvancedEscalation]:
        """Get escalation by ID."""
        result = await self.db.execute(
            select(AdvancedEscalation).where(
                and_(
                    AdvancedEscalation.id == escalation_id,
                    AdvancedEscalation.deleted_at.is_(None)
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_escalations(
        self,
        status: Optional[List[EscalationStatus]] = None,
        priority: Optional[List[EscalationPriority]] = None,
        escalation_type: Optional[List[EscalationType]] = None,
        level: Optional[List[EscalationLevel]] = None,
        assigned_to_id: Optional[str] = None,
        department: Optional[str] = None,
        tags: Optional[List[str]] = None,
        sla_at_risk: bool = False,
        created_after: Optional[datetime] = None,
        created_before: Optional[datetime] = None,
        search: Optional[str] = None,
        skip: int = 0,
        limit: int = 50,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> tuple[List[AdvancedEscalation], int]:
        """
        List escalations with advanced filtering and pagination.
        Returns: (escalations, total_count)
        """
        # Build query conditions
        conditions = [AdvancedEscalation.deleted_at.is_(None)]

        if status:
            conditions.append(AdvancedEscalation.status.in_(status))
        if priority:
            conditions.append(AdvancedEscalation.priority.in_(priority))
        if escalation_type:
            conditions.append(AdvancedEscalation.escalation_type.in_(escalation_type))
        if level:
            conditions.append(AdvancedEscalation.level.in_(level))
        if assigned_to_id:
            conditions.append(AdvancedEscalation.assigned_to_id == assigned_to_id)
        if department:
            conditions.append(AdvancedEscalation.department == department)
        if tags:
            # Match any of the provided tags
            conditions.append(AdvancedEscalation.tags.overlap(tags))
        if sla_at_risk:
            # SLA at risk: less than 25% time remaining
            now = datetime.utcnow()
            conditions.append(AdvancedEscalation.sla_deadline <= now + timedelta(hours=6))
        if created_after:
            conditions.append(AdvancedEscalation.created_at >= created_after)
        if created_before:
            conditions.append(AdvancedEscalation.created_at <= created_before)
        if search:
            # Full-text search on title and description
            search_pattern = f"%{search}%"
            conditions.append(
                or_(
                    AdvancedEscalation.title.ilike(search_pattern),
                    AdvancedEscalation.description.ilike(search_pattern),
                    AdvancedEscalation.escalation_number.ilike(search_pattern),
                )
            )

        # Count query
        count_query = select(func.count()).select_from(AdvancedEscalation).where(and_(*conditions))
        count_result = await self.db.execute(count_query)
        total_count = count_result.scalar()

        # Data query
        query = select(AdvancedEscalation).where(and_(*conditions))

        # Order by
        order_column = getattr(AdvancedEscalation, order_by, AdvancedEscalation.created_at)
        if order_desc:
            query = query.order_by(desc(order_column))
        else:
            query = query.order_by(order_column)

        # Pagination
        query = query.offset(skip).limit(limit)

        result = await self.db.execute(query)
        escalations = result.scalars().all()

        return list(escalations), total_count

    async def get_escalation_timeline(
        self, escalation_id: UUID
    ) -> List[EscalationTimelineEvent]:
        """Get full timeline for an escalation."""
        result = await self.db.execute(
            select(EscalationTimelineEvent)
            .where(EscalationTimelineEvent.escalation_id == escalation_id)
            .order_by(EscalationTimelineEvent.timestamp)
        )
        return list(result.scalars().all())

    async def get_escalation_comments(
        self, escalation_id: UUID, include_internal: bool = True
    ) -> List[EscalationComment]:
        """Get all comments for an escalation."""
        conditions = [
            EscalationComment.escalation_id == escalation_id,
            EscalationComment.deleted_at.is_(None),
        ]

        if not include_internal:
            conditions.append(EscalationComment.is_internal == False)

        result = await self.db.execute(
            select(EscalationComment)
            .where(and_(*conditions))
            .order_by(EscalationComment.created_at)
        )
        return list(result.scalars().all())

    async def add_comment(
        self,
        escalation_id: UUID,
        author_type: str,
        author_id: str,
        content: str,
        is_internal: bool = False,
        parent_comment_id: Optional[UUID] = None,
        mentions: Optional[List[str]] = None,
    ) -> EscalationComment:
        """Add a comment to an escalation."""
        comment = EscalationComment(
            id=uuid4(),
            escalation_id=escalation_id,
            author_type=author_type,
            author_id=author_id,
            content=content,
            is_internal=is_internal,
            parent_comment_id=parent_comment_id,
            mentions=mentions or [],
        )

        self.db.add(comment)

        # Create timeline event
        await self._create_timeline_event(
            escalation_id=escalation_id,
            event_type=EscalationEventType.COMMENT_ADDED,
            actor_type=author_type,
            actor_id=author_id,
            description=f"Comment added: {content[:50]}...",
            details={"comment_id": str(comment.id)},
        )

        await self.db.commit()

        # Send mention notifications
        if mentions:
            asyncio.create_task(self._send_mention_notifications(escalation_id, comment.id, mentions))

        return comment

    # ==================== STATISTICS AND ANALYTICS ====================

    async def get_escalation_stats(
        self,
        department: Optional[str] = None,
        agent_id: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        """Get escalation statistics for dashboard."""
        conditions = [AdvancedEscalation.deleted_at.is_(None)]

        if department:
            conditions.append(AdvancedEscalation.department == department)
        if agent_id:
            conditions.append(
                or_(
                    AdvancedEscalation.assigned_to_id == agent_id,
                    AdvancedEscalation.created_by_id == agent_id,
                )
            )
        if start_date:
            conditions.append(AdvancedEscalation.created_at >= start_date)
        if end_date:
            conditions.append(AdvancedEscalation.created_at <= end_date)

        # Total escalations
        total_query = select(func.count()).select_from(AdvancedEscalation).where(and_(*conditions))
        total_result = await self.db.execute(total_query)
        total_escalations = total_result.scalar()

        # Open escalations
        open_conditions = conditions + [AdvancedEscalation.status.in_([
            EscalationStatus.OPEN,
            EscalationStatus.IN_PROGRESS,
            EscalationStatus.PENDING_AGENT,
            EscalationStatus.PENDING_HUMAN,
            EscalationStatus.BLOCKED,
        ])]
        open_query = select(func.count()).select_from(AdvancedEscalation).where(and_(*open_conditions))
        open_result = await self.db.execute(open_query)
        open_escalations = open_result.scalar()

        # Resolved today
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        resolved_today_conditions = conditions + [
            AdvancedEscalation.status == EscalationStatus.RESOLVED,
            AdvancedEscalation.resolved_at >= today_start,
        ]
        resolved_today_query = select(func.count()).select_from(AdvancedEscalation).where(
            and_(*resolved_today_conditions)
        )
        resolved_today_result = await self.db.execute(resolved_today_query)
        resolved_today = resolved_today_result.scalar()

        # Average resolution time
        resolved_conditions = conditions + [
            AdvancedEscalation.status == EscalationStatus.RESOLVED,
            AdvancedEscalation.time_to_resolution.is_not(None),
        ]
        avg_resolution_query = select(func.avg(AdvancedEscalation.time_to_resolution)).where(
            and_(*resolved_conditions)
        )
        avg_resolution_result = await self.db.execute(avg_resolution_query)
        avg_resolution_time = avg_resolution_result.scalar() or 0

        # SLA compliance rate
        sla_conditions = conditions + [AdvancedEscalation.status == EscalationStatus.RESOLVED]
        sla_query = select(
            func.count(),
            func.sum(
                func.cast(AdvancedEscalation.resolved_at <= AdvancedEscalation.sla_deadline, Integer)
            )
        ).where(and_(*sla_conditions))
        sla_result = await self.db.execute(sla_query)
        sla_row = sla_result.first()
        sla_total = sla_row[0] if sla_row else 0
        sla_compliant = sla_row[1] if sla_row else 0
        sla_compliance_rate = (sla_compliant / sla_total * 100) if sla_total > 0 else 100

        # Pending human decision
        human_pending_conditions = conditions + [
            AdvancedEscalation.status == EscalationStatus.PENDING_HUMAN,
        ]
        human_pending_query = select(func.count()).select_from(AdvancedEscalation).where(
            and_(*human_pending_conditions)
        )
        human_pending_result = await self.db.execute(human_pending_query)
        pending_human_decision = human_pending_result.scalar()

        # By type breakdown
        by_type_query = select(
            AdvancedEscalation.escalation_type,
            func.count()
        ).where(and_(*conditions)).group_by(AdvancedEscalation.escalation_type)
        by_type_result = await self.db.execute(by_type_query)
        by_type = {row[0].value: row[1] for row in by_type_result}

        # By priority breakdown
        by_priority_query = select(
            AdvancedEscalation.priority,
            func.count()
        ).where(and_(*conditions)).group_by(AdvancedEscalation.priority)
        by_priority_result = await self.db.execute(by_priority_query)
        by_priority = {row[0].value: row[1] for row in by_priority_result}

        return {
            "total_escalations": total_escalations,
            "open_escalations": open_escalations,
            "resolved_today": resolved_today,
            "average_resolution_time_minutes": round(avg_resolution_time, 2),
            "sla_compliance_rate": round(sla_compliance_rate, 2),
            "pending_human_decision": pending_human_decision,
            "by_type": by_type,
            "by_priority": by_priority,
        }

    # ==================== HELPER METHODS ====================

    async def _generate_escalation_number(self) -> str:
        """Generate unique escalation number (ESC-YYYY-NNN)."""
        year = datetime.utcnow().year
        prefix = f"ESC-{year}-"

        # Get the latest escalation number for this year
        result = await self.db.execute(
            select(AdvancedEscalation.escalation_number)
            .where(AdvancedEscalation.escalation_number.like(f"{prefix}%"))
            .order_by(desc(AdvancedEscalation.escalation_number))
            .limit(1)
        )
        latest = result.scalar_one_or_none()

        if latest:
            # Extract number and increment
            number = int(latest.split("-")[-1]) + 1
        else:
            number = 1

        return f"{prefix}{number:04d}"

    async def _get_sla_config(
        self, escalation_type: EscalationType, priority: EscalationPriority
    ) -> EscalationSLAConfig:
        """Get SLA configuration for escalation type and priority."""
        result = await self.db.execute(
            select(EscalationSLAConfig).where(
                and_(
                    EscalationSLAConfig.escalation_type == escalation_type,
                    EscalationSLAConfig.priority == priority,
                    EscalationSLAConfig.is_active == True,
                )
            )
        )
        config = result.scalar_one_or_none()

        if not config:
            # Return default SLA if no specific config found
            return EscalationSLAConfig(
                time_to_first_response=30,  # 30 minutes
                time_to_resolution=240,  # 4 hours
            )

        return config

    async def _auto_route_escalation(
        self, escalation_type: EscalationType, priority: EscalationPriority, department: Optional[str]
    ) -> tuple[str, str, EscalationLevel]:
        """
        Auto-route escalation based on type, priority, and department.
        Returns: (assigned_to_type, assigned_to_id, level)
        """
        # Escalation routing matrix implementation
        level = EscalationLevel.DEPARTMENT

        # High priority or critical issues start at executive level
        if priority in [EscalationPriority.CRITICAL, EscalationPriority.URGENT]:
            level = EscalationLevel.EXECUTIVE

        # Route based on escalation type
        routing_map = {
            EscalationType.TECHNICAL_DECISION: ("agent", "cto", EscalationLevel.EXECUTIVE),
            EscalationType.BUDGET_THRESHOLD: ("agent", "cfo", EscalationLevel.EXECUTIVE),
            EscalationType.AGENT_MALFUNCTION: ("agent", "hr", EscalationLevel.DEPARTMENT),
            EscalationType.RESOURCE_ALLOCATION: ("agent", "hr", EscalationLevel.DEPARTMENT),
            EscalationType.CROSS_DEPT_CONFLICT: ("agent", "coo", EscalationLevel.EXECUTIVE),
            EscalationType.DEADLINE_RISK: ("agent", "pm", EscalationLevel.DEPARTMENT),
            EscalationType.SCOPE_CHANGE: ("agent", "pm", EscalationLevel.DEPARTMENT),
            EscalationType.STRATEGIC_DIRECTION: ("agent", "ceo", EscalationLevel.HUMAN),
            EscalationType.RESOURCE_CONFLICT: ("agent", "pm", EscalationLevel.DEPARTMENT),
            EscalationType.PRIORITY_CONFLICT: ("agent", "pm", EscalationLevel.DEPARTMENT),
            EscalationType.BLOCKED_TASK: ("agent", "pm", EscalationLevel.DEPARTMENT),
            EscalationType.SCOPE_CREEP: ("agent", "pm", EscalationLevel.DEPARTMENT),
        }

        assigned_to_type, assigned_to_id, default_level = routing_map.get(
            escalation_type, ("agent", "pm", EscalationLevel.DEPARTMENT)
        )

        # Use higher of priority-based level or type-based level
        final_level = max(level, default_level, key=lambda x: ["department", "executive", "human"].index(x.value))

        return assigned_to_type, assigned_to_id, final_level

    async def _get_assignee_for_level(
        self, escalation_type: EscalationType, level: EscalationLevel
    ) -> tuple[str, str]:
        """Get appropriate assignee for escalation level."""
        if level == EscalationLevel.HUMAN:
            return "user", "human_reviewer"  # Placeholder for human decision maker
        elif level == EscalationLevel.EXECUTIVE:
            # Map to executive agents
            exec_map = {
                EscalationType.TECHNICAL_DECISION: "cto",
                EscalationType.BUDGET_THRESHOLD: "cfo",
                EscalationType.CROSS_DEPT_CONFLICT: "coo",
                EscalationType.STRATEGIC_DIRECTION: "ceo",
            }
            agent_id = exec_map.get(escalation_type, "ceo")
            return "agent", agent_id
        else:  # DEPARTMENT level
            # Map to department heads or PM
            return "agent", "pm"

    async def _create_timeline_event(
        self,
        escalation_id: UUID,
        event_type: EscalationEventType,
        actor_type: str,
        actor_id: str,
        description: str,
        details: Optional[Dict] = None,
        previous_state: Optional[Dict] = None,
        new_state: Optional[Dict] = None,
    ) -> EscalationTimelineEvent:
        """Create a timeline event for an escalation."""
        event = EscalationTimelineEvent(
            id=uuid4(),
            escalation_id=escalation_id,
            event_type=event_type,
            actor_type=actor_type,
            actor_id=actor_id,
            description=description,
            details=details or {},
            previous_state=previous_state,
            new_state=new_state,
        )
        self.db.add(event)
        return event

    async def _send_escalation_notifications(self, escalation_id: UUID, notification_type: str):
        """Send notifications for escalation events (async task)."""
        try:
            escalation = await self.get_escalation(escalation_id)
            if not escalation:
                return

            # Determine recipients based on notification type
            recipients = []

            if notification_type == "created":
                # Notify assigned person
                if escalation.assigned_to_id:
                    recipients.append({
                        "type": escalation.assigned_to_type,
                        "id": escalation.assigned_to_id,
                    })
            elif notification_type == "resolved":
                # Notify creator and stakeholders
                recipients.append({
                    "type": escalation.created_by_type,
                    "id": escalation.created_by_id,
                })
            elif notification_type in ["escalated", "reassigned"]:
                # Notify new assignee
                if escalation.assigned_to_id:
                    recipients.append({
                        "type": escalation.assigned_to_type,
                        "id": escalation.assigned_to_id,
                    })

            # Create notification records
            for recipient in recipients:
                notification = EscalationNotification(
                    id=uuid4(),
                    escalation_id=escalation.id,
                    recipient_type=recipient["type"],
                    recipient_id=recipient["id"],
                    notification_type=notification_type,
                    title=f"Escalation {notification_type}: {escalation.title}",
                    message=f"Escalation {escalation.escalation_number} has been {notification_type}",
                    priority=escalation.priority,
                    channels=["in_app", "email"],
                )
                self.db.add(notification)

            await self.db.commit()
            logger.info(f"Sent {len(recipients)} notifications for escalation {escalation.escalation_number}")

        except Exception as e:
            logger.error(f"Error sending notifications for escalation {escalation_id}: {e}")

    async def _send_mention_notifications(self, escalation_id: UUID, comment_id: UUID, mentions: List[str]):
        """Send notifications for @mentions in comments."""
        try:
            escalation = await self.get_escalation(escalation_id)
            if not escalation:
                return

            for mention in mentions:
                # Parse mention (format: "type:id")
                parts = mention.split(":")
                if len(parts) != 2:
                    continue

                recipient_type, recipient_id = parts
                notification = EscalationNotification(
                    id=uuid4(),
                    escalation_id=escalation.id,
                    recipient_type=recipient_type,
                    recipient_id=recipient_id,
                    notification_type="mention",
                    title=f"You were mentioned in {escalation.escalation_number}",
                    message=f"You were mentioned in a comment on escalation {escalation.escalation_number}",
                    priority=EscalationPriority.MEDIUM,
                    channels=["in_app"],
                )
                self.db.add(notification)

            await self.db.commit()

        except Exception as e:
            logger.error(f"Error sending mention notifications: {e}")

    async def _attempt_auto_resolution(self, escalation_id: UUID):
        """Attempt automatic resolution of escalation (async task)."""
        try:
            # This would integrate with the agentic flow engine
            # For now, just log the attempt
            escalation = await self.get_escalation(escalation_id)
            if not escalation:
                return

            logger.info(f"Auto-resolution attempt for {escalation.escalation_number}")

            # Update auto_resolution_attempts counter
            escalation.auto_resolution_attempts += 1
            await self.db.commit()

            # Here you would trigger agent collaboration or decision-making
            # based on the escalation type and context

        except Exception as e:
            logger.error(f"Error in auto-resolution attempt for {escalation_id}: {e}")

    # ==================== REVIEW TIMEOUT ESCALATION ====================

    async def check_and_escalate_review_timeouts(
        self,
        review_timeout_minutes: int = 5,
    ) -> List[UUID]:
        """
        Check for tasks in REVIEW status that exceed the timeout threshold.
        Automatically creates escalations for tasks pending review too long.
        Returns list of escalated task IDs.
        """
        try:
            now = datetime.utcnow()
            timeout_threshold = now - timedelta(minutes=review_timeout_minutes)

            # Find tasks in REVIEW status that started before the timeout threshold
            result = await self.db.execute(
                select(Task).where(
                    and_(
                        Task.status == "REVIEW",
                        Task.review_started_at.isnot(None),
                        Task.review_started_at <= timeout_threshold,
                        Task.deleted_at.is_(None),
                    )
                )
            )
            timed_out_tasks = result.scalars().all()

            escalated_task_ids = []

            for task in timed_out_tasks:
                # Check if escalation already exists for this task
                existing_escalation = await self._check_existing_review_escalation(task.task_id)
                if existing_escalation:
                    continue

                # Fetch project and agent info for context
                project = await self.db.execute(
                    select(Project).where(Project.project_id == task.project_id)
                )
                project = project.scalar_one_or_none()

                agent = await self.db.execute(
                    select(Agent).where(Agent.agent_id == task.assigned_to_agent_id)
                )
                agent = agent.scalar_one_or_none()

                # Create escalation for review timeout
                escalation = await self.create_escalation(
                    title=f"Task Review Timeout: {task.title}",
                    description=(
                        f"Task '{task.title}' has been in REVIEW status for more than "
                        f"{review_timeout_minutes} minutes and requires manager attention.\n\n"
                        f"Assigned to: {agent.name if agent else task.assigned_to_agent_id}\n"
                        f"Project: {project.name if project else 'Unknown'}\n"
                        f"Review started: {task.review_started_at}\n"
                        f"Time in review: {int((now - task.review_started_at).total_seconds() / 60)} minutes"
                    ),
                    escalation_type=EscalationType.BLOCKED_TASK,
                    priority=EscalationPriority.HIGH,
                    impact=ImpactLevel.HIGH,
                    urgency=UrgencyLevel.HIGH,
                    created_by_type="system",
                    created_by_id="review_timeout_monitor",
                    related_task_id=task.task_id,
                    related_project_id=task.project_id,
                    related_agent_id=task.assigned_to_agent_id,
                    tags=["review_timeout", "auto_escalation"],
                )

                escalated_task_ids.append(task.task_id)
                logger.warning(
                    f"Escalated task {task.task_id} due to review timeout. "
                    f"In review for {int((now - task.review_started_at).total_seconds() / 60)} minutes"
                )

            return escalated_task_ids

        except Exception as e:
            logger.error(f"Error checking review timeouts: {e}")
            return []

    async def _check_existing_review_escalation(self, task_id: UUID) -> Optional[AdvancedEscalation]:
        """Check if an open review timeout escalation already exists for a task."""
        result = await self.db.execute(
            select(AdvancedEscalation).where(
                and_(
                    AdvancedEscalation.related_task_id == task_id,
                    AdvancedEscalation.tags.contains(["review_timeout"]),
                    AdvancedEscalation.status.in_([
                        EscalationStatus.OPEN,
                        EscalationStatus.IN_PROGRESS,
                    ]),
                    AdvancedEscalation.deleted_at.is_(None),
                )
            )
        )
        return result.scalar_one_or_none()

    async def resolve_review_escalation(
        self,
        task_id: UUID,
        resolution_notes: str,
        clear_direction: str,
        resolved_by_agent_id: str,
    ) -> Task:
        """
        Resolve a review timeout escalation by providing clear direction to the task agent.
        This updates the task with manager feedback and returns it to IN_PROGRESS status.
        """
        # Get the task
        task_result = await self.db.execute(
            select(Task).where(Task.task_id == task_id)
        )
        task = task_result.scalar_one_or_none()

        if not task:
            raise ValueError(f"Task {task_id} not found")

        if task.status != "REVIEW":
            raise ValueError(f"Task {task_id} is not in REVIEW status")

        # Update task meta_data with manager feedback
        if not task.output:
            task.output = {}

        task.output["manager_feedback"] = {
            "resolved_by": resolved_by_agent_id,
            "resolved_at": datetime.utcnow().isoformat(),
            "resolution_notes": resolution_notes,
            "clear_direction": clear_direction,
        }

        # Set task back to IN_PROGRESS with clear requirements
        task.status = "IN_PROGRESS"
        task.blocking_reason = None
        task.review_started_at = None
        task.updated_at = datetime.utcnow()

        # Create message to agent with clear direction
        from app.db.models import Message

        message = Message(
            message_id=uuid4(),
            from_agent_id=resolved_by_agent_id,
            to_agent_id=task.assigned_to_agent_id,
            content=(
                f"Your task '{task.title}' has been reviewed and returned to IN_PROGRESS.\n\n"
                f"Manager feedback:\n{resolution_notes}\n\n"
                f"Clear direction on what needs to be done:\n{clear_direction}"
            ),
            message_type="ALERT",
            priority=Priority.HIGH,
            related_task_id=task.task_id,
            related_project_id=task.project_id,
        )
        self.db.add(message)

        # Mark related escalation as resolved
        escalation_result = await self.db.execute(
            select(AdvancedEscalation).where(
                and_(
                    AdvancedEscalation.related_task_id == task_id,
                    AdvancedEscalation.tags.contains(["review_timeout"]),
                    AdvancedEscalation.status.in_([
                        EscalationStatus.OPEN,
                        EscalationStatus.IN_PROGRESS,
                    ]),
                )
            )
        )
        escalation = escalation_result.scalar_one_or_none()

        if escalation:
            await self.resolve_escalation(
                escalation_id=escalation.id,
                resolution_type=ResolutionType.MANAGER_DECISION,
                resolution_notes=clear_direction,
                resolved_by_type="agent",
                resolved_by_id=resolved_by_agent_id,
            )

        await self.db.commit()

        logger.info(
            f"Resolved review escalation for task {task_id} "
            f"with clear direction from {resolved_by_agent_id}"
        )

        return task
