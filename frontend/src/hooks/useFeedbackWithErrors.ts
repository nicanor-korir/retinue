import { useState, useCallback } from 'react';
import axios from 'axios';
import { useErrorHandler } from './useErrorHandler';
import { useToast } from '@/components/error/error-toast';

/**
 * Enhanced feedback hook with error handling
 * Provides the same feedback functionality but with proper error management
 */

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

export interface FeedbackError {
  message: string;
  code?: string;
  field?: string;
  requestId?: string;
}

// Project Feedback Hook with Error Handling
export function useProjectFeedbackWithErrors(projectId: string | undefined) {
  const [feedback, setFeedback] = useState<ProjectFeedback[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<FeedbackError | null>(null);
  const { formatError, isNotFoundError, isValidationError } = useErrorHandler();
  const { error: showErrorToast } = useToast();

  const fetchFeedback = useCallback(async () => {
    if (!projectId) return;

    try {
      setIsLoading(true);
      setError(null);

      const response = await axios.get(`/api/v1/projects/${projectId}/feedback`);
      setFeedback(response.data.feedback || []);
    } catch (err) {
      // Format error properly
      const formatted = formatError(err);

      // Check specific error types
      if (isNotFoundError(err)) {
        setError({
          message: 'Project not found. Please check the project ID.',
          code: 'NOT_FOUND',
          requestId: formatted.requestId,
        });
      } else {
        setError({
          message: formatted.userMessage,
          code: formatted.code,
          requestId: formatted.requestId,
        });
      }

      // Show toast notification
      showErrorToast(err);
    } finally {
      setIsLoading(false);
    }
  }, [projectId, formatError, isNotFoundError, showErrorToast]);

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
      if (!projectId) {
        setError({
          message: 'Project ID is required',
          code: 'VALIDATION_ERROR',
        });
        throw new Error('Project ID is required');
      }

      try {
        setError(null);

        const response = await axios.post(`/api/v1/projects/${projectId}/feedback`, data);

        // Refresh feedback list
        await fetchFeedback();

        return response.data;
      } catch (err) {
        const formatted = formatError(err);

        // Handle validation errors (field-specific)
        if (isValidationError(err)) {
          setError({
            message: formatted.message,
            code: 'VALIDATION_ERROR',
            field: formatted.field,
            requestId: formatted.requestId,
          });
        } else {
          setError({
            message: formatted.userMessage,
            code: formatted.code,
            requestId: formatted.requestId,
          });
        }

        // Show toast notification
        showErrorToast(err);

        throw err;
      }
    },
    [projectId, fetchFeedback, formatError, isValidationError, showErrorToast]
  );

  return {
    feedback,
    isLoading,
    error,
    fetchFeedback,
    createFeedback,
    clearError: () => setError(null),
  };
}

// Task Feedback Hook with Error Handling
export function useTaskFeedbackWithErrors(taskId: string | undefined, projectId: string | undefined) {
  const [feedback, setFeedback] = useState<ProjectFeedback[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<FeedbackError | null>(null);
  const { formatError, isNotFoundError, isValidationError } = useErrorHandler();
  const { error: showErrorToast } = useToast();

  const fetchFeedback = useCallback(async () => {
    if (!taskId) return;

    try {
      setIsLoading(true);
      setError(null);

      const response = await axios.get(`/api/v1/tasks/${taskId}/feedback`);
      setFeedback(response.data.feedback || []);
    } catch (err) {
      const formatted = formatError(err);

      if (isNotFoundError(err)) {
        setError({
          message: 'Task not found. Please check the task ID.',
          code: 'NOT_FOUND',
          requestId: formatted.requestId,
        });
      } else {
        setError({
          message: formatted.userMessage,
          code: formatted.code,
          requestId: formatted.requestId,
        });
      }

      showErrorToast(err);
    } finally {
      setIsLoading(false);
    }
  }, [taskId, formatError, isNotFoundError, showErrorToast]);

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
      if (!taskId || !projectId) {
        setError({
          message: 'Task ID and Project ID are required',
          code: 'VALIDATION_ERROR',
        });
        throw new Error('Task ID and Project ID are required');
      }

      try {
        setError(null);

        const response = await axios.post(`/api/v1/tasks/${taskId}/feedback?project_id=${projectId}`, data);

        // Refresh feedback list
        await fetchFeedback();

        return response.data;
      } catch (err) {
        const formatted = formatError(err);

        if (isValidationError(err)) {
          setError({
            message: formatted.message,
            code: 'VALIDATION_ERROR',
            field: formatted.field,
            requestId: formatted.requestId,
          });
        } else {
          setError({
            message: formatted.userMessage,
            code: formatted.code,
            requestId: formatted.requestId,
          });
        }

        showErrorToast(err);
        throw err;
      }
    },
    [taskId, projectId, fetchFeedback, formatError, isValidationError, showErrorToast]
  );

  return {
    feedback,
    isLoading,
    error,
    fetchFeedback,
    createFeedback,
    clearError: () => setError(null),
  };
}

// Agent Feedback Hook with Error Handling
export function useAgentFeedbackWithErrors(agentId: string | undefined) {
  const [feedback, setFeedback] = useState<ProjectFeedback[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<FeedbackError | null>(null);
  const { formatError, isNotFoundError, isValidationError } = useErrorHandler();
  const { error: showErrorToast } = useToast();

  const fetchFeedback = useCallback(async () => {
    if (!agentId) return;

    try {
      setIsLoading(true);
      setError(null);

      const response = await axios.get(`/api/v1/agents/${agentId}/feedback`);
      setFeedback(response.data.feedback || []);
    } catch (err) {
      const formatted = formatError(err);

      if (isNotFoundError(err)) {
        setError({
          message: 'Agent not found. Please check the agent ID.',
          code: 'NOT_FOUND',
          requestId: formatted.requestId,
        });
      } else {
        setError({
          message: formatted.userMessage,
          code: formatted.code,
          requestId: formatted.requestId,
        });
      }

      showErrorToast(err);
    } finally {
      setIsLoading(false);
    }
  }, [agentId, formatError, isNotFoundError, showErrorToast]);

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
      if (!agentId) {
        setError({
          message: 'Agent ID is required',
          code: 'VALIDATION_ERROR',
        });
        throw new Error('Agent ID is required');
      }

      try {
        setError(null);

        const response = await axios.post(`/api/v1/agents/${agentId}/feedback`, data);

        // Refresh feedback list
        await fetchFeedback();

        return response.data;
      } catch (err) {
        const formatted = formatError(err);

        if (isValidationError(err)) {
          setError({
            message: formatted.message,
            code: 'VALIDATION_ERROR',
            field: formatted.field,
            requestId: formatted.requestId,
          });
        } else {
          setError({
            message: formatted.userMessage,
            code: formatted.code,
            requestId: formatted.requestId,
          });
        }

        showErrorToast(err);
        throw err;
      }
    },
    [agentId, fetchFeedback, formatError, isValidationError, showErrorToast]
  );

  return {
    feedback,
    isLoading,
    error,
    fetchFeedback,
    createFeedback,
    clearError: () => setError(null),
  };
}
