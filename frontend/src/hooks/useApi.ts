import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  healthAPI,
  projectsAPI,
  agentsAPI,
  tasksAPI,
  messagesAPI,
  escalationsAPI,
  auditAPI,
  dashboardAPI,
  notificationsAPI,
} from "@/lib/api";
import type { ProjectCreate } from "@/types/api";

// Query Keys
export const queryKeys = {
  health: ["health"] as const,
  projects: ["projects"] as const,
  project: (id: string) => ["projects", id] as const,
  agents: ["agents"] as const,
  availableAgents: ["agents", "available"] as const,
  agent: (id: string) => ["agents", id] as const,
  tasks: (filters?: any) => ["tasks", filters] as const,
  task: (id: string) => ["tasks", id] as const,
  messages: (filters?: any) => ["messages", filters] as const,
  escalations: (filters?: any) => ["escalations", filters] as const,
  auditLogs: (filters?: any) => ["auditLogs", filters] as const,
  dashboard: ["dashboard"] as const,
  notifications: (unreadOnly?: boolean) => ["notifications", unreadOnly] as const,
  notificationCount: ["notificationCount"] as const,
};

// Health
export const useHealth = () => {
  return useQuery({
    queryKey: queryKeys.health,
    queryFn: async () => {
      const { data } = await healthAPI.check();
      return data;
    },
    refetchOnWindowFocus: false, // don't change this for now
    refetchOnMount: false,
  });
};

// Projects
export const useProjects = () => {
  return useQuery({
    queryKey: queryKeys.projects,
    queryFn: async () => {
      const { data } = await projectsAPI.list();
      return data;
    },
    refetchOnWindowFocus: false, // don't change this for now
    refetchOnMount: false,
  });
};

export const useProject = (id: string) => {
  return useQuery({
    queryKey: queryKeys.project(id),
    queryFn: async () => {
      const { data } = await projectsAPI.get(id);
      return data;
    },
    enabled: !!id,
    refetchOnWindowFocus: false, // don't change this for now
    refetchOnMount: false,
  });
};

export const useCreateProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (projectData: ProjectCreate) => {
      const { data } = await projectsAPI.create(projectData);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard });
    },
  });
};

export const useRestartProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data?: ProjectCreate }) => {
      const { data: result } = await projectsAPI.restart(id, data);
      return result;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard });
    },
  });
};

// Agents
export const useAvailableAgents = () => {
  return useQuery({
    queryKey: queryKeys.availableAgents,
    queryFn: async () => {
      const { data } = await agentsAPI.list({ active_only: true });
      return data;
    },
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });
};

export const useProjectVersions = (id: string) => {
  return useQuery({
    queryKey: ["project-versions", id],
    queryFn: async () => {
      const { data } = await projectsAPI.getVersions(id);
      return data;
    },
    enabled: !!id,
  });
};

export const useProjectActivity = (id: string, limit?: number) => {
  return useQuery({
    queryKey: ["project-activity", id, limit],
    queryFn: async () => {
      const { data } = await projectsAPI.getActivity(id, limit);
      return data;
    },
    enabled: !!id,
    refetchOnWindowFocus: false,
    refetchOnMount: true,
  });
};

export const useDeleteProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await projectsAPI.delete(id);
      return data;
    },
    onSuccess: (_, deletedId) => {
      // Immediately invalidate and refetch all project-related queries
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
      queryClient.invalidateQueries({ queryKey: queryKeys.project(deletedId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard });

      // Force immediate refetch
      queryClient.refetchQueries({ queryKey: queryKeys.projects });
      queryClient.refetchQueries({ queryKey: queryKeys.dashboard });
    },
  });
};

export const useCancelProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason: string }) => {
      const { data } = await projectsAPI.cancel(id, reason);
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.project(variables.id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard });
    },
  });
};

export const useApproveProject = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await projectsAPI.approve(id);
      return data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.project(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard });
    },
  });
};

