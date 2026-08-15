import { useCallback } from 'react';
import axios, { AxiosError } from 'axios';

/**
 * Error response structure from backend
 */
export interface BackendError {
  error: {
    code: string;
    message: string;
    timestamp?: string;
    request_id?: string;
    field?: string;
    details?: Record<string, any>;
  };
}

/**
 * Standardized error format for frontend
 */
export interface FormattedError {
  code: string;
  message: string;
  userMessage: string;
  status?: number;
  field?: string;
  requestId?: string;
  timestamp?: string;
  details?: Record<string, any>;
}

/**
 * Hook for handling and formatting API errors
 */
export function useErrorHandler() {
  /**
   * Extract user-friendly message from backend error
   */
  const getErrorMessage = useCallback((error: any): string => {
    // Handle BackendError format
    if (error?.error?.message) {
      return error.error.message;
    }

    // Handle Axios error
    if (axios.isAxiosError(error)) {
      const status = error.response?.status;
      const data = error.response?.data as BackendError | undefined;

      // Try to extract message from backend error structure
      if (data?.error?.message) {
        return data.error.message;
      }

      // Handle specific HTTP status codes
      switch (status) {
        case 400:
          return 'Invalid request. Please check your input.';
        case 401:
          return 'Authentication failed. Please log in again.';
        case 403:
          return 'You do not have permission to perform this action.';
        case 404:
          return 'The requested resource was not found.';
        case 409:
          return 'This action conflicts with existing data. Please try again.';
        case 422:
          return 'Invalid data format. Please check your input.';
        case 429:
          return 'Too many requests. Please wait a moment and try again.';
        case 500:
          return 'An unexpected error occurred. Please try again later.';
        case 503:
          return 'The service is temporarily unavailable. Please try again later.';
        case 504:
          return 'Request timed out. Please try again.';
        default:
          break;
      }

      // Fallback to error message or status text
      if (error.message) {
        return error.message;
      }

      return 'An unexpected error occurred. Please try again.';
    }

    // Handle generic error
    if (error instanceof Error) {
      return error.message || 'An unexpected error occurred.';
    }

    // Fallback
    return 'An unexpected error occurred. Please try again.';
  }, []);

  /**
   * Format error into standardized structure
   */
  const formatError = useCallback((error: any): FormattedError => {
    const userMessage = getErrorMessage(error);

    // Handle BackendError format
    if (error?.error) {
      return {
        code: error.error.code || 'UNKNOWN_ERROR',
        message: error.error.message || userMessage,
        userMessage,
        field: error.error.field,
        requestId: error.error.request_id,
        timestamp: error.error.timestamp,
        details: error.error.details,
      };
    }

    // Handle Axios error
    if (axios.isAxiosError(error)) {
      const status = error.response?.status;
      const data = error.response?.data as BackendError | undefined;

      return {
        code: data?.error?.code || getStatusCode(status),
        message: data?.error?.message || error.message,
        userMessage,
        status,
        field: data?.error?.field,
        requestId: data?.error?.request_id,
        timestamp: data?.error?.timestamp,
        details: data?.error?.details,
      };
    }

    // Handle generic error
    return {
      code: 'UNKNOWN_ERROR',
      message: error?.message || 'An unexpected error occurred',
      userMessage,
    };
  }, [getErrorMessage]);

  /**
   * Check if error is a specific type
   */
  const isErrorType = useCallback((error: any, errorCode: string): boolean => {
    if (error?.error?.code) {
      return error.error.code === errorCode;
    }

    if (axios.isAxiosError(error)) {
      const data = error.response?.data as BackendError | undefined;
      return data?.error?.code === errorCode;
    }

    return false;
  }, []);

  /**
   * Check if error is a validation error
   */
  const isValidationError = useCallback((error: any): boolean => {
    return isErrorType(error, 'VALIDATION_ERROR');
  }, [isErrorType]);

  /**
   * Check if error is a not found error
   */
  const isNotFoundError = useCallback((error: any): boolean => {
    return isErrorType(error, 'NOT_FOUND');
  }, [isErrorType]);

  /**
   * Check if error is a conflict error
   */
  const isConflictError = useCallback((error: any): boolean => {
    return isErrorType(error, 'CONFLICT');
  }, [isErrorType]);

  /**
   * Check if error is a rate limit error
   */
  const isRateLimitError = useCallback((error: any): boolean => {
    return isErrorType(error, 'RATE_LIMIT_ERROR');
  }, [isErrorType]);

  /**
   * Check if error is a timeout error
   */
  const isTimeoutError = useCallback((error: any): boolean => {
    return isErrorType(error, 'TIMEOUT_ERROR');
  }, [isErrorType]);

  /**
   * Check if error is an LLM error
   */
  const isLLMError = useCallback((error: any): boolean => {
    return isErrorType(error, 'LLM_ERROR');
  }, [isErrorType]);

  /**
   * Get field error message (for form validation)
   */
  const getFieldError = useCallback((error: any, fieldName: string): string | null => {
    if (!isValidationError(error)) {
      return null;
    }

    if (error?.error?.field === fieldName) {
      return error.error.message;
    }

    // Check in details object
    if (error?.error?.details?.[fieldName]) {
      return error.error.details[fieldName];
    }

    return null;
  }, [isValidationError]);

  return {
    getErrorMessage,
    formatError,
    isErrorType,
    isValidationError,
    isNotFoundError,
    isConflictError,
    isRateLimitError,
    isTimeoutError,
    isLLMError,
    getFieldError,
  };
}

/**
 * Helper function to map HTTP status to error code
 */
function getStatusCode(status?: number): string {
  const statusMap: Record<number, string> = {
    400: 'BAD_REQUEST',
    401: 'UNAUTHORIZED',
    403: 'FORBIDDEN',
    404: 'NOT_FOUND',
    409: 'CONFLICT',
    422: 'VALIDATION_ERROR',
    429: 'RATE_LIMIT_ERROR',
    500: 'INTERNAL_ERROR',
    503: 'SERVICE_UNAVAILABLE',
    504: 'TIMEOUT_ERROR',
  };

  return statusMap[status || 0] || 'HTTP_ERROR';
}
