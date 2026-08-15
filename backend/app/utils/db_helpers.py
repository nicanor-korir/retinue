"""
Database helper utilities to reduce code duplication across API endpoints.

This module provides reusable database operations following DRY principles.
"""

from typing import TypeVar, Type, Optional
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import DeclarativeMeta

T = TypeVar("T", bound=DeclarativeMeta)


async def get_or_404(
    session: AsyncSession,
    model: Type[T],
    entity_id: str,
    id_column: str = "id",
    error_message: Optional[str] = None
) -> T:
    """
    Get an entity by ID or raise 404 HTTPException.

    Args:
        session: Database session
        model: SQLAlchemy model class
        entity_id: ID of the entity to fetch
        id_column: Name of the ID column (default: "id")
        error_message: Custom error message (default: auto-generated)

    Returns:
        The entity if found

    Raises:
        HTTPException: 404 if entity not found

    Example:
        project = await get_or_404(session, Project, project_id, "project_id")
    """
    # Build the query
    id_attr = getattr(model, id_column)
    result = await session.execute(
        select(model).where(id_attr == entity_id)
    )
    entity = result.scalar_one_or_none()

    if not entity:
        entity_name = model.__tablename__.replace("_", " ").title()
        message = error_message or f"{entity_name} '{entity_id}' not found"
        raise HTTPException(status_code=404, detail=message)

    return entity


async def get_or_none(
    session: AsyncSession,
    model: Type[T],
    entity_id: str,
    id_column: str = "id"
) -> Optional[T]:
    """
    Get an entity by ID or return None if not found.

    Args:
        session: Database session
        model: SQLAlchemy model class
        entity_id: ID of the entity to fetch
        id_column: Name of the ID column (default: "id")

    Returns:
        The entity if found, None otherwise

    Example:
        project = await get_or_none(session, Project, project_id, "project_id")
    """
    id_attr = getattr(model, id_column)
    result = await session.execute(
        select(model).where(id_attr == entity_id)
    )
    return result.scalar_one_or_none()


async def exists(
    session: AsyncSession,
    model: Type[T],
    entity_id: str,
    id_column: str = "id"
) -> bool:
    """
    Check if an entity exists by ID.

    Args:
        session: Database session
        model: SQLAlchemy model class
        entity_id: ID of the entity to check
        id_column: Name of the ID column (default: "id")

    Returns:
        True if entity exists, False otherwise

    Example:
        if await exists(session, Project, project_id, "project_id"):
            # entity exists
    """
    entity = await get_or_none(session, model, entity_id, id_column)
    return entity is not None


def raise_not_found(entity_name: str, entity_id: str) -> None:
    """
    Raise a standardized 404 HTTPException.

    Args:
        entity_name: Name of the entity type (e.g., "Project", "Task")
        entity_id: ID of the entity

    Raises:
        HTTPException: 404 with formatted message

    Example:
        raise_not_found("Project", project_id)
    """
    raise HTTPException(
        status_code=404,
        detail=f"{entity_name} '{entity_id}' not found"
    )


def raise_bad_request(message: str) -> None:
    """
    Raise a standardized 400 HTTPException.

    Args:
        message: Error message

    Raises:
        HTTPException: 400 with message

    Example:
        raise_bad_request("Invalid agent IDs provided")
    """
    raise HTTPException(status_code=400, detail=message)


def raise_conflict(message: str) -> None:
    """
    Raise a standardized 409 HTTPException.

    Args:
        message: Error message

    Raises:
        HTTPException: 409 with message

    Example:
        raise_conflict("Entity already exists")
    """
    raise HTTPException(status_code=409, detail=message)
