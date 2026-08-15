/**
 * Custom React hooks for Escalation Management System
 */
import { useState, useEffect, useCallback } from 'react';
import {
  Escalation,
  EscalationListResponse,
  EscalationStats,
  TimelineEvent,
  Comment,
  CreateEscalationRequest,
  UpdateEscalationRequest,
  ResolveEscalationRequest,
  EscalateRequest,
  ReassignRequest,
  AddCommentRequest,
  EscalationFilters,
} from '../types/escalation';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Helper function for API calls
async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
    throw new Error(error.detail || `HTTP error! status: ${response.status}`);
  }

  return response.json();
}

/**
 * Hook to fetch escalation statistics
 */
export function useEscalationStats(
  department?: string,
  agent_id?: string
) {
  const [stats, setStats] = useState<EscalationStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      if (department) params.append('department', department);
      if (agent_id) params.append('agent_id', agent_id);

      const data = await apiFetch<EscalationStats>(
        `/api/v1/escalations/stats/dashboard${params.toString()}`
      );

      setStats(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch stats');
    } finally {
      setLoading(false);
    }
  }, [department, agent_id]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  return { stats, loading, error, refetch: fetchStats };
}

/**
 * Hook to fetch and manage escalations list
 */
export function useEscalations(filters: EscalationFilters = {}) {
  const [data, setData] = useState<EscalationListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEscalations = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      
      if (filters.status) {
        filters.status.forEach(s => params.append('status', s));
      }
      if (filters.priority) {
        filters.priority.forEach(p => params.append('priority', p));
      }
      if (filters.type) {
        filters.type.forEach(t => params.append('type', t));
      }
      if (filters.level) {
        filters.level.forEach(l => params.append('level', l));
      }
      if (filters.assigned_to_id) params.append('assigned_to_id', filters.assigned_to_id);
      if (filters.department) params.append('department', filters.department);
      if (filters.tags) {
        filters.tags.forEach(tag => params.append('tags', tag));
      }
      if (filters.sla_at_risk !== undefined) {
        params.append('sla_at_risk', String(filters.sla_at_risk));
      }
      if (filters.search) params.append('search', filters.search);
      if (filters.page) params.append('page', String(filters.page));
      if (filters.per_page) params.append('per_page', String(filters.per_page));
      if (filters.order_by) params.append('order_by', filters.order_by);
      if (filters.order_desc !== undefined) {
        params.append('order_desc', String(filters.order_desc));
      }

      const response = await apiFetch<EscalationListResponse>(
        `/api/v1/escalations?${params.toString()}`
      );

      setData(response);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch escalations');
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    fetchEscalations();
  }, [fetchEscalations]);

  return {
    escalations: data?.escalations || [],
    total: data?.total || 0,
    page: data?.page || 1,
    per_page: data?.per_page || 50,
    loading,
    error,
    refetch: fetchEscalations,
  };
}

/**
 * Hook to fetch a single escalation
 */
export function useEscalation(escalationId: string | null) {
  const [escalation, setEscalation] = useState<Escalation | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchEscalation = useCallback(async () => {
    if (!escalationId) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const data = await apiFetch<Escalation>(
        `/api/v1/escalations/${escalationId}`
      );

      setEscalation(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch escalation');
    } finally {
      setLoading(false);
    }
  }, [escalationId]);

  useEffect(() => {
    fetchEscalation();
  }, [fetchEscalation]);

  return { escalation, loading, error, refetch: fetchEscalation };
}

/**
 * Hook to fetch escalation timeline
 */
export function useEscalationTimeline(escalationId: string | null) {
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchTimeline = useCallback(async () => {
    if (!escalationId) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const data = await apiFetch<TimelineEvent[]>(
        `/api/v1/escalations/${escalationId}/timeline`
      );

      setTimeline(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch timeline');
    } finally {
      setLoading(false);
    }
  }, [escalationId]);

  useEffect(() => {
    fetchTimeline();
  }, [fetchTimeline]);

  return { timeline, loading, error, refetch: fetchTimeline };
}

/**
 * Hook to fetch escalation comments
 */
