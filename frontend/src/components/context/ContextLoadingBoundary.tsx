/**
 * ContextLoadingBoundary - Handles loading and error states for context intelligence
 * Phase 2: Frontend Integration
 */

import React, { ReactNode } from "react";
import { AlertTriangle, Loader2, RefreshCw, AlertCircle } from "lucide-react";
import { cn } from "@/lib/utils";

interface ContextLoadingBoundaryProps {
  loading: boolean;
  error: Error | null;
  onRetry?: () => void;
  children: ReactNode;
  loadingMessage?: string;
  errorMessage?: string;
  fallback?: ReactNode;
  className?: string;
}

/**
 * Wraps context intelligence components with loading and error handling
 */
export function ContextLoadingBoundary({
  loading,
  error,
  onRetry,
  children,
  loadingMessage = "Loading context...",
  errorMessage = "Failed to load context intelligence",
  fallback,
  className,
}: ContextLoadingBoundaryProps) {
  if (error) {
    return (
      <div className={cn("p-4 border rounded-lg bg-red-50 border-red-200", className)}>
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-red-900 mb-1">{errorMessage}</h4>
            <p className="text-xs text-red-700 mb-2">{error.message}</p>
            {onRetry && (
              <button
                onClick={onRetry}
                className="inline-flex items-center gap-1 px-2 py-1 text-xs font-medium text-red-700 bg-red-100 hover:bg-red-200 rounded transition-colors"
              >
                <RefreshCw className="w-3 h-3" />
                Retry
              </button>
            )}
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    if (fallback) {
      return <>{fallback}</>;
    }

    return (
      <div className={cn("p-4 border rounded-lg bg-gray-50 border-gray-200", className)}>
        <div className="flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
          <span className="text-sm text-gray-600">{loadingMessage}</span>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}

/**
 * Inline loading indicator for smaller components
 */
export function InlineContextLoader({
  loading,
  error,
  size = "sm",
  className,
}: {
  loading: boolean;
  error?: Error | null;
  size?: "xs" | "sm" | "md";
  className?: string;
}) {
  const sizeMap = {
    xs: "w-3 h-3",
    sm: "w-4 h-4",
    md: "w-5 h-5",
  };

  if (error) {
    return (
      <span title={error.message}>
        <AlertCircle
          className={cn(sizeMap[size], "text-red-500", className)}
        />
      </span>
    );
  }

  if (loading) {
    return (
      <Loader2 className={cn(sizeMap[size], "animate-spin text-gray-400", className)} />
    );
  }

  return null;
}

/**
 * Loading skeleton for context panel
 */
export function ContextPanelSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("space-y-3 animate-pulse", className)}>
      {/* Intent skeleton */}
      <div>
        <div className="h-3 bg-gray-200 rounded w-24 mb-2" />
        <div className="h-6 bg-gray-200 rounded w-32" />
      </div>

      {/* Entities skeleton */}
      <div>
        <div className="h-3 bg-gray-200 rounded w-32 mb-2" />
        <div className="flex gap-2">
          <div className="h-6 bg-gray-200 rounded w-20" />
          <div className="h-6 bg-gray-200 rounded w-24" />
          <div className="h-6 bg-gray-200 rounded w-16" />
        </div>
      </div>

      {/* Stats skeleton */}
      <div className="pt-3 border-t">
        <div className="grid grid-cols-2 gap-3">
          <div className="h-4 bg-gray-200 rounded" />
          <div className="h-4 bg-gray-200 rounded" />
        </div>
      </div>
    </div>
  );
}

/**
 * Loading skeleton for message context indicator
 */
export function MessageContextSkeleton({ className }: { className?: string }) {
  return (
    <div className={cn("flex items-center gap-2 animate-pulse", className)}>
      <div className="h-5 bg-gray-200 rounded w-16" />
      <div className="h-5 bg-gray-200 rounded w-12" />
    </div>
  );
}

/**
 * Error banner for context intelligence failures
 */
export function ContextErrorBanner({
  error,
  onDismiss,
  onRetry,
  className,
}: {
  error: string;
  onDismiss?: () => void;
  onRetry?: () => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "flex items-center justify-between p-3 bg-yellow-50 border border-yellow-200 rounded-lg",
        className
      )}
    >
      <div className="flex items-center gap-2">
        <AlertCircle className="w-4 h-4 text-yellow-600" />
        <span className="text-sm text-yellow-800">{error}</span>
      </div>
      <div className="flex items-center gap-2">
        {onRetry && (
          <button
            onClick={onRetry}
            className="text-xs font-medium text-yellow-700 hover:text-yellow-900"
          >
            Retry
          </button>
        )}
        {onDismiss && (
          <button onClick={onDismiss} className="text-yellow-600 hover:text-yellow-800">
            <X className="w-4 h-4" />
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Graceful degradation wrapper
 * Shows fallback UI when context intelligence is unavailable
 */
export function ContextGracefulFallback({
  enabled,
  children,
  fallback,
}: {
  enabled: boolean;
  children: ReactNode;
  fallback?: ReactNode;
}) {
  if (!enabled) {
    if (fallback) {
      return <>{fallback}</>;
    }
    return null;
  }

  return <>{children}</>;
}

/**
 * Context feature flag wrapper
 */
export function ContextFeatureGuard({
  feature,
  children,
  fallback,
}: {
  feature: boolean;
  children: ReactNode;
  fallback?: ReactNode;
}) {
  if (!feature) {
    return fallback ? <>{fallback}</> : null;
  }

  return <>{children}</>;
}

function X({ className }: { className?: string }) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="2"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
    >
      <line x1="18" y1="6" x2="6" y2="18" />
      <line x1="6" y1="6" x2="18" y2="18" />
    </svg>
  );
}
