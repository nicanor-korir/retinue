"""
LLM error handling utilities for graceful Claude API error management.
Provides retry logic, timeout handling, and user-friendly error messages.
"""

import asyncio
import logging
import time
from typing import Optional, TypeVar, Callable, Any, Awaitable
from functools import wraps
from anthropic import (
    RateLimitError as AnthropicRateLimitError,
    APIError as AnthropicAPIError,
    APIStatusError as AnthropicAPIStatusError,
    APIConnectionError as AnthropicAPIConnectionError,
    Timeout as AnthropicTimeout,
    APITimeoutError as AnthropicAPITimeoutError,
)

from app.exceptions import RateLimitError, LLMError, TimeoutError as RetinueTimeoutError

logger = logging.getLogger(__name__)

T = TypeVar('T')

# Retry configuration
DEFAULT_MAX_RETRIES = 3
DEFAULT_INITIAL_BACKOFF = 1  # seconds
DEFAULT_MAX_BACKOFF = 60  # seconds
DEFAULT_TIMEOUT = 60  # seconds


def handle_llm_errors(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
    """
    Decorator to handle LLM API errors with retry logic and timeout.
    Converts Claude API exceptions to Retinue exceptions.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs) -> T:
        max_retries = kwargs.pop('max_retries', DEFAULT_MAX_RETRIES)
        timeout = kwargs.pop('timeout', DEFAULT_TIMEOUT)

        last_exception: Optional[Exception] = None

        for attempt in range(max_retries):
            try:
                # Wrap function call in timeout
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=timeout
                )

            except AnthropicRateLimitError as e:
                logger.warning(
                    f"Rate limit hit (attempt {attempt + 1}/{max_retries}): {e}",
                    exc_info=False
                )
                last_exception = e

                if attempt < max_retries - 1:
                    # Extract retry_after from headers if available
                    retry_after = getattr(e.response, 'headers', {}).get('retry-after', 60)
                    retry_after = int(retry_after) if isinstance(retry_after, str) else 60

                    logger.info(f"Retrying after {retry_after} seconds...")
                    await asyncio.sleep(retry_after)
                else:
                    raise RateLimitError(retry_after=retry_after)

            except AnthropicAPITimeoutError as e:
                logger.warning(
                    f"API timeout (attempt {attempt + 1}/{max_retries}): {e}",
                    exc_info=False
                )
                last_exception = e

                if attempt < max_retries - 1:
                    backoff = min(
                        DEFAULT_INITIAL_BACKOFF * (2 ** attempt),
                        DEFAULT_MAX_BACKOFF
                    )
                    logger.info(f"Retrying after {backoff} seconds...")
                    await asyncio.sleep(backoff)
                else:
                    raise RetinueTimeoutError(
                        message="AI service request timed out. Please try again.",
                        operation=func.__name__,
                        timeout_seconds=timeout
                    )

            except asyncio.TimeoutError as e:
                logger.warning(
                    f"Request timeout (attempt {attempt + 1}/{max_retries}): {e}",
                    exc_info=False
                )
                last_exception = e

                if attempt < max_retries - 1:
                    backoff = min(
                        DEFAULT_INITIAL_BACKOFF * (2 ** attempt),
                        DEFAULT_MAX_BACKOFF
                    )
                    logger.info(f"Retrying after {backoff} seconds...")
                    await asyncio.sleep(backoff)
                else:
                    raise RetinueTimeoutError(
                        message="Request timed out. Please try again.",
                        operation=func.__name__,
                        timeout_seconds=timeout
                    )

            except AnthropicAPIConnectionError as e:
                logger.warning(
                    f"Connection error (attempt {attempt + 1}/{max_retries}): {e}",
                    exc_info=False
                )
                last_exception = e

                if attempt < max_retries - 1:
                    backoff = min(
                        DEFAULT_INITIAL_BACKOFF * (2 ** attempt),
                        DEFAULT_MAX_BACKOFF
                    )
                    logger.info(f"Retrying after {backoff} seconds...")
                    await asyncio.sleep(backoff)
                else:
                    raise LLMError(
                        message="Failed to connect to the AI service. Please try again later.",
                        status_code=503,
                        details={"error_type": "connection_error"}
                    )

            except AnthropicAPIStatusError as e:
                # Non-retryable status errors (401, 403, etc.)
                status_code = getattr(e, 'status_code', 500)

                if status_code == 401:
                    raise LLMError(
                        message="Authentication failed with the AI service.",
                        status_code=401,
                        details={"error_type": "authentication_error"}
                    )
                elif status_code == 403:
                    raise LLMError(
                        message="Access denied to the AI service.",
                        status_code=403,
                        details={"error_type": "permission_error"}
                    )
                elif status_code == 400:
                    raise LLMError(
                        message="Invalid request to the AI service.",
                        status_code=400,
                        details={"error_type": "invalid_request"}
                    )
                elif status_code >= 500:
                    logger.warning(
                        f"Server error (attempt {attempt + 1}/{max_retries}): {e}",
                        exc_info=False
                    )
                    last_exception = e

                    if attempt < max_retries - 1:
                        backoff = min(
                            DEFAULT_INITIAL_BACKOFF * (2 ** attempt),
                            DEFAULT_MAX_BACKOFF
                        )
                        logger.info(f"Retrying after {backoff} seconds...")
                        await asyncio.sleep(backoff)
                    else:
                        raise LLMError(
                            message="The AI service is currently unavailable. Please try again later.",
                            status_code=503,
                            details={"error_type": "service_unavailable"}
                        )
                else:
                    raise LLMError(
                        message="An error occurred with the AI service.",
                        status_code=status_code,
                        details={"error_type": "api_error"}
                    )

            except AnthropicAPIError as e:
                # Generic Anthropic API error
                logger.warning(
                    f"API error (attempt {attempt + 1}/{max_retries}): {e}",
                    exc_info=False
                )
                last_exception = e

                if attempt < max_retries - 1:
                    backoff = min(
                        DEFAULT_INITIAL_BACKOFF * (2 ** attempt),
                        DEFAULT_MAX_BACKOFF
                    )
                    logger.info(f"Retrying after {backoff} seconds...")
                    await asyncio.sleep(backoff)
                else:
                    raise LLMError(
                        message="An error occurred with the AI service. Please try again.",
                        details={"error_type": "unknown_api_error"}
                    )

        # This shouldn't be reached, but just in case
        if last_exception:
            raise LLMError(
                message="Failed to complete AI request after retries.",
                details={"error_type": "max_retries_exceeded"}
            )

    return wrapper


def extract_llm_error_message(error: Exception) -> str:
    """
    Extract a user-friendly message from LLM error.
    Handles both Anthropic exceptions and Retinue exceptions.
    """
    error_str = str(error)

    # Check for specific error patterns
    if "rate_limit" in error_str.lower() or isinstance(error, AnthropicRateLimitError):
        return "The AI service is currently rate limited. Please try again in a few moments."

    if "authentication" in error_str.lower() or "unauthorized" in error_str.lower():
        return "Authentication failed. Please check your API configuration."

    if "token" in error_str.lower():
        return "The request exceeded the maximum token limit. Please try with a shorter prompt."

    if "connection" in error_str.lower() or isinstance(error, AnthropicAPIConnectionError):
        return "Failed to connect to the AI service. Please try again later."

    if "timeout" in error_str.lower() or isinstance(error, (AnthropicTimeout, AnthropicAPITimeoutError, asyncio.TimeoutError)):
        return "Request timed out. Please try again."

    if "overload" in error_str.lower() or "service unavailable" in error_str.lower():
        return "The AI service is currently overloaded. Please try again in a moment."

    if "invalid" in error_str.lower() and "request" in error_str.lower():
        return "Invalid request to the AI service. Please check your input."

    # Default fallback
    return "An error occurred with the AI service. Please try again."


async def retry_with_exponential_backoff(
    func: Callable[..., Awaitable[T]],
    *args,
    max_retries: int = DEFAULT_MAX_RETRIES,
    initial_backoff: float = DEFAULT_INITIAL_BACKOFF,
    max_backoff: float = DEFAULT_MAX_BACKOFF,
    timeout: int = DEFAULT_TIMEOUT,
    **kwargs
) -> T:
    """
    Execute async function with exponential backoff retry logic.

    Args:
        func: Async function to execute
        max_retries: Maximum number of retry attempts
        initial_backoff: Initial backoff time in seconds
        max_backoff: Maximum backoff time in seconds
        timeout: Timeout for each attempt in seconds
        *args, **kwargs: Arguments to pass to function

    Returns:
        Result from function

    Raises:
        RateLimitError: If rate limited
        RetinueTimeoutError: If timed out
        LLMError: For other LLM errors
    """
    for attempt in range(max_retries):
        try:
            return await asyncio.wait_for(
                func(*args, **kwargs),
                timeout=timeout
            )
        except Exception as e:
            if attempt == max_retries - 1:
                # Last attempt failed, raise the error
                if isinstance(e, (RateLimitError, RetinueTimeoutError, LLMError)):
                    raise
                raise LLMError(
                    message=extract_llm_error_message(e),
                    details={"error_type": type(e).__name__}
                )

            # Calculate backoff
            backoff = min(initial_backoff * (2 ** attempt), max_backoff)
            logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying in {backoff}s...")
            await asyncio.sleep(backoff)
