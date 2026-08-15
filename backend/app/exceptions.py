"""
Custom exception hierarchy for Deviant application.
Provides consistent error handling and user-friendly error messages.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import uuid


class ErrorResponse:
    """Standardized error response structure."""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None
    ):
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.field = field
        self.timestamp = datetime.utcnow().isoformat()
        self.request_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON response."""
        response = {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "timestamp": self.timestamp,
                "request_id": self.request_id,
            }
        }

        if self.field:
            response["error"]["field"] = self.field

        if self.details:
            response["error"]["details"] = self.details

        return response


class DeviantException(Exception):
    """Base exception for all Deviant custom exceptions."""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        field: Optional[str] = None
    ):
        self.error_response = ErrorResponse(
            message=message,
            error_code=error_code,
            status_code=status_code,
            details=details,
            field=field
        )
        super().__init__(message)


class RateLimitError(DeviantException):
    """Raised when API rate limit is exceeded."""

    def __init__(self, retry_after: int = 60, details: Optional[Dict[str, Any]] = None):
        detail_dict = {"retry_after": retry_after}
        if details:
            detail_dict.update(details)

        super().__init__(
            message="API rate limit exceeded. Please try again later.",
            error_code="RATE_LIMIT_ERROR",
            status_code=429,
            details=detail_dict
        )
        self.retry_after = retry_after


class LLMError(DeviantException):
    """Raised when LLM/Claude API returns an error."""

    def __init__(
        self,
        message: str,
        status_code: int = 503,
        details: Optional[Dict[str, Any]] = None
    ):
        # Extract user-friendly message from Claude error if possible
        user_message = self._extract_user_message(message)

        super().__init__(
            message=user_message,
            error_code="LLM_ERROR",
            status_code=status_code,
            details=details
        )

    @staticmethod
    def _extract_user_message(error_msg: str) -> str:
        """Extract user-friendly message from Claude API error."""
        # Handle rate limit errors
        if "rate_limit" in error_msg.lower():
            return "The AI service is currently rate limited. Please try again in a few moments."

        # Handle authentication errors
        if "authentication" in error_msg.lower() or "unauthorized" in error_msg.lower():
            return "Authentication failed. Please check your API configuration."

        # Handle token limit errors
        if "token" in error_msg.lower():
            return "The request exceeded the maximum token limit. Please try with a shorter prompt."

        # Handle connection errors
        if "connection" in error_msg.lower() or "timeout" in error_msg.lower():
            return "Failed to connect to the AI service. Please try again later."

        # Handle overloaded errors
        if "overload" in error_msg.lower():
            return "The AI service is currently overloaded. Please try again in a moment."

        # Default fallback
        return "An error occurred with the AI service. Please try again."


class DatabaseError(DeviantException):
    """Raised when a database operation fails."""

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        detail_dict = {}
        if operation:
            detail_dict["operation"] = operation
        if details:
            detail_dict.update(details)

        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            status_code=500,
            details=detail_dict
        )


class ValidationError(DeviantException):
    """Raised when input validation fails."""

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=422,
            details=details,
            field=field
        )


class NotFoundError(DeviantException):
    """Raised when a requested resource is not found."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None
    ):
        details = {}
        if resource_type:
            details["resource_type"] = resource_type
        if resource_id:
            details["resource_id"] = resource_id

        super().__init__(
            message=message,
            error_code="NOT_FOUND",
            status_code=404,
            details=details
        )


class ConflictError(DeviantException):
    """Raised when operation conflicts with existing data."""

    def __init__(
        self,
        message: str,
        conflict_field: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        detail_dict = {}
        if conflict_field:
            detail_dict["conflict_field"] = conflict_field
        if details:
            detail_dict.update(details)

        super().__init__(
            message=message,
            error_code="CONFLICT",
            status_code=409,
            details=detail_dict
        )


class ForbiddenError(DeviantException):
    """Raised when user does not have permission to perform action."""

    def __init__(
        self,
        message: str = "You do not have permission to perform this action.",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="FORBIDDEN",
            status_code=403,
            details=details
        )


class InternalError(DeviantException):
    """Raised for unexpected internal errors."""

    def __init__(
        self,
        message: str = "An unexpected error occurred. Please try again later.",
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(
            message=message,
            error_code="INTERNAL_ERROR",
            status_code=500,
            details=details
        )


class TimeoutError(DeviantException):
    """Raised when an operation times out."""

    def __init__(
        self,
        message: str = "Request timed out. Please try again.",
        operation: Optional[str] = None,
        timeout_seconds: Optional[int] = None
    ):
        details = {}
        if operation:
            details["operation"] = operation
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds

        super().__init__(
            message=message,
            error_code="TIMEOUT_ERROR",
            status_code=504,
            details=details
        )


class InvalidStateError(DeviantException):
    """Raised when an operation is performed on an invalid state."""

    def __init__(
        self,
        message: str,
        current_state: Optional[str] = None,
        expected_state: Optional[str] = None
    ):
        details = {}
        if current_state:
            details["current_state"] = current_state
        if expected_state:
            details["expected_state"] = expected_state

        super().__init__(
            message=message,
            error_code="INVALID_STATE",
            status_code=409,
            details=details
        )
