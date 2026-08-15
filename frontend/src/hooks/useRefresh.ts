import { useState } from "react";

type RefreshFunction = () => Promise<any>;

/**
 * Custom hook for managing refresh state
 * Handles loading state and error handling for refresh operations
 */
export function useRefresh(refreshFns: RefreshFunction | RefreshFunction[]) {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    setError(null);

    try {
      const fns = Array.isArray(refreshFns) ? refreshFns : [refreshFns];
      await Promise.all(fns.map(fn => fn()));
    } catch (err) {
      setError(err instanceof Error ? err : new Error("Refresh failed"));
      console.error("Refresh error:", err);
    } finally {
      setIsRefreshing(false);
    }
  };

  return { isRefreshing, error, handleRefresh };
}
