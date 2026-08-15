/**
 * Multi-Agent Chat Hooks
 *
 * React hooks for managing multi-agent conversations:
 * - Agent suggestions
 * - Agent invitations
 * - Participant management
 * - Presence tracking
 */

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { useState, useCallback } from 'react';

// Types
export interface AgentSuggestion {
  agent_id: string;
  agent_name: string;
  agent_role: string;
  relevance_score: number;
  expertise_match: string[];
  reasoning: string;
  prediction_factors: {
    expertise_match: number;
    historical_success: number;
    user_preference: number;
    context_fit: number;
    gap_filling?: number;
  };
  confidence: number;
}

export interface AgentParticipant {
  participant_id: string;
  agent_id: string;
  agent_name: string;
  agent_role: string;
  joined_at: string;
  presence: {
    status: 'active' | 'idle' | 'thinking' | 'typing' | 'away';
    activity: string | null;
    last_active: string;
  } | null;
}

export interface AgentInvitation {
  invitation_id: string;
  agent_id: string;
  status: 'pending' | 'accepted' | 'declined' | 'expired';
  invited_by_id: string;
  invitation_reason: string | null;
  specific_question: string | null;
  auto_accept: boolean;
  created_at: string;
  briefing?: any;
}

export interface InviteAgentRequest {
  agent_id: string;
  invited_by_type: 'user' | 'agent' | 'system';
  invited_by_id: string;
  invited_by_name?: string;
  reason?: string;
  specific_question?: string;
  urgency?: 'low' | 'normal' | 'high' | 'urgent';
}

// API functions
const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

