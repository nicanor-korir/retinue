'use client';

import { AlertCircle, AlertTriangle, Clock, Zap, X } from 'lucide-react';
import { useErrorHandler, FormattedError } from '@/hooks/useErrorHandler';
import { useState } from 'react';

interface ErrorDisplayProps {
  error: any;
  onDismiss?: () => void;
  showDismiss?: boolean;
  compact?: boolean;
}

export function ErrorDisplay({ error, onDismiss, showDismiss = true, compact = false }: ErrorDisplayProps) {
  const { formatError, isRateLimitError, isTimeoutError, isLLMError } = useErrorHandler();
  const [isDismissed, setIsDismissed] = useState(false);

  if (!error || isDismissed) {
    return null;
  }

  const formatted = formatError(error);

  const handleDismiss = () => {
    setIsDismissed(true);
    onDismiss?.();
  };

  // Determine error type and styling
  let bgColor = 'bg-red-50';
  let borderColor = 'border-red-200';
  let textColor = 'text-red-800';
  let Icon = AlertCircle;

  if (isRateLimitError(error)) {
    bgColor = 'bg-yellow-50';
    borderColor = 'border-yellow-200';
    textColor = 'text-yellow-800';
    Icon = Zap;
  } else if (isTimeoutError(error)) {
    bgColor = 'bg-orange-50';
    borderColor = 'border-orange-200';
    textColor = 'text-orange-800';
    Icon = Clock;
  } else if (isLLMError(error)) {
    bgColor = 'bg-purple-50';
    borderColor = 'border-purple-200';
    textColor = 'text-purple-800';
    Icon = AlertTriangle;
  }

  if (compact) {
    return (
      <div className={`${bgColor} border ${borderColor} rounded-lg p-3`}>
        <div className="flex items-start gap-2">
          <Icon className={`h-4 w-4 ${textColor} flex-shrink-0 mt-0.5`} />
          <div className="flex-1 min-w-0">
            <p className={`text-sm font-medium ${textColor}`}>
              {formatted.userMessage}
            </p>
          </div>
          {showDismiss && (
            <button
              onClick={handleDismiss}
              className="flex-shrink-0 ml-2"
              aria-label="Dismiss error"
            >
              <X className={`h-4 w-4 ${textColor} opacity-50 hover:opacity-100`} />
            </button>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className={`${bgColor} border ${borderColor} rounded-lg p-4`}>
      <div className="flex items-start gap-3">
        <Icon className={`h-5 w-5 ${textColor} flex-shrink-0 mt-0.5`} />

        <div className="flex-1 min-w-0">
          <h3 className={`text-sm font-semibold ${textColor} mb-1`}>
            {getErrorTitle(formatted.code)}
          </h3>

          <p className={`text-sm ${textColor} opacity-90 mb-2`}>
            {formatted.userMessage}
          </p>

          {/* Additional help text for specific error types */}
          {isRateLimitError(error) && (
            <p className={`text-xs ${textColor} opacity-75`}>
              Please wait a moment before trying again.
              {formatted.details?.retry_after && ` (Retry after ${formatted.details.retry_after} seconds)`}
            </p>
          )}

          {isTimeoutError(error) && (
            <p className={`text-xs ${textColor} opacity-75`}>
              The request took too long. Please check your connection and try again.
            </p>
          )}

          {isLLMError(error) && (
            <p className={`text-xs ${textColor} opacity-75`}>
              The AI service encountered an issue. Please try again in a moment.
            </p>
          )}

          {/* Debug info (only in development) */}
          {process.env.NODE_ENV === 'development' && formatted.requestId && (
            <p className={`text-xs ${textColor} opacity-50 mt-2 font-mono`}>
              Request ID: {formatted.requestId}
            </p>
          )}
        </div>

        {showDismiss && (
          <button
            onClick={handleDismiss}
            className="flex-shrink-0"
            aria-label="Dismiss error"
          >
            <X className={`h-5 w-5 ${textColor} opacity-50 hover:opacity-100 transition-opacity`} />
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Get user-friendly error title based on error code
 */
function getErrorTitle(code: string): string {
  const titles: Record<string, string> = {
    'BAD_REQUEST': 'Invalid Request',
    'UNAUTHORIZED': 'Authentication Failed',
    'FORBIDDEN': 'Access Denied',
    'NOT_FOUND': 'Not Found',
    'CONFLICT': 'Data Conflict',
    'VALIDATION_ERROR': 'Validation Error',
    'RATE_LIMIT_ERROR': 'Rate Limited',
    'INTERNAL_ERROR': 'Server Error',
    'SERVICE_UNAVAILABLE': 'Service Unavailable',
    'TIMEOUT_ERROR': 'Request Timeout',
    'LLM_ERROR': 'AI Service Error',
    'DATABASE_ERROR': 'Database Error',
  };

  return titles[code] || 'Error';
}
