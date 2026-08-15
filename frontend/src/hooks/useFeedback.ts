import { useState, useCallback } from 'react';
import axios from 'axios';

// Types
export interface ProjectFeedback {
  feedback_id: string;
  title: string;
  description: string;
  type: string;
  status: string;
  priority: string;
  quality_rating?: number;
  satisfaction_rating?: number;
  confidence_level?: number;
  created_at: string;
}

export interface TaskFeedback {
  feedback_id: string;
  title: string;
  description: string;
  type: string;
  status: string;
  priority: string;
  output_quality?: number;
  correctness?: number;
  completeness?: number;
  implementation_quality?: number;
  code_review_feedback?: string;
  created_at: string;
}

export interface AgentFeedback {
  feedback_id: string;
  title: string;
  description: string;
  type: string;
  status: string;
  priority: string;
  decision_quality?: number;
  execution_quality?: number;
  communication_clarity?: number;
  created_at: string;
}

export interface FeedbackResponse {
  feedback_id: string;
  status: string;
  priority: string;
  created_at: string;
  title: string;
  description: string;
}

export interface FeedbackListResponse {
  count: number;
  feedback: ProjectFeedback[] | TaskFeedback[] | AgentFeedback[];
}

// Project Feedback Hook
export function useProjectFeedback(projectId: string | undefined) {
  const [feedback, setFeedback] = useState<ProjectFeedback[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFeedback = useCallback(async () => {
    if (!projectId) return;

    try {
      setIsLoading(true);
      setError(null);

      const response = await axios.get<FeedbackListResponse>(
        `/api/v1/projects/${projectId}/feedback`
      );

      setFeedback((response.data.feedback || []) as ProjectFeedback[]);
    } catch (err) {
      const message =
        axios.isAxiosError(err) && err.response?.data?.detail
          ? err.response.data.detail
          : 'Failed to load feedback';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [projectId]);

  const createFeedback = useCallback(
    async (data: {
      feedback_type: string;
      title: string;
      description: string;
      quality_rating?: number;
      satisfaction_rating?: number;
      confidence_level?: number;
      suggested_actions?: string[];
      priority?: string;
      context?: Record<string, unknown>;
    }) => {
      if (!projectId) throw new Error('Project ID is required');

      try {
        const response = await axios.post<FeedbackResponse>(
          `/api/v1/projects/${projectId}/feedback`,
          data
        );

        // Refresh feedback list
        await fetchFeedback();

        return response.data;
      } catch (err) {
        const message =
          axios.isAxiosError(err) && err.response?.data?.detail
            ? err.response.data.detail
            : 'Failed to create feedback';
        throw new Error(message);
      }
    },
    [projectId, fetchFeedback]
  );

  return {
    feedback,
    isLoading,
    error,
    fetchFeedback,
    createFeedback,
  };
}

// Task Feedback Hook
export function useTaskFeedback(taskId: string | undefined, projectId: string | undefined) {
  const [feedback, setFeedback] = useState<TaskFeedback[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFeedback = useCallback(async () => {
    if (!taskId) return;

    try {
      setIsLoading(true);
      setError(null);

      const response = await axios.get<FeedbackListResponse>(
        `/api/v1/tasks/${taskId}/feedback`
      );

      setFeedback((response.data.feedback || []) as TaskFeedback[]);
    } catch (err) {
      const message =
        axios.isAxiosError(err) && err.response?.data?.detail
          ? err.response.data.detail
          : 'Failed to load feedback';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [taskId]);

  const createFeedback = useCallback(
    async (data: {
      feedback_type: string;
      title: string;
      description: string;
      output_quality?: number;
      correctness?: number;
      completeness?: number;
      implementation_quality?: number;
      code_review_feedback?: string;
      suggested_improvements?: string[];
      action_items?: string[];
      priority?: string;
      context?: Record<string, unknown>;
    }) => {
      if (!taskId || !projectId) throw new Error('Task ID and Project ID are required');

      try {
        const response = await axios.post<FeedbackResponse>(
          `/api/v1/tasks/${taskId}/feedback?project_id=${projectId}`,
          data
        );

        // Refresh feedback list
        await fetchFeedback();

        return response.data;
      } catch (err) {
        const message =
          axios.isAxiosError(err) && err.response?.data?.detail
            ? err.response.data.detail
            : 'Failed to create feedback';
        throw new Error(message);
      }
    },
    [taskId, projectId, fetchFeedback]
  );

  return {
    feedback,
    isLoading,
    error,
    fetchFeedback,
    createFeedback,
  };
}

// Agent Feedback Hook
export function useAgentFeedback(agentId: string | undefined) {
  const [feedback, setFeedback] = useState<AgentFeedback[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchFeedback = useCallback(async () => {
    if (!agentId) return;

    try {
      setIsLoading(true);
      setError(null);

      const response = await axios.get<FeedbackListResponse>(
        `/api/v1/agents/${agentId}/feedback`
      );

      setFeedback((response.data.feedback || []) as AgentFeedback[]);
    } catch (err) {
      const message =
        axios.isAxiosError(err) && err.response?.data?.detail
          ? err.response.data.detail
          : 'Failed to load feedback';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [agentId]);

  const createFeedback = useCallback(
    async (data: {
      feedback_type: string;
      title: string;
      description: string;
      decision_quality?: number;
      execution_quality?: number;
      communication_clarity?: number;
      problem_solving?: number;
      efficiency?: number;
      behavior_observations?: string;
      recommended_improvements?: string[];
      strengths_noted?: string[];
      suggested_system_prompt_updates?: string;
      priority?: string;
      related_task_id?: string;
      related_project_id?: string;
      context?: Record<string, unknown>;
    }) => {
      if (!agentId) throw new Error('Agent ID is required');

      try {
        const response = await axios.post<FeedbackResponse>(
          `/api/v1/agents/${agentId}/feedback`,
          data
        );

        // Refresh feedback list
        await fetchFeedback();

        return response.data;
      } catch (err) {
        const message =
          axios.isAxiosError(err) && err.response?.data?.detail
            ? err.response.data.detail
            : 'Failed to create feedback';
        throw new Error(message);
      }
    },
    [agentId, fetchFeedback]
  );

  return {
    feedback,
    isLoading,
    error,
    fetchFeedback,
    createFeedback,
  };
}

// Generic Feedback Status Update Hook
export function useFeedbackStatusUpdate() {
  const [isUpdating, setIsUpdating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const updateStatus = useCallback(
    async (
      feedbackId: string,
      status: string,
      implementationNotes?: string
    ): Promise<boolean> => {
      try {
        setIsUpdating(true);
        setError(null);

        await axios.patch(`/api/v1/feedback/${feedbackId}/status`, {
          status,
          implementation_notes: implementationNotes,
        });

        return true;
      } catch (err) {
        const message =
          axios.isAxiosError(err) && err.response?.data?.detail
            ? err.response.data.detail
            : 'Failed to update feedback status';
        setError(message);
        return false;
      } finally {
        setIsUpdating(false);
      }
    },
    []
  );

  return {
    isUpdating,
    error,
    updateStatus,
  };
}

// Context Updates Hook
export interface ContextUpdate {
  context_id: string;
  title: string;
  content: string;
  tags: string[];
  source: string;
  implementation_status: string;
  created_at: string;
}

export interface ContextListResponse {
  count: number;
  contexts: ContextUpdate[];
}

export function useContextUpdates(
  entityType: 'project' | 'task' | 'agent' | undefined,
  entityId: string | undefined
) {
  const [contexts, setContexts] = useState<ContextUpdate[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchContexts = useCallback(async () => {
    if (!entityType || !entityId) return;

    try {
      setIsLoading(true);
      setError(null);

      const response = await axios.get<ContextListResponse>(
        `/api/v1/${entityType}/${entityId}/context`
      );

      setContexts(response.data.contexts || []);
    } catch (err) {
      const message =
        axios.isAxiosError(err) && err.response?.data?.detail
          ? err.response.data.detail
          : 'Failed to load context updates';
      setError(message);
    } finally {
      setIsLoading(false);
    }
  }, [entityType, entityId]);

  return {
    contexts,
    isLoading,
    error,
    fetchContexts,
  };
}