export function useEscalationComments(
  escalationId: string | null,
  includeInternal: boolean = true
) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchComments = useCallback(async () => {
    if (!escalationId) {
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const data = await apiFetch<Comment[]>(
        `/api/v1/escalations/${escalationId}/comments?include_internal=${includeInternal}`
      );

      setComments(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch comments');
    } finally {
      setLoading(false);
    }
  }, [escalationId, includeInternal]);

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  return { comments, loading, error, refetch: fetchComments };
}

/**
 * Hook for escalation mutations (create, update, delete, etc.)
 */
export function useEscalationMutations() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const createEscalation = async (
    request: CreateEscalationRequest
  ): Promise<Escalation> => {
    try {
      setLoading(true);
      setError(null);

      const data = await apiFetch<Escalation>(
        '/api/v1/escalations',
        {
          method: 'POST',
          body: JSON.stringify(request),
        }
      );

      return data;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to create escalation';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const updateEscalation = async (
    escalationId: string,
    request: UpdateEscalationRequest,
    actorType: string,
    actorId: string
  ): Promise<Escalation> => {
    try {
      setLoading(true);
      setError(null);

      const data = await apiFetch<Escalation>(
        `/api/v1/escalations/${escalationId}?actor_type=${actorType}&actor_id=${actorId}`,
        {
          method: 'PATCH',
          body: JSON.stringify(request),
        }
      );

      return data;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to update escalation';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const resolveEscalation = async (
    escalationId: string,
    request: ResolveEscalationRequest
  ): Promise<Escalation> => {
    try {
      setLoading(true);
      setError(null);

      const data = await apiFetch<Escalation>(
        `/api/v1/escalations/${escalationId}/resolve`,
        {
          method: 'POST',
          body: JSON.stringify(request),
        }
      );

      return data;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to resolve escalation';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const escalateToNextLevel = async (
    escalationId: string,
    request: EscalateRequest
  ): Promise<Escalation> => {
    try {
      setLoading(true);
      setError(null);

      const data = await apiFetch<Escalation>(
        `/api/v1/escalations/${escalationId}/escalate`,
        {
          method: 'POST',
          body: JSON.stringify(request),
        }
      );

      return data;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to escalate';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const reassignEscalation = async (
    escalationId: string,
    request: ReassignRequest
  ): Promise<Escalation> => {
    try {
      setLoading(true);
      setError(null);

      const data = await apiFetch<Escalation>(
        `/api/v1/escalations/${escalationId}/reassign`,
        {
          method: 'POST',
          body: JSON.stringify(request),
        }
      );

      return data;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to reassign';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const addComment = async (
    escalationId: string,
    request: AddCommentRequest
  ): Promise<Comment> => {
    try {
      setLoading(true);
      setError(null);

      const data = await apiFetch<Comment>(
        `/api/v1/escalations/${escalationId}/comments`,
        {
          method: 'POST',
          body: JSON.stringify(request),
        }
      );

      return data;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to add comment';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  const deleteEscalation = async (
    escalationId: string,
    actorType: string,
    actorId: string
  ): Promise<void> => {
    try {
      setLoading(true);
      setError(null);

      await apiFetch<void>(
        `/api/v1/escalations/${escalationId}?actor_type=${actorType}&actor_id=${actorId}`,
        {
          method: 'DELETE',
        }
      );
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to delete escalation';
      setError(errorMsg);
      throw new Error(errorMsg);
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    error,
    createEscalation,
    updateEscalation,
    resolveEscalation,
    escalateToNextLevel,
    reassignEscalation,
    addComment,
    deleteEscalation,
  };
}

/**
 * Hook for real-time escalation updates via polling
 * (WebSocket implementation would be preferred in production)
 */
export function useEscalationUpdates(
  escalationId: string | null,
  pollInterval: number = 5000
) {
  const { escalation, refetch } = useEscalation(escalationId);

  useEffect(() => {
    if (!escalationId) return;

    const interval = setInterval(() => {
      refetch();
    }, pollInterval);

    return () => clearInterval(interval);
  }, [escalationId, pollInterval, refetch]);

  return { escalation };
}
