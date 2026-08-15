"""
Utility modules for error handling, LLM operations, and database operations.
"""

from .llm_error_handler import (
    handle_llm_errors,
    extract_llm_error_message,
    retry_with_exponential_backoff,
)
from .db_error_handler import (
    handle_database_error,
    DatabaseErrorHandler,
    handle_async_database_error,
)
from .api_errors import (
    handle_api_errors,
    validate_required_fields,
    validate_enum_field,
    validate_id_format,
    validate_range,
    validate_string_length,
)

__all__ = [
    # LLM error handling
    "handle_llm_errors",
    "extract_llm_error_message",
    "retry_with_exponential_backoff",
    # Database error handling
    "handle_database_error",
    "DatabaseErrorHandler",
    "handle_async_database_error",
    # API error handling
    "handle_api_errors",
    "validate_required_fields",
    "validate_enum_field",
    "validate_id_format",
    "validate_range",
    "validate_string_length",
]
