import axios, { AxiosInstance } from "axios";
import type {
  Project,
  ProjectCreate,
  Task,
  Message,
  Agent,
  AgentStatus,
  Escalation,
  AuditLog,
  DashboardMetrics,
  Notification,
  HealthResponse,
  ProjectFeedbackRequest,
  ProjectFeedback,
  TaskFeedbackRequest,
  TaskFeedback,
  AgentFeedbackRequest,
  AgentFeedback,
  FeedbackSubmissionResponse,
  FeedbackListResponse,
} from "@/types/api";

// Create axios instance with base URL
const API_BASE_URL_DEFAULT = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const API_BASE_URL = `${process.env.NEXT_PUBLIC_API_URL}/api/v1` || "http://localhost:8000/api/v1";

const axiosInstance: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // For cookies
});

const axiosInstanceDefault: AxiosInstance = axios.create({
  baseURL: API_BASE_URL_DEFAULT,
  headers: {
    "Content-Type": "application/json",
  },
  withCredentials: true, // For cookies
});

// Add response interceptor to handle errors
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle common errors here
    console.error("API Error:", error);
    throw error;
  }
);

/**
 * Health API endpoints
 */
export const healthAPI = {
  check: () => axiosInstanceDefault.get<HealthResponse>("/health"),
};

/**
 * Projects API endpoints
 */
export const projectsAPI = {
  list: () => axiosInstance.get<Project[]>("/projects"),
  get: (id: string) => axiosInstance.get<Project>(`/projects/${id}`),
  create: (data: ProjectCreate) => axiosInstance.post<Project>("/projects", data),
  update: (id: string, data: Partial<ProjectCreate>) =>
    axiosInstance.put<Project>(`/projects/${id}`, data),
  delete: (id: string) => axiosInstance.delete<{ success: boolean }>(`/projects/${id}`),
  cancel: (id: string, reason: string) =>
    axiosInstance.post<Project>(`/projects/${id}/cancel`, { reason }),
  approve: (id: string) =>
    axiosInstance.post<Project>(`/projects/${id}/approve`),
  restart: (id: string, data?: ProjectCreate) =>
    axiosInstance.post<Project>(`/projects/${id}/restart`, data || {}),
  getVersions: (id: string) =>
    axiosInstance.get<any[]>(`/projects/${id}/versions`),
  getActivity: (id: string, limit?: number) =>
    axiosInstance.get<any[]>(`/projects/${id}/activity`, { params: { limit } }),
  addFollowUp: (id: string, data: { question: string; priority: string }) =>
    axiosInstance.post<Task>(`/projects/${id}/follow-up`, data),
};

/**
 * Agents API endpoints
 */
export const agentsAPI = {
  list: (filters?: { skip?: number; limit?: number; department?: string; active_only?: boolean }) =>
    axiosInstance.get<Agent[]>("/agents", { params: filters }),
  get: (id: string) => axiosInstance.get<Agent>(`/agents/${id}`),
  getActivity: (id: string, limit?: number) =>
    axiosInstance.get<any[]>(`/agents/${id}/activity`, { params: { limit } }),
  addHumanInput: (id: string, data: any) =>
    axiosInstance.post(`/agents/${id}/human-input`, data),
};

/**
 * Tasks API endpoints
 */
export const tasksAPI = {
  list: (filters?: {
    project_id?: string;
    agent_id?: string;
    status?: string;
    limit?: number;
  }) => axiosInstance.get<Task[]>("/tasks", { params: filters }),
  get: (id: string) => axiosInstance.get<Task>(`/tasks/${id}`),
  update: (id: string, data: Partial<Task>) =>
    axiosInstance.put<Task>(`/tasks/${id}`, data),
  cancel: (id: string, reason: string) =>
    axiosInstance.post<Task>(`/tasks/${id}/cancel`, null, { params: { reason } }),
  approve: (id: string) =>
    axiosInstance.post<Task>(`/tasks/${id}/approve`),
  getActivity: (id: string, limit?: number) =>
    axiosInstance.get<any[]>(`/tasks/${id}/activity`, { params: { limit } }),
  resolveReview: (id: string, data: {
    resolution_notes: string;
    clear_direction: string;
    resolved_by_agent_id: string;
  }) =>
    axiosInstance.post<any>(`/tasks/${id}/resolve-review`, data),
};

/**
 * Messages API endpoints
 */
export const messagesAPI = {
  list: (filters?: {
    from_agent_id?: string;
    to_agent_id?: string;
    limit?: number;
  }) => axiosInstance.get<Message[]>("/messages", { params: filters }),
  get: (id: string) => axiosInstance.get<Message>(`/messages/${id}`),
  send: (data: any) => axiosInstance.post<Message>("/messages", data),
  markAsRead: (id: string) =>
    axiosInstance.put<Message>(`/messages/${id}/read`),
};

/**
 * Escalations API endpoints
 */
