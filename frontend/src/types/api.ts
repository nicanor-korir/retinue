// Agent Types
export enum Availability {
  AVAILABLE = "available",
  BUSY = "busy",
  OFFLINE = "offline",
}

export interface Agent {
  agent_id: string;
  name: string;
  role: string;
  capabilities: string[];
  availability: Availability;
  permissions: Record<string, any>;
  system_prompt: string;
  created_at: string;
  department?: string;  // Legacy - primary department
  departments?: string[];  // New - all departments this agent belongs to
  tasks_completed?: number;
  description?: string;
  current_task_id?: string | null;
}

export interface AgentStatus {
  agent_id: string;
  availability: Availability;
  current_task_id: string | null;
  last_active: string;
  last_check: string;
  tasks_completed: number;
  name?: string;
  role?: string;
  department?: string;  // Legacy - primary department
  departments?: string[];  // New - all departments this agent belongs to
  description?: string;
}

// Project Types
export enum ProjectStatus {
  PLANNING = "PLANNING",
  IN_PROGRESS = "IN_PROGRESS",
  REVIEW = "REVIEW",
  COMPLETED = "COMPLETED",
  ON_HOLD = "ON_HOLD",
  CANCELLED = "CANCELLED",
  FAILED = "FAILED",
}

export interface Project {
  project_id: string;
  name: string;
  description: string;
  status: ProjectStatus;
  owner_agent_id: string;
  start_date: string | null;
  end_date: string | null;
  metadata: Record<string, any>;
  created_at: string;
  updated_at: string;
  tasks?: Task[];
}

// Task Types
export enum TaskStatus {
  PENDING = "PENDING",
  IN_PROGRESS = "IN_PROGRESS",
  REVIEW = "REVIEW",
  BLOCKED = "BLOCKED",
  COMPLETED = "COMPLETED",
  CANCELLED = "CANCELLED",
  FAILED = "FAILED",
}

export enum Priority {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  CRITICAL = "critical",
}

export interface Task {
  task_id: string;
  project_id: string;
  assigned_to_agent_id: string;
  title: string;
  description: string;
  status: TaskStatus;
  priority: Priority;
  estimated_hours: number | null;
  actual_hours: number | null;
  dependencies: string[];
  output: Record<string, any>;
  created_at: string;
  updated_at: string;
  completed_at: string | null;
  review_started_at?: string | null;
  version?: number;
  blocking_reason?: string;
}

// Message Types
export enum MessageType {
  INFO = "info",
  TASK_ASSIGNMENT = "task_assignment",
  APPROVAL = "approval",
  ALERT = "alert",
  STATUS_UPDATE = "status_update",
}

export interface Message {
  message_id: string;
  from_agent_id: string;
  to_agent_id: string;
  message_type: MessageType;
  content: string;
  priority: Priority;
  read: boolean;
  metadata: Record<string, any>;
  created_at: string;
}

// Decision Types
export interface Decision {
  decision_id: string;
  agent_id: string;
  decision_type: string;
  context: string;
  decision: string;
  reasoning: string;
  metadata: Record<string, any>;
  created_at: string;
}

// Escalation Types
export interface Escalation {
  escalation_id: string;
  from_agent_id: string;
  to_agent_id: string;
  task_id: string | null;
  issue: string;
  resolution: string | null;
  status: string;
  created_at: string;
  resolved_at: string | null;
}

// Audit Log Types
export interface AuditLog {
  log_id: string;
  agent_id: string;
  action_type: string;
  entity_type: string;
  entity_id: string | null;
  details: Record<string, any>;
  created_at: string;
  action?: string;
  timestamp?: string;
}

// Dashboard Types
export interface DashboardMetrics {
  total_projects: number;
  active_projects: number;
  completed_projects: number;
  total_tasks: number;
  pending_tasks: number;
  in_progress_tasks: number;
  completed_tasks: number;
  active_agents: number;
  total_agents: number;
  recent_activity: {
    projects: Project[];
    tasks: Task[];
    messages: Message[];
  };
}