async function fetchAgentSuggestions(
  conversationId: string,
  userId: string,
  limit: number = 5,
  minRelevance: number = 0.6
): Promise<AgentSuggestion[]> {
  const url = `${API_BASE}/api/v1/conversations/${conversationId}/suggested-agents?user_id=${userId}&limit=${limit}&min_relevance=${minRelevance}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch agent suggestions');
  }
  return response.json();
}

async function inviteAgent(
  conversationId: string,
  request: InviteAgentRequest
): Promise<AgentInvitation> {
  const url = `${API_BASE}/api/v1/conversations/${conversationId}/invite-agent`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(request),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to invite agent');
  }
  return response.json();
}

async function fetchParticipants(
  conversationId: string
): Promise<AgentParticipant[]> {
  const url = `${API_BASE}/api/v1/conversations/${conversationId}/participants`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch participants');
  }
  return response.json();
}

async function updatePresence(
  conversationId: string,
  agentId: string,
  status: string,
  activity?: string
): Promise<any> {
  const url = `${API_BASE}/api/v1/conversations/${conversationId}/presence`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_id: agentId, status, activity }),
  });
  if (!response.ok) {
    throw new Error('Failed to update presence');
  }
  return response.json();
}

async function fetchInvitations(
  conversationId: string,
  status?: string
): Promise<AgentInvitation[]> {
  let url = `${API_BASE}/api/v1/conversations/${conversationId}/invitations`;
  if (status) {
    url += `?status=${status}`;
  }
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch invitations');
  }
  return response.json();
}

async function acceptInvitation(invitationId: string): Promise<any> {
  const url = `${API_BASE}/api/v1/invitations/${invitationId}/accept`;
  const response = await fetch(url, { method: 'POST' });
  if (!response.ok) {
    throw new Error('Failed to accept invitation');
  }
  return response.json();
}

async function declineInvitation(
  invitationId: string,
  reason?: string
): Promise<any> {
  const url = `${API_BASE}/api/v1/invitations/${invitationId}/decline`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ reason }),
  });
  if (!response.ok) {
    throw new Error('Failed to decline invitation');
  }
  return response.json();
}

async function agentLeave(
  conversationId: string,
  agentId: string,
  reason?: string
): Promise<any> {
  const url = `${API_BASE}/api/v1/conversations/${conversationId}/leave`;
  const response = await fetch(url, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ agent_id: agentId, reason }),
  });
  if (!response.ok) {
    throw new Error('Failed to leave conversation');
  }
  return response.json();
}

// Hooks

/**
 * Get AI-suggested agents for a conversation
 */
export function useAgentSuggestions(
  conversationId: string,
  userId: string,
  options?: {
    limit?: number;
    minRelevance?: number;
    enabled?: boolean;
  }
) {
  return useQuery({
    queryKey: ['agent-suggestions', conversationId, userId, options?.limit, options?.minRelevance],
    queryFn: () =>
      fetchAgentSuggestions(
        conversationId,
        userId,
        options?.limit || 10,
        options?.minRelevance || 0.4
      ),
    enabled: options?.enabled !== false,
    staleTime: 2 * 60 * 1000, // 2 minutes
    refetchOnWindowFocus: false,
  });
}

/**
 * Invite an agent to a conversation
 */
export function useInviteAgent(conversationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (request: InviteAgentRequest) =>
      inviteAgent(conversationId, request),
    onSuccess: () => {
      // Invalidate queries to refresh data
      queryClient.invalidateQueries({ queryKey: ['participants', conversationId] });
      queryClient.invalidateQueries({ queryKey: ['invitations', conversationId] });
      queryClient.invalidateQueries({ queryKey: ['agent-suggestions', conversationId] });
    },
  });
}

/**
 * Get all participants in a conversation with presence
 */
export function useConversationParticipants(
  conversationId: string,
  options?: {
    enabled?: boolean;
    refetchInterval?: number;
  }
) {
  return useQuery({
    queryKey: ['participants', conversationId],
    queryFn: () => fetchParticipants(conversationId),
    enabled: options?.enabled !== false,
    staleTime: 10 * 1000, // 10 seconds
    refetchInterval: options?.refetchInterval || 30000, // Refetch every 30s for presence updates
  });
}

/**
 * Update agent presence in a conversation
 */
export function useUpdatePresence(conversationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ agentId, status, activity }: {
      agentId: string;
      status: string;
      activity?: string;
    }) => updatePresence(conversationId, agentId, status, activity),
    onSuccess: () => {
      // Invalidate participants to show updated presence
      queryClient.invalidateQueries({ queryKey: ['participants', conversationId] });
    },
  });
}

/**
 * Get invitation history for a conversation
 */
export function useInvitations(
  conversationId: string,
  options?: {
    status?: string;
    enabled?: boolean;
  }
) {
  return useQuery({
    queryKey: ['invitations', conversationId, options?.status],
    queryFn: () => fetchInvitations(conversationId, options?.status),
    enabled: options?.enabled !== false,
    staleTime: 30 * 1000, // 30 seconds
  });
}

/**
 * Accept an agent invitation
 */
export function useAcceptInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (invitationId: string) => acceptInvitation(invitationId),
    onSuccess: (_, invitationId) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ['invitations'] });
      queryClient.invalidateQueries({ queryKey: ['participants'] });
    },
  });
}

/**
 * Decline an agent invitation
 */
export function useDeclineInvitation() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ invitationId, reason }: {
      invitationId: string;
      reason?: string;
    }) => declineInvitation(invitationId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['invitations'] });
    },
  });
}

/**
 * Agent leaves a conversation
 */
export function useAgentLeave(conversationId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ agentId, reason }: {
      agentId: string;
      reason?: string;
    }) => agentLeave(conversationId, agentId, reason),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['participants', conversationId] });
    },
  });
}

/**
 * Combined hook for multi-agent chat management
 */
export function useMultiAgentChat(conversationId: string, userId: string) {
  const [showSuggestions, setShowSuggestions] = useState(false); // Start hidden, show on invite click
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);

  const suggestions = useAgentSuggestions(conversationId, userId, {
    enabled: !!conversationId && showSuggestions, // Only fetch when panel is shown
  });

  const participants = useConversationParticipants(conversationId, {
    enabled: !!conversationId,
  });

  const invitations = useInvitations(conversationId, {
    status: 'pending',
    enabled: !!conversationId,
  });

  const inviteMutation = useInviteAgent(conversationId);

  const handleInviteAgent = useCallback(
    async (agentId: string, reason?: string, specificQuestion?: string) => {
      try {
        await inviteMutation.mutateAsync({
          agent_id: agentId,
          invited_by_type: 'user',
          invited_by_id: userId,
          reason,
          specific_question: specificQuestion,
        });
        setShowSuggestions(false); // Hide suggestions after inviting
      } catch (error) {
        console.error('Failed to invite agent:', error);
        throw error;
      }
    },
    [inviteMutation, userId]
  );

  const dismissSuggestion = useCallback((agentId: string) => {
    // Could track dismissed suggestions
    console.log('Dismissed suggestion:', agentId);
  }, []);

  // When showing suggestions, trigger a refetch to ensure fresh data
  const handleShowSuggestions = useCallback((show: boolean) => {
    setShowSuggestions(show);
    if (show) {
      // Refetch suggestions when panel is opened
      suggestions.refetch();
    }
  }, [suggestions]);

  return {
    suggestions: suggestions.data || [],
    suggestionsLoading: suggestions.isLoading || suggestions.isFetching,
    suggestionsError: suggestions.error,
    participants: participants.data || [],
    participantsLoading: participants.isLoading,
    pendingInvitations: invitations.data || [],
    inviteAgent: handleInviteAgent,
    dismissSuggestion,
    showSuggestions,
    setShowSuggestions: handleShowSuggestions,
    refetchSuggestions: suggestions.refetch,
    selectedAgent,
    setSelectedAgent,
    isInviting: inviteMutation.isPending,
  };
}