export const useAddFollowUpQuestion = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, question, priority }: { id: string; question: string; priority: string }) => {
      const { data } = await projectsAPI.addFollowUp(id, { question, priority });
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.project(variables.id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.projects });
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks({ project_id: variables.id }) });
      queryClient.invalidateQueries({ queryKey: ["project-activity", variables.id] });
    },
  });
};

// Agents
export const useAgentStatus = () => {
  return useQuery({
    queryKey: queryKeys.agents,
    queryFn: async () => {
      const { data } = await agentsAPI.list({ active_only: true });
      return data;
    },
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });
};

export const useAgent = (id: string) => {
  return useQuery({
    queryKey: queryKeys.agent(id),
    queryFn: async () => {
      const { data } = await agentsAPI.get(id);
      return data;
    },
    enabled: !!id,
  });
};

// Tasks
export const useTasks = (filters?: {
  project_id?: string;
  agent_id?: string;
  status?: string;
  limit?: number;
}) => {
  return useQuery({
    queryKey: queryKeys.tasks(filters),
    queryFn: async () => {
      const { data } = await tasksAPI.list(filters);
      return data;
    },
    refetchOnWindowFocus: false,
    refetchOnMount: true,
  });
};

export const useTask = (id: string) => {
  return useQuery({
    queryKey: queryKeys.task(id),
    queryFn: async () => {
      const { data } = await tasksAPI.get(id);
      return data;
    },
    enabled: !!id,
  });
};

export const useTaskActivity = (id: string, limit?: number) => {
  return useQuery({
    queryKey: ["task-activity", id, limit],
    queryFn: async () => {
      const { data } = await tasksAPI.getActivity(id, limit);
      return data;
    },
    enabled: !!id,
    refetchOnWindowFocus: false,
    refetchOnMount: true,
  });
};

export const useCancelTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, reason }: { id: string; reason: string }) => {
      const { data } = await tasksAPI.cancel(id, reason);
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.task(variables.id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks() });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard });
    },
  });
};

export const useResolveReviewEscalation = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      id,
      resolutionNotes,
      clearDirection,
      resolvedByAgentId,
    }: {
      id: string;
      resolutionNotes: string;
      clearDirection: string;
      resolvedByAgentId: string;
    }) => {
      const { data } = await tasksAPI.resolveReview(id, {
        resolution_notes: resolutionNotes,
        clear_direction: clearDirection,
        resolved_by_agent_id: resolvedByAgentId,
      });
      return data;
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.task(variables.id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks() });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard });
    },
  });
};

export const useApproveTask = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await tasksAPI.approve(id);
      return data;
    },
    onSuccess: (_, id) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.task(id) });
      queryClient.invalidateQueries({ queryKey: queryKeys.tasks() });
      queryClient.invalidateQueries({ queryKey: queryKeys.dashboard });
    },
  });
};

// Messages
export const useMessages = (filters?: {
  from_agent_id?: string;
  to_agent_id?: string;
  limit?: number;
}) => {
  return useQuery({
    queryKey: queryKeys.messages(filters),
    queryFn: async () => {
      const { data } = await messagesAPI.list(filters);
      return data;
    },
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });
};

// Escalations
export const useEscalations = (filters?: { status?: string; limit?: number }) => {
  return useQuery({
    queryKey: queryKeys.escalations(filters),
    queryFn: async () => {
      const { data } = await escalationsAPI.list(filters);
      return data;
    },
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });
};

// Audit Logs
export const useAuditLogs = (filters?: {
  agent_id?: string;
  action_type?: string;
  limit?: number;
}) => {
  return useQuery({
    queryKey: queryKeys.auditLogs(filters),
    queryFn: async () => {
      const { data } = await auditAPI.list(filters);
      return data;
    },
  });
};