export const escalationsAPI = {
  list: (filters?: { status?: string; limit?: number }) =>
    axiosInstance.get<Escalation[]>("/escalations", { params: filters }),
  get: (id: string) => axiosInstance.get<Escalation>(`/escalations/${id}`),
  resolve: (id: string, resolution: string) =>
    axiosInstance.post<Escalation>(`/escalations/${id}/resolve`, { resolution }),
};

/**
 * Audit Logs API endpoints
 */
export const auditAPI = {
  list: (filters?: {
    agent_id?: string;
    action_type?: string;
    limit?: number;
  }) => axiosInstance.get<AuditLog[]>("/audit-log", { params: filters }),
  get: (id: string) => axiosInstance.get<AuditLog>(`/audit-log/${id}`),
};

/**
 * Dashboard API endpoints
 */
export const dashboardAPI = {
  metrics: () => axiosInstance.get<DashboardMetrics>("/dashboard"),
};

/**
 * Notifications API endpoints
 */
export const notificationsAPI = {
  list: (unreadOnly: boolean = false) =>
    axiosInstance.get<Notification[]>("/notifications", {
      params: { unread_only: unreadOnly },
    }),
  get: (id: string) => axiosInstance.get<Notification>(`/notifications/${id}`),
  markRead: (id: string) =>
    axiosInstance.put<Notification>(`/notifications/${id}/read`),
  markAllRead: () => axiosInstance.post<{ message: string }>("/notifications/mark-all-read"),
  delete: (id: string) =>
    axiosInstance.delete<{ success: boolean }>(`/notifications/${id}`),
  unreadCount: () =>
    axiosInstance.get<{ unread_count: number }>("/notifications/unread-count"),
};

/**
 * System Settings API endpoints (Admin only)
 */
export const systemSettingsAPI = {
  get: () => axiosInstance.get<any>("/system-settings"),
  update: (data: any, updatedBy: string = "admin") =>
    axiosInstance.put<any>("/system-settings", data, {
      params: { updated_by: updatedBy },
    }),
};

/**
 * User Profiles API endpoints
 */
export const userProfilesAPI = {
  list: (limit?: number) =>
    axiosInstance.get<any[]>("/profiles", { params: { limit } }),
  get: (userId: string) => axiosInstance.get<any>(`/profiles/${userId}`),
  create: (data: any) => axiosInstance.post<any>("/profiles", data),
  update: (userId: string, data: any) =>
    axiosInstance.put<any>(`/profiles/${userId}`, data),
};

/**
 * Settings Audit Log API endpoints
 */
export const settingsAuditAPI = {
  list: (filters?: {
    entity_type?: "system_settings" | "user_profile";
    entity_id?: string;
    limit?: number;
  }) => axiosInstance.get<any[]>("/settings-audit-log", { params: filters }),
};

/**
 * Feedback API endpoints
 */
export const feedbackAPI = {
  // Project Feedback
  submitProjectFeedback: (projectId: string, data: ProjectFeedbackRequest) =>
    axiosInstance.post<FeedbackSubmissionResponse>(
      `/projects/${projectId}/feedback`,
      data
    ),
  getProjectFeedback: (projectId: string, limit?: number) =>
    axiosInstance.get<FeedbackListResponse>(`/projects/${projectId}/feedback`, {
      params: { limit },
    }),

  // Task Feedback
  submitTaskFeedback: (taskId: string, data: TaskFeedbackRequest) =>
    axiosInstance.post<FeedbackSubmissionResponse>(
      `/tasks/${taskId}/feedback`,
      data
    ),
  getTaskFeedback: (taskId: string, limit?: number) =>
    axiosInstance.get<FeedbackListResponse>(`/tasks/${taskId}/feedback`, {
      params: { limit },
    }),

  // Agent Feedback
  submitAgentFeedback: (agentId: string, data: AgentFeedbackRequest) =>
    axiosInstance.post<FeedbackSubmissionResponse>(
      `/agents/${agentId}/feedback`,
      data
    ),
  getAgentFeedback: (agentId: string, limit?: number) =>
    axiosInstance.get<FeedbackListResponse>(`/agents/${agentId}/feedback`, {
      params: { limit },
    }),

  // Generic Feedback Operations (optional, for admin/overview purposes)
  listAll: (filters?: {
    entity_type?: "project" | "task" | "agent";
    entity_id?: string;
    feedback_type?: string;
    priority?: string;
    limit?: number;
  }) => axiosInstance.get<FeedbackListResponse>("/feedback", { params: filters }),

  get: (feedbackId: string) =>
    axiosInstance.get<ProjectFeedback | TaskFeedback | AgentFeedback>(
      `/feedback/${feedbackId}`
    ),

  delete: (feedbackId: string) =>
    axiosInstance.delete<{ success: boolean }>(`/feedback/${feedbackId}`),
};

// Named export for hooks that import apiClient
export const apiClient = axiosInstance;

export default axiosInstance;