// Notification Types
export enum NotificationType {
  HUMAN_INTERVENTION_REQUIRED = "human_intervention_required",
  CEO_FEEDBACK = "ceo_feedback",
  PROJECT_COMPLETED = "project_completed",
  PROJECT_FAILED = "project_failed",
  TASK_BLOCKED = "task_blocked",
  ESCALATION = "escalation",
  GENERAL = "general",
}

export interface Notification {
  notification_id: string;
  type: NotificationType;
  title: string;
  message: string;
  related_entity_type: string | null;
  related_entity_id: string | null;
  agent_id: string | null;
  agent_name: string | null;
  priority: Priority;
  read: boolean;
  read_at: string | null;
  created_at: string;
  meta_data: Record<string, any>;
}

// Feedback Types
export enum FeedbackType {
  GENERAL = "general",
  QUALITY = "quality",
  CORRECTNESS = "correctness",
  COMPLETENESS = "completeness",
  DIRECTION = "direction",
  IMPLEMENTATION = "implementation",
  BLOCKING_ISSUE = "blocking_issue",
  ENHANCEMENT = "enhancement",
  BUG_REPORT = "bug_report",
  PERFORMANCE = "performance",
}

// Common Feedback Context
export interface FeedbackContext {
  tags: string[];
  additional_details: string;
}

// Base Feedback Interface (common to all entity types)
interface BaseFeedback {
  feedback_type: FeedbackType;
  title: string;
  description: string;
  priority: Priority;
  context: FeedbackContext;
}

// Project Feedback Request
export interface ProjectFeedbackRequest extends BaseFeedback {
  quality_rating?: number | null; // 0-5
  satisfaction_rating?: number | null; // 0-5
  confidence_level?: number | null; // 0-5
  suggested_actions?: string[];
}

// Project Feedback Response
export interface ProjectFeedback extends ProjectFeedbackRequest {
  feedback_id: string;
  project_id: string;
  created_at: string;
  updated_at: string;
}

// Task Feedback Request
export interface TaskFeedbackRequest extends BaseFeedback {
  output_quality?: number | null; // 0-5
  correctness?: number | null; // 0-5
  completeness?: number | null; // 0-5
  implementation_quality?: number | null; // 0-5
  code_review_feedback?: string | null;
  suggested_improvements?: string[];
  action_items?: string[];
}

// Task Feedback Response
export interface TaskFeedback extends TaskFeedbackRequest {
  feedback_id: string;
  task_id: string;
  project_id?: string;
  created_at: string;
  updated_at: string;
}

// Agent Feedback Request
export interface AgentFeedbackRequest extends BaseFeedback {
  decision_quality?: number | null; // 0-5
  execution_quality?: number | null; // 0-5
  communication_clarity?: number | null; // 0-5
  problem_solving?: number | null; // 0-5
  efficiency?: number | null; // 0-5
  recommended_improvements?: string[];
}

// Agent Feedback Response
export interface AgentFeedback extends AgentFeedbackRequest {
  feedback_id: string;
  agent_id: string;
  created_at: string;
  updated_at: string;
}

// Generic Feedback Response (useful for handling responses from any endpoint)
export interface FeedbackSubmissionResponse {
  feedback_id: string;
  message: string;
  status: 'success' | 'pending' | 'failed';
}

// Feedback List Response (for fetching feedback history)
export interface FeedbackListItem {
  feedback_id: string;
  entity_type: 'project' | 'task' | 'agent';
  entity_id: string;
  entity_name?: string;
  feedback_type: FeedbackType;
  title: string;
  priority: Priority;
  created_at: string;
}

export interface FeedbackListResponse {
  feedbacks: FeedbackListItem[];
  total: number;
  page: number;
  page_size: number;
}

// API Request/Response Types
export interface ProjectCreate {
  name: string;
  description: string;
  priority?: Priority;
  selectedAgents?: string[];
}

export interface HealthResponse {
  status: string;
  agents_count: number;
  agents: Record<string, string>;
}
