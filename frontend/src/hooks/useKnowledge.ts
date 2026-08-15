/**
 * Knowledge System Hooks
 *
 * Custom React hooks for interacting with the intelligent knowledge base.
 * Includes caching, debouncing, and optimistic updates for performance.
 */

import { useState, useCallback, useEffect, useMemo } from 'react';
import { useQuery, useMutation, useQueryClient, UseQueryOptions } from '@tanstack/react-query';
import { debounce } from 'lodash';

// ===== TYPES =====

export interface KnowledgeEntry {
  entry_id: string;
  title: string;
  summary: string | null;
  content_excerpt: string;
  entry_type: string;
  domain: string | null;
  tags: string[];
  validation_status: string;
  quality_score: number;
  relevance_score?: number;
  use_count: number;
  helpfulness_ratio: number;
  created_at: string | null;
  last_accessed_at: string | null;
}

export interface KnowledgeSearchRequest {
  query: string;
  user_id?: string;
  agent_id?: string;
  filters?: Record<string, any>;
  top_k?: number;
  include_relations?: boolean;
}

export interface ExtractionCandidate {
  candidate_id: string;
  extraction_type: string;
  title: string;
  summary: string;
  confidence_score: number;
  novelty_score: number;
  relevance_score: number;
  extraction_quality: number;
  trigger_type: string;
  status: string;
  created_at: string;
}

export interface KnowledgeCategory {
  category_id: string;
  name: string;
  slug: string;
  description: string | null;
  parent_category_id: string | null;
  level: number;
  entry_count: number;
  icon: string | null;
  color: string | null;
}

export interface AgentPrediction {
  agent_id: string;
  agent_name: string;
  agent_role: string;
  involvement_probability: number;
  confidence: number;
  predicted_contribution_type: string;
  suggested_timing: string;
  introduction_approach: string;
  trigger_reasons: string[];
  signal_strength: number;
}

// ===== API CLIENT =====

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class KnowledgeAPI {
  private async request<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const response = await fetch(`${API_BASE}${endpoint}`, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || `API error: ${response.status}`);
    }

    return response.json();
  }

  async search(request: KnowledgeSearchRequest): Promise<KnowledgeEntry[]> {
    return this.request('/api/v1/knowledge/search', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async getEntry(entryId: string, userId?: string, agentId?: string): Promise<any> {
    const params = new URLSearchParams();
    if (userId) params.append('user_id', userId);
    if (agentId) params.append('agent_id', agentId);

    return this.request(`/api/v1/knowledge/entries/${entryId}?${params}`);
  }

  async createEntry(entry: any, createdById: string): Promise<any> {
    return this.request(`/api/v1/knowledge/entries?created_by_id=${createdById}`, {
      method: 'POST',
      body: JSON.stringify(entry),
    });
  }

  async getPendingExtractions(limit = 20, minQuality = 0.5): Promise<ExtractionCandidate[]> {
    return this.request(
      `/api/v1/knowledge/extractions/pending?limit=${limit}&min_quality=${minQuality}`
    );
  }

  async reviewExtraction(
    candidateId: string,
    reviewerId: string,
    decision: 'approve' | 'reject' | 'modify',
    reviewNotes?: string,
    modifications?: any
  ): Promise<any> {
    return this.request(
      `/api/v1/knowledge/extractions/${candidateId}/review?reviewer_id=${reviewerId}`,
      {
        method: 'POST',
        body: JSON.stringify({ decision, review_notes: reviewNotes, modifications }),
      }
    );
  }

  async submitFeedback(feedback: {
    entry_id: string;
    feedback_type: string;
    rating?: number;
    comment?: string;
    user_id?: string;
    agent_id?: string;
  }): Promise<any> {
    return this.request('/api/v1/knowledge/feedback', {
      method: 'POST',
      body: JSON.stringify(feedback),
    });
  }

  async getCategories(): Promise<KnowledgeCategory[]> {
    return this.request('/api/v1/knowledge/categories');
  }

  async predictAgents(request: {
    conversation_id?: string;
    project_id?: string;
    message_ids: string[];
    current_agent_ids?: string[];
    user_id?: string;
  }): Promise<AgentPrediction[]> {
    const params = new URLSearchParams();
    request.message_ids.forEach(id => params.append('message_ids', id));
    if (request.current_agent_ids) {
      request.current_agent_ids.forEach(id => params.append('current_agent_ids', id));
    }
    if (request.conversation_id) params.append('conversation_id', request.conversation_id);
    if (request.project_id) params.append('project_id', request.project_id);
    if (request.user_id) params.append('user_id', request.user_id);

    return this.request(`/api/v1/knowledge/predict-agents?${params}`, {
      method: 'POST',
    });
  }

  async getUsageAnalytics(startDate?: string, endDate?: string, limit = 100): Promise<any> {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);

    return this.request(`/api/v1/knowledge/analytics/usage?${params}`);
  }

  async getTopEntries(metric: 'quality' | 'uses' | 'helpfulness' | 'views' = 'quality', limit = 10): Promise<any> {
    return this.request(`/api/v1/knowledge/analytics/top-entries?metric=${metric}&limit=${limit}`);
  }
}

