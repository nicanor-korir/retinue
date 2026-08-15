'use client';

import { useEffect, useState } from 'react';
import { AlertCircle, AlertTriangle, Clock, Zap, X, CheckCircle, Info } from 'lucide-react';
import { useErrorHandler, FormattedError } from '@/hooks/useErrorHandler';

type ToastType = 'error' | 'warning' | 'success' | 'info';

interface ErrorToastProps {
  error: any;
  autoClose?: boolean;
  duration?: number;
  onClose?: () => void;
}

interface Toast {
  id: string;
  error: any;
  type: ToastType;
  autoClose: boolean;
  duration: number;
}

// Global toast container state
let toastId = 0;
let toastListeners: Set<(toasts: Toast[]) => void> = new Set();
let toasts: Toast[] = [];

export function addErrorToast(error: any, autoClose = true, duration = 5000) {
  const id = `toast-${++toastId}`;

  const newToast: Toast = {
    id,
    error,
    type: getToastType(error),
    autoClose,
    duration,
  };

  toasts = [...toasts, newToast];
  notifyListeners();

  if (autoClose) {
    setTimeout(() => {
      removeToast(id);
    }, duration);
  }

  return id;
}

export function removeToast(id: string) {
  toasts = toasts.filter((t) => t.id !== id);
  notifyListeners();
}

function notifyListeners() {
  toastListeners.forEach((listener) => listener([...toasts]));
}

function getToastType(error: any): ToastType {
  const errorStr = JSON.stringify(error).toLowerCase();

  if (errorStr.includes('rate_limit')) {
    return 'warning';
  }
  if (errorStr.includes('success')) {
    return 'success';
  }
  if (errorStr.includes('info')) {
    return 'info';
  }

  return 'error';
}

/**
 * Individual toast component
 */
function Toast({ toast, onClose }: { toast: Toast; onClose: () => void }) {
  const { formatError, isRateLimitError, isTimeoutError, isLLMError } = useErrorHandler();
  const formatted = formatError(toast.error);

  let bgColor = 'bg-red-50';
  let borderColor = 'border-red-200';
  let textColor = 'text-red-800';
  let Icon = AlertCircle;

  if (toast.type === 'warning') {
    bgColor = 'bg-yellow-50';
    borderColor = 'border-yellow-200';
    textColor = 'text-yellow-800';
    Icon = AlertTriangle;
  } else if (toast.type === 'success') {
    bgColor = 'bg-green-50';
    borderColor = 'border-green-200';
    textColor = 'text-green-800';
    Icon = CheckCircle;
  } else if (toast.type === 'info') {
    bgColor = 'bg-blue-50';
    borderColor = 'border-blue-200';
    textColor = 'text-blue-800';
    Icon = Info;
  }

  return (
    <div
      className={`${bgColor} border ${borderColor} rounded-lg p-4 shadow-lg flex items-start gap-3 min-w-sm max-w-md`}
      role="alert"
    >
      <Icon className={`h-5 w-5 ${textColor} flex-shrink-0 mt-0.5`} />

      <div className="flex-1 min-w-0">
        <h3 className={`font-semibold text-sm ${textColor}`}>
          {getToastTitle(formatted.code)}
        </h3>
        <p className={`text-sm ${textColor} opacity-90 mt-1`}>
          {formatted.userMessage}
        </p>

        {/* Additional context */}
        {isRateLimitError(toast.error) && (
          <p className={`text-xs ${textColor} opacity-75 mt-2`}>
            Please wait before trying again.
          </p>
        )}

        {isTimeoutError(toast.error) && (
          <p className={`text-xs ${textColor} opacity-75 mt-2`}>
            Check your connection and try again.
          </p>
        )}

        {isLLMError(toast.error) && (
          <p className={`text-xs ${textColor} opacity-75 mt-2`}>
            The AI service encountered an issue.
          </p>
        )}
      </div>

      <button
        onClick={onClose}
        className="flex-shrink-0 mt-0.5"
        aria-label="Close toast"
      >
        <X className={`h-4 w-4 ${textColor} opacity-50 hover:opacity-100 transition-opacity`} />
      </button>
    </div>
  );
}

/**
 * Toast container - renders all active toasts
 */
export function ToastContainer() {
  const [toastList, setToastList] = useState<Toast[]>([]);

  useEffect(() => {
    const listener = (toasts: Toast[]) => {
      setToastList(toasts);
    };

    toastListeners.add(listener);

    return () => {
      toastListeners.delete(listener);
    };
  }, []);

  return (
    <div
      className="fixed bottom-4 right-4 space-y-3 pointer-events-none"
      role="region"
      aria-live="polite"
      aria-label="Toast notifications"
    >
      {toastList.map((toast) => (
        <div key={toast.id} className="pointer-events-auto">
          <Toast toast={toast} onClose={() => removeToast(toast.id)} />
        </div>
      ))}
    </div>
  );
}

/**
 * Hook for using toast notifications in components
 */
export function useToast() {
  const toast = (options: { title?: string; description?: string; variant?: string }) => {
    // Convert shadcn-style toast to our error toast format
    const error = {
      message: options.description || options.title || 'Notification',
      code: options.variant === 'destructive' ? 'error' : 'info',
    };
    return addErrorToast(error, true, 5000);
  };

  return {
    toast,
    error: (error: any, autoClose = true, duration = 5000) =>
      addErrorToast(error, autoClose, duration),
    remove: removeToast,
  };
}

function getToastTitle(code: string): string {
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
