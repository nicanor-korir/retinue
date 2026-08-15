"""
Database error handling utilities for graceful error management.
Converts SQLAlchemy exceptions to user-friendly errors.
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.exc import (
    IntegrityError,
    DBAPIError,
    DisconnectionError,
    OperationalError,
    ProgrammingError,
    DataError,
)

from app.exceptions import (
    DatabaseError,
    ConflictError,
    ValidationError,
    NotFoundError,
)

logger = logging.getLogger(__name__)


def handle_database_error(error: Exception, operation: str = "database operation") -> Exception:
    """
    Convert SQLAlchemy exceptions to user-friendly Retinue exceptions.

    Args:
        error: SQLAlchemy exception
        operation: Description of the operation that failed

    Returns:
        Retinue exception with user-friendly message
    """

    error_str = str(error)
    logger.error(f"Database error during {operation}: {error_str}", exc_info=True)

    # Handle integrity errors (unique constraint, foreign key, not null, etc.)
    if isinstance(error, IntegrityError):
        # Check for specific constraint violations
        if "unique constraint" in error_str.lower():
            constraint_field = extract_constraint_field(error_str)
            return ConflictError(
                message=f"This {constraint_field or 'item'} already exists.",
                conflict_field=constraint_field,
                details={"error_type": "unique_constraint"}
            )

        if "foreign key constraint" in error_str.lower():
            return ValidationError(
                message="Referenced item does not exist.",
                details={"error_type": "foreign_key_constraint"}
            )

        if "not null constraint" in error_str.lower():
            field = extract_field_name(error_str)
            return ValidationError(
                message=f"Field '{field}' is required." if field else "Required field is missing.",
                field=field,
                details={"error_type": "not_null_constraint"}
            )

        # Generic integrity error
        return ConflictError(
            message="Data conflict occurred. Please check your input.",
            details={"error_type": "integrity_constraint"}
        )

    # Handle connection errors
    if isinstance(error, (DisconnectionError, OperationalError)):
        if "connection" in error_str.lower():
            return DatabaseError(
                message="Database connection lost. Please try again.",
                operation=operation,
                details={"error_type": "connection_lost"}
            )

        if "timeout" in error_str.lower():
            return DatabaseError(
                message="Database query timed out. Please try again.",
                operation=operation,
                details={"error_type": "query_timeout"}
            )

        return DatabaseError(
            message="Database is temporarily unavailable. Please try again.",
            operation=operation,
            details={"error_type": "connection_error"}
        )

    # Handle data errors (type mismatches, invalid data)
    if isinstance(error, DataError):
        return ValidationError(
            message="Invalid data format provided.",
            details={"error_type": "invalid_data_format"}
        )

    # Handle programming errors (SQL syntax, invalid column names, etc.)
    if isinstance(error, ProgrammingError):
        logger.error(f"Programming error (likely a bug): {error_str}")
        return DatabaseError(
            message="An unexpected database error occurred. Please contact support.",
            operation=operation,
            details={"error_type": "programming_error"}
        )

    # Handle generic DBAPIError
    if isinstance(error, DBAPIError):
        return DatabaseError(
            message="Database error occurred. Please try again.",
            operation=operation,
            details={"error_type": "db_api_error"}
        )

    # Fallback for unknown database errors
    return DatabaseError(
        message="An unexpected database error occurred. Please try again.",
        operation=operation,
        details={"error_type": "unknown_database_error"}
    )


def extract_constraint_field(error_str: str) -> Optional[str]:
    """Extract field name from constraint violation message."""
    # Common patterns in constraint messages
    patterns = [
        r'Key \((.*?)\)=',
        r'column "(.*?)"',
        r'field \'(.*?)\'',
        r'\((.*?)\)',
    ]

    import re
    for pattern in patterns:
        match = re.search(pattern, error_str, re.IGNORECASE)
        if match:
            field = match.group(1).strip()
            if field and not field.startswith('_'):
                return field

    return None


def extract_field_name(error_str: str) -> Optional[str]:
    """Extract field name from constraint error message."""
    import re

    # Try various patterns
    patterns = [
        r'column "([^"]+)"',
        r"column '([^']+)'",
        r'Field "([^"]+)"',
        r"Field '([^']+)'",
    ]

    for pattern in patterns:
        match = re.search(pattern, error_str)
        if match:
            return match.group(1)

    return None


class DatabaseErrorHandler:
    """Context manager for handling database errors."""

    def __init__(self, operation: str = "database operation"):
        self.operation = operation

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return False

        # Check if it's a database error
        if issubclass(exc_type, (IntegrityError, DBAPIError, DisconnectionError, OperationalError, DataError, ProgrammingError)):
            retinue_error = handle_database_error(exc_val, self.operation)
            raise retinue_error from exc_val

        # Let other exceptions propagate
        return False


async def handle_async_database_error(
    coro,
    operation: str = "database operation"
):
    """
    Execute async database operation and handle errors.

    Args:
        coro: Async coroutine to execute
        operation: Description of the operation

    Returns:
        Result from coroutine

    Raises:
        Retinue exception with user-friendly message
    """
    try:
        return await coro
    except Exception as e:
        if isinstance(e, (IntegrityError, DBAPIError, DisconnectionError, OperationalError, DataError, ProgrammingError)):
            retinue_error = handle_database_error(e, operation)
            raise retinue_error from e
        raise