const knowledgeAPI = new KnowledgeAPI();

// ===== HOOKS =====

/**
 * Hook for searching knowledge with debouncing and caching
 */
export function useKnowledgeSearch(
  initialQuery: string = '',
  options?: {
    userId?: string;
    agentId?: string;
    filters?: Record<string, any>;
    topK?: number;
    includeRelations?: boolean;
    debounceMs?: number;
    enabled?: boolean;
  }
) {
  const [query, setQuery] = useState(initialQuery);
  const [debouncedQuery, setDebouncedQuery] = useState(initialQuery);

  // Debounce query updates
  const debouncedSetQuery = useMemo(
    () =>
      debounce((value: string) => {
        setDebouncedQuery(value);
      }, options?.debounceMs || 300),
    [options?.debounceMs]
  );

  useEffect(() => {
    debouncedSetQuery(query);
    return () => debouncedSetQuery.cancel();
  }, [query, debouncedSetQuery]);

  const searchQuery = useQuery({
    queryKey: ['knowledge-search', debouncedQuery, options?.filters, options?.topK],
    queryFn: () =>
      knowledgeAPI.search({
        query: debouncedQuery,
        user_id: options?.userId,
        agent_id: options?.agentId,
        filters: options?.filters,
        top_k: options?.topK || 10,
        include_relations: options?.includeRelations,
      }),
    enabled: (options?.enabled !== false) && debouncedQuery.length >= 2,
    staleTime: 5 * 60 * 1000, // 5 minutes
    gcTime: 10 * 60 * 1000, // 10 minutes
  });

  return {
    query,
    setQuery,
    results: searchQuery.data || [],
    isLoading: searchQuery.isLoading,
    isError: searchQuery.isError,
    error: searchQuery.error,
    refetch: searchQuery.refetch,
  };
}

/**
 * Hook for fetching a single knowledge entry
 */
export function useKnowledgeEntry(
  entryId: string | null,
  options?: { userId?: string; agentId?: string; enabled?: boolean }
) {
  return useQuery({
    queryKey: ['knowledge-entry', entryId],
    queryFn: () => knowledgeAPI.getEntry(entryId!, options?.userId, options?.agentId),
    enabled: (options?.enabled !== false) && !!entryId,
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook for creating knowledge entries with optimistic updates
 */
export function useCreateKnowledgeEntry() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ entry, createdById }: { entry: any; createdById: string }) =>
      knowledgeAPI.createEntry(entry, createdById),
    onSuccess: () => {
      // Invalidate relevant queries
      queryClient.invalidateQueries({ queryKey: ['knowledge-search'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-categories'] });
    },
  });
}

/**
 * Hook for fetching pending extraction candidates
 */
export function useExtractionCandidates(
  options?: { limit?: number; minQuality?: number; enabled?: boolean }
) {
  return useQuery({
    queryKey: ['extraction-candidates', options?.limit, options?.minQuality],
    queryFn: () => knowledgeAPI.getPendingExtractions(options?.limit, options?.minQuality),
    enabled: options?.enabled !== false,
    refetchInterval: 30000, // Refetch every 30 seconds
  });
}

/**
 * Hook for reviewing extraction candidates
 */
export function useReviewExtraction() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({
      candidateId,
      reviewerId,
      decision,
      reviewNotes,
      modifications,
    }: {
      candidateId: string;
      reviewerId: string;
      decision: 'approve' | 'reject' | 'modify';
      reviewNotes?: string;
      modifications?: any;
    }) => knowledgeAPI.reviewExtraction(candidateId, reviewerId, decision, reviewNotes, modifications),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['extraction-candidates'] });
      queryClient.invalidateQueries({ queryKey: ['knowledge-search'] });
    },
  });
}

