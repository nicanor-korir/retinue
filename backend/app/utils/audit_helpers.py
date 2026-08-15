"""
Audit logging helper utilities to standardize audit log creation.

This module provides reusable audit logging operations following DRY principles.
"""

from typing import Any, Dict, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import AuditLog


async def create_audit_log(
    session: AsyncSession,
    actor: str,
    action: str,
    entity_type: str,
    entity_id: str,
    old_value: Optional[Dict[str, Any]] = None,
    new_value: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """
    Create and persist an audit log entry.

    Args:
        session: Database session
        actor: ID of the actor performing the action (agent_id or "system")
        action: Action being performed (e.g., "created", "updated", "deleted")
        entity_type: Type of entity (e.g., "project", "task", "agent")
        entity_id: ID of the entity being acted upon
        old_value: Previous value of the entity (for updates)
        new_value: New value of the entity
        metadata: Additional metadata about the action

    Returns:
        The created AuditLog instance

    Example:
        await create_audit_log(
            session=session,
            actor="pm_001",
            action="project_created",
            entity_type="project",
            entity_id=project_id,
            new_value={"name": "My Project", "status": "PLANNING"}
        )
    """
    audit_log = AuditLog(
        actor=actor,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_value or {},
        new_value=new_value or {},
        metadata=metadata or {}
    )
    session.add(audit_log)
    return audit_log


async def log_entity_created(
    session: AsyncSession,
    entity_type: str,
    entity_id: str,
    actor: str = "system",
    entity_data: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """
    Log entity creation.

    Args:
        session: Database session
        entity_type: Type of entity (e.g., "project", "task")
        entity_id: ID of the created entity
        actor: ID of the actor (default: "system")
        entity_data: Data of the created entity

    Returns:
        The created AuditLog instance

    Example:
        await log_entity_created(
            session, "project", project_id, "pm_001", {"name": "My Project"}
        )
    """
    return await create_audit_log(
        session=session,
        actor=actor,
        action=f"{entity_type}_created",
        entity_type=entity_type,
        entity_id=entity_id,
        new_value=entity_data or {}
    )


async def log_entity_updated(
    session: AsyncSession,
    entity_type: str,
    entity_id: str,
    actor: str,
    old_data: Dict[str, Any],
    new_data: Dict[str, Any],
    changed_fields: Optional[list[str]] = None
) -> AuditLog:
    """
    Log entity update.

    Args:
        session: Database session
        entity_type: Type of entity (e.g., "project", "task")
        entity_id: ID of the updated entity
        actor: ID of the actor
        old_data: Previous state of the entity
        new_data: New state of the entity
        changed_fields: List of fields that changed (optional)

    Returns:
        The created AuditLog instance

    Example:
        await log_entity_updated(
            session, "task", task_id, "dev_001",
            {"status": "IN_PROGRESS"},
            {"status": "COMPLETED"},
            ["status"]
        )
    """
    metadata = {}
    if changed_fields:
        metadata["changed_fields"] = changed_fields

    return await create_audit_log(
        session=session,
        actor=actor,
        action=f"{entity_type}_updated",
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=old_data,
        new_value=new_data,
        metadata=metadata
    )


async def log_entity_deleted(
    session: AsyncSession,
    entity_type: str,
    entity_id: str,
    actor: str,
    entity_data: Optional[Dict[str, Any]] = None
) -> AuditLog:
    """
    Log entity deletion.

    Args:
        session: Database session
        entity_type: Type of entity (e.g., "project", "task")
        entity_id: ID of the deleted entity
        actor: ID of the actor
        entity_data: Data of the deleted entity

    Returns:
        The created AuditLog instance

    Example:
        await log_entity_deleted(
            session, "project", project_id, "system", {"name": "Old Project"}
        )
    """
    return await create_audit_log(
        session=session,
        actor=actor,
        action=f"{entity_type}_deleted",
        entity_type=entity_type,
        entity_id=entity_id,
        old_value=entity_data or {}
    )


async def log_status_change(
    session: AsyncSession,
    entity_type: str,
    entity_id: str,
    actor: str,
    old_status: str,
    new_status: str,
    reason: Optional[str] = None
) -> AuditLog:
    """
    Log status change.

    Args:
        session: Database session
        entity_type: Type of entity (e.g., "project", "task")
        entity_id: ID of the entity
        actor: ID of the actor
        old_status: Previous status
        new_status: New status
        reason: Reason for status change (optional)

    Returns:
        The created AuditLog instance

    Example:
        await log_status_change(
            session, "project", project_id, "pm_001",
            "IN_PROGRESS", "COMPLETED"
        )
    """
    metadata = {}
    if reason:
        metadata["reason"] = reason

    return await create_audit_log(
        session=session,
        actor=actor,
        action=f"{entity_type}_status_changed",
        entity_type=entity_type,
        entity_id=entity_id,
        old_value={"status": old_status},
        new_value={"status": new_status},
        metadata=metadata
    )
