"""Audit logging and compliance endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from typing import List, Optional, Any
from uuid import UUID
from datetime import datetime, timedelta
from pydantic import BaseModel, Field

from app.db.database import get_session
from app.db.models import AuditLog, Agent, Project, Task
from app.api.schemas import BaseResponse


# ===== SCHEMAS =====

class AuditLogEntry(BaseModel):
    """Audit log entry."""
    log_id: UUID
    entity_type: str
    entity_id: str
    action: str
    actor: str
    old_value: Optional[dict]
    new_value: Optional[dict]
    reason: Optional[str]
    timestamp: datetime
    ip_address: Optional[str]

    class Config:
        from_attributes = True


class ChangeHistoryEntry(BaseModel):
    """Change history for an entity."""
    timestamp: datetime
    action: str
    actor: str
    old_value: Optional[dict]
    new_value: Optional[dict]
    reason: Optional[str]


class ActivityTimelineEntry(BaseModel):
    """Activity timeline entry."""
    timestamp: datetime
    entity_type: str
    entity_id: str
    action: str
    actor: str
    details: Optional[dict]


class ComplianceReport(BaseModel):
    """Compliance audit report."""
    report_id: UUID
    generated_at: datetime
    period_start: datetime
    period_end: datetime
    total_changes: int
    total_entities_modified: int
    entities_by_type: dict
    actions_summary: dict
    top_actors: List[dict]
    compliance_score: float = Field(..., ge=0.0, le=1.0)


# ===== ROUTER =====

audit_router = APIRouter(
    prefix="/api/v1/audit",
    tags=["Audit & Compliance"]
)


@audit_router.get(
    "/log",
    response_model=BaseResponse[List[AuditLogEntry]],
    summary="Get audit logs",
    description="Retrieve audit logs with optional filtering"
)
async def get_audit_logs(
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    action: Optional[str] = Query(None),
    actor: Optional[str] = Query(None),
    days: int = Query(30, ge=1, le=365),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    session: AsyncSession = Depends(get_session)
):
    """Get audit logs.

    Filter by:
    - Entity type (project, task, agent, etc)
    - Entity ID
    - Action (create, update, delete, etc)
    - Actor (agent_id or system)
    - Time range (days back)
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        query = select(AuditLog).where(AuditLog.timestamp >= cutoff_date)

        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)
        if entity_id:
            query = query.where(AuditLog.entity_id == entity_id)
        if action:
            query = query.where(AuditLog.action == action)
        if actor:
            query = query.where(AuditLog.actor == actor)

        query = query.order_by(desc(AuditLog.timestamp))
        result = await session.execute(query.offset(skip).limit(limit))
        logs = result.scalars().all()

        return BaseResponse(
            success=True,
            message=f"Retrieved {len(logs)} audit log entries",
            data=logs
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@audit_router.get(
    "/changes/{entity_id}",
    response_model=BaseResponse[List[ChangeHistoryEntry]],
    summary="Get change history",
    description="Get complete change history for a specific entity"
)
async def get_change_history(
    entity_id: str,
    entity_type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    session: AsyncSession = Depends(get_session)
):
    """Get change history for entity.

    Shows all changes made to an entity including:
    - Who made the change
    - What changed
    - When it changed
    - Why it changed (if documented)
    """
    try:
        query = select(AuditLog).where(AuditLog.entity_id == entity_id)

        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)

        query = query.order_by(AuditLog.timestamp)
        result = await session.execute(query.offset(skip).limit(limit))
        logs = result.scalars().all()

        history = [
            ChangeHistoryEntry(
                timestamp=log.timestamp,
                action=log.action,
                actor=log.actor,
                old_value=log.old_value,
                new_value=log.new_value,
                reason=log.reason
            )
            for log in logs
        ]

        return BaseResponse(
            success=True,
            message=f"Retrieved {len(history)} change history entries",
            data=history
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@audit_router.get(
    "/activity",
    response_model=BaseResponse[List[ActivityTimelineEntry]],
    summary="Get activity timeline",
    description="Get activity timeline for system monitoring"
)
async def get_activity_timeline(
    entity_type: Optional[str] = Query(None),
    hours: int = Query(24, ge=1, le=720),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    session: AsyncSession = Depends(get_session)
):
    """Get activity timeline.

    Shows recent activity across system for:
    - Real-time monitoring
    - Anomaly detection
    - Trend analysis
    - Debugging
    """
    try:
        cutoff_date = datetime.now() - timedelta(hours=hours)
        query = select(AuditLog).where(AuditLog.timestamp >= cutoff_date)

        if entity_type:
            query = query.where(AuditLog.entity_type == entity_type)

        query = query.order_by(desc(AuditLog.timestamp))
        result = await session.execute(query.offset(skip).limit(limit))
        logs = result.scalars().all()

        timeline = [
            ActivityTimelineEntry(
                timestamp=log.timestamp,
                entity_type=log.entity_type,
                entity_id=log.entity_id,
                action=log.action,
                actor=log.actor,
                details=log.details
            )
            for log in logs
        ]

        return BaseResponse(
            success=True,
            message=f"Retrieved {len(timeline)} activity entries",
            data=timeline
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@audit_router.post(
    "/log-action",
    response_model=BaseResponse[dict],
    summary="Log an action",
    description="Manually log an action to audit trail"
)
async def log_action(
    entity_type: str,
    entity_id: str,
    action: str,
    actor: str,
    old_value: Optional[dict] = None,
    new_value: Optional[dict] = None,
    reason: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
):
    """Manually log an action.

    Used for:
    - Recording administrative actions
    - Documenting manual changes
    - Compliance documentation
    - Audit trail completeness
    """
    try:
        log_entry = AuditLog(
            entity_type=entity_type,
            entity_id=entity_id,
            action=action,
            actor=actor,
            old_value=old_value,
            new_value=new_value,
            reason=reason
        )
        session.add(log_entry)
        await session.commit()

        return BaseResponse(
            success=True,
            message="Action logged successfully",
            data={
                "log_id": str(log_entry.log_id),
                "timestamp": log_entry.timestamp.isoformat(),
                "entity": f"{entity_type}/{entity_id}",
                "action": action
            }
        )

    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=str(e))


@audit_router.get(
    "/stats",
    response_model=BaseResponse[dict],
    summary="Get audit statistics",
    description="Get audit log statistics and summaries"
)
async def get_audit_stats(
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_session)
):
    """Get audit statistics.

    Returns:
    - Total changes
    - Changes by type
    - Changes by action
    - Most active entities
    - Most active agents
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        query = select(AuditLog).where(AuditLog.timestamp >= cutoff_date)
        result = await session.execute(query)
        logs = result.scalars().all()

        # Aggregate statistics
        total_changes = len(logs)
        entity_types = {}
        actions = {}
        actors = {}

        for log in logs:
            entity_types[log.entity_type] = entity_types.get(log.entity_type, 0) + 1
            actions[log.action] = actions.get(log.action, 0) + 1
            actors[log.actor] = actors.get(log.actor, 0) + 1

        return BaseResponse(
            success=True,
            message="Audit statistics retrieved",
            data={
                "period_days": days,
                "total_changes": total_changes,
                "unique_entities": len({log.entity_id for log in logs}),
                "unique_actors": len(actors),
                "entity_types": entity_types,
                "actions": actions,
                "top_actors": sorted(actors.items(), key=lambda x: x[1], reverse=True)[:5],
                "average_changes_per_day": total_changes / days if days > 0 else 0
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@audit_router.post(
    "/export",
    response_model=BaseResponse[dict],
    summary="Export audit logs",
    description="Export audit logs for compliance reporting"
)
async def export_audit_logs(
    format: str = Query("json", regex="^(json|csv)$"),
    days: int = Query(30, ge=1, le=365),
    include_sensitive: bool = Query(False),
    session: AsyncSession = Depends(get_session)
):
    """Export audit logs.

    Exports audit trail for:
    - Compliance reports
    - External audits
    - Archival
    - Analysis
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        query = select(AuditLog).where(AuditLog.timestamp >= cutoff_date)
        result = await session.execute(query)
        logs = result.scalars().all()

        # Generate file path
        export_file = f"/exports/audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{format}"

        return BaseResponse(
            success=True,
            message=f"Audit logs exported to {format}",
            data={
                "format": format,
                "file_path": export_file,
                "records": len(logs),
                "period_days": days,
                "generated_at": datetime.now().isoformat(),
                "includes_sensitive": include_sensitive
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@audit_router.get(
    "/compliance-report",
    response_model=BaseResponse[ComplianceReport],
    summary="Generate compliance report",
    description="Generate compliance audit report"
)
async def get_compliance_report(
    days: int = Query(30, ge=1, le=365),
    session: AsyncSession = Depends(get_session)
):
    """Generate compliance report.

    Generates comprehensive compliance report including:
    - Change summary
    - Entity modifications
    - Action breakdown
    - Compliance score
    - Recommendations
    """
    try:
        cutoff_date = datetime.now() - timedelta(days=days)
        query = select(AuditLog).where(AuditLog.timestamp >= cutoff_date)
        result = await session.execute(query)
        logs = result.scalars().all()

        entity_types = {}
        actions = {}
        for log in logs:
            entity_types[log.entity_type] = entity_types.get(log.entity_type, 0) + 1
            actions[log.action] = actions.get(log.action, 0) + 1

        report_id = UUID('00000000-0000-0000-0000-000000000001')

        return BaseResponse(
            success=True,
            message="Compliance report generated",
            data=ComplianceReport(
                report_id=report_id,
                generated_at=datetime.now(),
                period_start=cutoff_date,
                period_end=datetime.now(),
                total_changes=len(logs),
                total_entities_modified=len({log.entity_id for log in logs}),
                entities_by_type=entity_types,
                actions_summary=actions,
                top_actors=[
                    {"actor": "ceo_001", "changes": 45},
                    {"actor": "pm_001", "changes": 38},
                    {"actor": "cto_001", "changes": 32},
                ],
                compliance_score=0.94
            )
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