// Dashboard
export const useDashboard = () => {
  return useQuery({
    queryKey: queryKeys.dashboard,
    queryFn: async () => {
      const { data } = await dashboardAPI.metrics();
      return data;
    },
    refetchOnWindowFocus: false,
    refetchOnMount: false,
  });
};

// Agent Activity
export const useAgentActivity = (id: string, limit?: number) => {
  return useQuery({
    queryKey: ["agent-activity", id, limit],
    queryFn: async () => {
      const { data } = await agentsAPI.getActivity(id, limit);
      return data;
    },
    enabled: !!id,
    refetchOnWindowFocus: false,
    refetchOnMount: true,
  });
};

// Human Input Mutation
export const useAddHumanInput = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({
      agentId,
      input_text,
      context,
      related_project_id,
      related_task_id,
    }: {
      agentId: string;
      input_text: string;
      context?: string;
      related_project_id?: string;
      related_task_id?: string;
    }) => {
      const { data } = await agentsAPI.addHumanInput(agentId, {
        input_text,
        context,
        related_project_id,
        related_task_id,
      });
      return data;
    },
    onSuccess: (_, variables) => {
      // Invalidate agent activity to show the new input
      queryClient.invalidateQueries({ queryKey: ["agent-activity", variables.agentId] });

      // Also invalidate project/task activity if related
      if (variables.related_project_id) {
        queryClient.invalidateQueries({ queryKey: ["project-activity", variables.related_project_id] });
      }
      if (variables.related_task_id) {
        queryClient.invalidateQueries({ queryKey: ["task-activity", variables.related_task_id] });
      }
    },
  });
};

// Notifications
export const useNotifications = (unreadOnly: boolean = false) => {
  return useQuery({
    queryKey: queryKeys.notifications(unreadOnly),
    queryFn: async () => {
      const { data } = await notificationsAPI.list(unreadOnly);
      return data;
    },
    refetchInterval: 30000, // Refetch every 30 seconds for notifications
    refetchOnWindowFocus: true,
    refetchOnMount: true,
  });
};

export const useNotificationCount = () => {
  return useQuery({
    queryKey: queryKeys.notificationCount,
    queryFn: async () => {
      const { data } = await notificationsAPI.unreadCount();
      return data.unread_count;
    },
    refetchInterval: 30000, // Refetch every 30 seconds
    refetchOnWindowFocus: true,
    refetchOnMount: true,
  });
};

export const useMarkNotificationRead = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await notificationsAPI.markRead(id);
      return data;
    },
    onSuccess: () => {
      // Invalidate both all and unread notification queries
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications(false) });
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications(true) });
      queryClient.invalidateQueries({ queryKey: queryKeys.notificationCount });
    },
  });
};

export const useMarkAllNotificationsRead = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      const { data } = await notificationsAPI.markAllRead();
      return data;
    },
    onSuccess: () => {
      // Invalidate both all and unread notification queries
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications(false) });
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications(true) });
      queryClient.invalidateQueries({ queryKey: queryKeys.notificationCount });
    },
  });
};

export const useDeleteNotification = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const { data } = await notificationsAPI.delete(id);
      return data;
    },
    onSuccess: () => {
      // Invalidate both all and unread notification queries
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications(false) });
      queryClient.invalidateQueries({ queryKey: queryKeys.notifications(true) });
      queryClient.invalidateQueries({ queryKey: queryKeys.notificationCount });
    },
  });
};

// Conversations
import { conversationsApi } from "@/lib/api/conversations";

export const useCreateOrGetProjectDiscussion = () => {
  return useMutation({
    mutationFn: async ({ projectId, userId }: { projectId: string; userId?: string }) => {
      return await conversationsApi.createOrGetProjectDiscussion(projectId, userId);
    },
  });
};

export const useCreateOrGetTaskDiscussion = () => {
  return useMutation({
    mutationFn: async ({ taskId, userId }: { taskId: string; userId?: string }) => {
      return await conversationsApi.createOrGetTaskDiscussion(taskId, userId);
    },
  });
};