/**
 * Hook for submitting knowledge feedback
 */
export function useKnowledgeFeedback() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (feedback: {
      entry_id: string;
      feedback_type: string;
      rating?: number;
      comment?: string;
      user_id?: string;
      agent_id?: string;
    }) => knowledgeAPI.submitFeedback(feedback),
    onSuccess: (_, variables) => {
      // Invalidate entry to refresh helpfulness counters
      queryClient.invalidateQueries({ queryKey: ['knowledge-entry', variables.entry_id] });
    },
  });
}

/**
 * Hook for fetching knowledge categories
 */
export function useKnowledgeCategories() {
  return useQuery({
    queryKey: ['knowledge-categories'],
    queryFn: () => knowledgeAPI.getCategories(),
    staleTime: 30 * 60 * 1000, // 30 minutes
  });
}

/**
 * Hook for agent involvement predictions
 */
export function useAgentPredictions(
  request: {
    conversation_id?: string;
    project_id?: string;
    message_ids: string[];
    current_agent_ids?: string[];
    user_id?: string;
  },
  options?: { enabled?: boolean }
) {
  return useQuery({
    queryKey: ['agent-predictions', request],
    queryFn: () => knowledgeAPI.predictAgents(request),
    enabled: (options?.enabled !== false) && request.message_ids.length > 0,
    staleTime: 2 * 60 * 1000, // 2 minutes
  });
}

/**
 * Hook for knowledge usage analytics
 */
export function useKnowledgeAnalytics(
  options?: { startDate?: string; endDate?: string; limit?: number; enabled?: boolean }
) {
  return useQuery({
    queryKey: ['knowledge-analytics', options?.startDate, options?.endDate, options?.limit],
    queryFn: () => knowledgeAPI.getUsageAnalytics(options?.startDate, options?.endDate, options?.limit),
    enabled: options?.enabled !== false,
    refetchInterval: 60000, // Refetch every minute
  });
}

/**
 * Hook for top knowledge entries
 */
export function useTopKnowledgeEntries(
  metric: 'quality' | 'uses' | 'helpfulness' | 'views' = 'quality',
  limit = 10
) {
  return useQuery({
    queryKey: ['top-knowledge-entries', metric, limit],
    queryFn: () => knowledgeAPI.getTopEntries(metric, limit),
    staleTime: 5 * 60 * 1000,
  });
}

/**
 * Hook for real-time knowledge updates via WebSocket
 */
export function useKnowledgeUpdates(callback: (update: any) => void) {
  const queryClient = useQueryClient();

  useEffect(() => {
    // Subscribe to knowledge updates via WebSocket
    // This assumes you have a WebSocket connection
    const handleKnowledgeUpdate = (event: MessageEvent) => {
      const data = JSON.parse(event.data);

      if (data.type === 'knowledge_extracted') {
        // New knowledge extracted
        queryClient.invalidateQueries({ queryKey: ['extraction-candidates'] });
        callback(data);
      } else if (data.type === 'knowledge_approved') {
        // Knowledge approved
        queryClient.invalidateQueries({ queryKey: ['knowledge-search'] });
        callback(data);
      }
    };

    // Add event listener (adjust based on your WebSocket implementation)
    // window.addEventListener('knowledge-update', handleKnowledgeUpdate);

    return () => {
      // window.removeEventListener('knowledge-update', handleKnowledgeUpdate);
    };
  }, [callback, queryClient]);
}

export default knowledgeAPI;
