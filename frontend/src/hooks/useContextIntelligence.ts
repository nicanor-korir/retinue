/**
 * React hooks for Context Intelligence API
 * Phase 2: Frontend Integration
 */

import { useState, useEffect, useCallback, useRef } from "react";
import {
  ConversationContext,
  MessageContext,
  UserActivityProfile,
  ExtractContextResponse,
  ContextLoadingState,
} from "@/types/context-intelligence";
import { apiClient } from "@/lib/api";

/**
 * Hook to fetch and manage conversation context
 */
export function useConversationContext(conversationId?: string) {
  const [context, setContext] = useState<ConversationContext | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const fetchContext = useCallback(async () => {
    if (!conversationId) {
      setContext(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<ConversationContext>(
        `/conversations/${conversationId}/context`
      );
      setContext(response.data);
      setLastUpdated(new Date());
    } catch (err: any) {
      if (err.response?.status === 404) {
        // No context yet - this is okay
        setContext(null);
      } else {
        setError(err);
      }
    } finally {
      setLoading(false);
    }
  }, [conversationId]);

  useEffect(() => {
    fetchContext();
  }, [fetchContext]);

  return {
    context,
    loading,
    error,
    lastUpdated,
    refetch: fetchContext,
  };
}

/**
 * Hook to fetch message context
 */
export function useMessageContext(conversationId?: string, messageId?: string) {
  const [context, setContext] = useState<MessageContext | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchContext = useCallback(async () => {
    if (!conversationId || !messageId) {
      setContext(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<MessageContext>(
        `/conversations/${conversationId}/messages/${messageId}/context`
      );
      setContext(response.data);
    } catch (err: any) {
      if (err.response?.status === 404) {
        setContext(null);
      } else {
        setError(err);
      }
    } finally {
      setLoading(false);
    }
  }, [conversationId, messageId]);

  useEffect(() => {
    fetchContext();
  }, [fetchContext]);

  return {
    context,
    loading,
    error,
    refetch: fetchContext,
  };
}

/**
 * Hook to fetch user activity profile
 */
export function useUserActivityProfile(userId: string, days: number = 30) {
  const [profile, setProfile] = useState<UserActivityProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchProfile = useCallback(async () => {
    if (!userId) {
      setProfile(null);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<UserActivityProfile>(
        `/conversations/users/${userId}/activity-profile`,
        { params: { days } }
      );
      setProfile(response.data);
    } catch (err: any) {
      setError(err);
    } finally {
      setLoading(false);
    }
  }, [userId, days]);

  useEffect(() => {
    fetchProfile();
  }, [fetchProfile]);

  return {
    profile,
    loading,
    error,
    refetch: fetchProfile,
  };
}

/**
 * Hook to manually trigger context extraction
 */
export function useExtractContext() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [result, setResult] = useState<ExtractContextResponse | null>(null);

  const extractContext = useCallback(async (conversationId: string) => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await apiClient.post<ExtractContextResponse>(
        `/conversations/${conversationId}/extract-context`
      );
      setResult(response.data);
      return response.data;
    } catch (err: any) {
      setError(err);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    extractContext,
    loading,
    error,
    result,
  };
}

/**
 * Hook for real-time context updates via WebSocket
 */
export function useContextUpdates(conversationId?: string) {
  const [lastUpdate, setLastUpdate] = useState<any>(null);
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);

  useEffect(() => {
    if (!conversationId) return;

    // Connect to WebSocket for real-time updates
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    const wsUrl = `${protocol}//${window.location.host}/ws/conversations/${conversationId}`;

    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log("Context updates WebSocket connected");
      setConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Handle context enriched events
        if (data.type === "context_enriched") {
          setLastUpdate(data);
        }
      } catch (err) {
        console.error("Error parsing WebSocket message:", err);
      }
    };

    ws.onerror = (error) => {
      console.error("WebSocket error:", error);
      setConnected(false);
    };

    ws.onclose = () => {
      console.log("Context updates WebSocket disconnected");
      setConnected(false);
    };

    wsRef.current = ws;

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, [conversationId]);

  return {
    lastUpdate,
    connected,
  };
}

/**
 * Combined hook for all context features
 */
export function useContextIntelligence(
  conversationId?: string,
  options: {
    enableRealTimeUpdates?: boolean;
    autoRefresh?: boolean;
    refreshInterval?: number;
  } = {}
) {
  const {
    enableRealTimeUpdates = true,
    autoRefresh = false,
    refreshInterval = 30000, // 30 seconds
  } = options;

  const conversationContext = useConversationContext(conversationId);
  const contextUpdates = enableRealTimeUpdates
    ? useContextUpdates(conversationId)
    : { lastUpdate: null, connected: false };

  // Auto-refresh context when real-time update received
  useEffect(() => {
    if (contextUpdates.lastUpdate) {
      conversationContext.refetch();
    }
  }, [contextUpdates.lastUpdate, conversationContext]);

  // Auto-refresh at interval if enabled
  useEffect(() => {
    if (!autoRefresh || !conversationId) return;

    const interval = setInterval(() => {
      conversationContext.refetch();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [autoRefresh, conversationId, refreshInterval, conversationContext]);

  return {
    context: conversationContext.context,
    loading: conversationContext.loading,
    error: conversationContext.error,
    lastUpdated: conversationContext.lastUpdated,
    refetch: conversationContext.refetch,
    realTimeConnected: contextUpdates.connected,
    lastRealTimeUpdate: contextUpdates.lastUpdate,
  };
}

/**
 * Hook for caching context data to reduce API calls
 */
export function useCachedContext(conversationId?: string, ttl: number = 300000) {
  const cache = useRef<Map<string, { data: ConversationContext; timestamp: number }>>(
    new Map()
  );
  const [context, setContext] = useState<ConversationContext | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetchContext = useCallback(async (force: boolean = false) => {
    if (!conversationId) {
      setContext(null);
      return;
    }

    // Check cache first
    const cached = cache.current.get(conversationId);
    const now = Date.now();

    if (!force && cached && now - cached.timestamp < ttl) {
      setContext(cached.data);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.get<ConversationContext>(
        `/conversations/${conversationId}/context`
      );

      // Update cache
      cache.current.set(conversationId, {
        data: response.data,
        timestamp: now,
      });

      setContext(response.data);
    } catch (err: any) {
      if (err.response?.status === 404) {
        setContext(null);
      } else {
        setError(err);
      }
    } finally {
      setLoading(false);
    }
  }, [conversationId, ttl]);

  useEffect(() => {
    fetchContext();
  }, [fetchContext]);

  return {
    context,
    loading,
    error,
    refetch: () => fetchContext(true),
  };
}
