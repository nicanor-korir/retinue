"""
API error handling utilities for consistent error responses across endpoints.
"""

import logging
from typing import Optional, Dict, Any
from functools import wraps

from app.exceptions import (
    DeviantException,
    ValidationError,
    DatabaseError,
    NotFoundError,
)
from app.utils.db_error_handler import handle_database_error

logger = logging.getLogger(__name__)


def handle_api_errors(func):
    """
    Decorator to handle errors in API routes and convert them to proper responses.
    Catches database errors and converts them to Deviant exceptions.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except DeviantException:
            # Already a formatted Deviant error, re-raise
            raise
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}", exc_info=True)

            # Check if it's a database error
            from sqlalchemy.exc import (
                IntegrityError,
                DBAPIError,
                DisconnectionError,
                OperationalError,
                ProgrammingError,
                DataError,
            )

            if isinstance(e, (IntegrityError, DBAPIError, DisconnectionError, OperationalError, DataError, ProgrammingError)):
                Deviant_error = handle_database_error(e, func.__name__)
                raise Deviant_error from e

            # For other exceptions, convert to generic internal error
            from app.exceptions import InternalError
            raise InternalError(
                details={"function": func.__name__, "error_type": type(e).__name__}
            ) from e

    return wrapper


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> None:
    """
    Validate that all required fields are present in the data.

    Args:
        data: Dictionary to validate
        required_fields: List of required field names

    Raises:
        ValidationError: If any required field is missing or empty
    """
    for field in required_fields:
        if field not in data or (isinstance(data[field], str) and not data[field].strip()):
            raise ValidationError(
                message=f"Field '{field}' is required.",
                field=field
            )


def validate_enum_field(value: str, enum_class, field_name: str) -> None:
    """
    Validate that a value is a valid enum member.

    Args:
        value: Value to validate
        enum_class: Enum class to validate against
        field_name: Name of the field for error messages

    Raises:
        ValidationError: If value is not a valid enum member
    """
    try:
        enum_class[value]
    except KeyError:
        valid_values = list(enum_class.__members__.keys())
        raise ValidationError(
            message=f"Invalid value '{value}' for field '{field_name}'. Valid values are: {', '.join(valid_values)}",
            field=field_name,
            details={"valid_values": valid_values}
        )


def validate_id_format(id_value: str, field_name: str = "id") -> None:
    """
    Validate that an ID is in a proper format (UUID or simple string).

    Args:
        id_value: ID to validate
        field_name: Name of the field for error messages

    Raises:
        ValidationError: If ID format is invalid
    """
    if not id_value or not isinstance(id_value, str):
        raise ValidationError(
            message=f"Field '{field_name}' must be a non-empty string.",
            field=field_name
        )

    if len(id_value.strip()) == 0:
        raise ValidationError(
            message=f"Field '{field_name}' cannot be empty.",
            field=field_name
        )


def validate_range(value: int, min_val: int, max_val: int, field_name: str) -> None:
    """
    Validate that a value is within a specified range.

    Args:
        value: Value to validate
        min_val: Minimum valid value (inclusive)
        max_val: Maximum valid value (inclusive)
        field_name: Name of the field for error messages

    Raises:
        ValidationError: If value is out of range
    """
    if value < min_val or value > max_val:
        raise ValidationError(
            message=f"Field '{field_name}' must be between {min_val} and {max_val}, got {value}.",
            field=field_name,
            details={"min": min_val, "max": max_val, "value": value}
        )


def validate_string_length(value: str, min_len: int, max_len: int, field_name: str) -> None:
    """
    Validate that a string is within specified length bounds.

    Args:
        value: String to validate
        min_len: Minimum length (inclusive)
        max_len: Maximum length (inclusive)
        field_name: Name of the field for error messages

    Raises:
        ValidationError: If string length is out of bounds
    """
    if not isinstance(value, str):
        raise ValidationError(
            message=f"Field '{field_name}' must be a string.",
            field=field_name
        )

    length = len(value)
    if length < min_len or length > max_len:
        raise ValidationError(
            message=f"Field '{field_name}' must be between {min_len} and {max_len} characters, got {length}.",
            field=field_name,
            details={"min_length": min_len, "max_length": max_len, "actual_length": length}
        )
