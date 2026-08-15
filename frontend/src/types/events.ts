/**
 * TypeScript types for real-time event tracking
 */

export enum ActivityType {
  THINKING = "thinking",
  GENERATING = "generating",
  WAITING = "waiting",
  DECIDING = "deciding",
  MESSAGING = "messaging",
  EXECUTING = "executing",
  REVIEWING = "reviewing",
  COMPLETED = "completed",
  ERROR = "error",
}

export enum ThoughtType {
  ANALYSIS = "analysis",
  PLANNING = "planning",
  REASONING = "reasoning",
  EVALUATION = "evaluation",
  REFLECTION = "reflection",
}

export enum LLMProvider {
  ANTHROPIC = "anthropic",
  OPENAI = "openai",
  GOOGLE = "google",
  LOCAL = "local",
}

export enum HandoffStatus {
  INITIATED = "initiated",
  IN_TRANSIT = "in_transit",
  RECEIVED = "received",
  ACCEPTED = "accepted",
  REJECTED = "rejected",
}

export interface AgentActivity {
  activity_id: string;
  agent_id: string;
  project_id?: string;
  task_id?: string;
  activity_type: ActivityType;
  title: string;
  description?: string;
  progress_percentage: number;
  stage?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  completed_at?: string;
  metadata?: Record<string, any>;
}

export interface AgentThought {
  thought_id: string;
  agent_id: string;
  activity_id?: string;
  project_id?: string;
  task_id?: string;
  thought_type: ThoughtType;
  content: string;
  context?: Record<string, any>;
  created_at: string;
}

export interface LLMInteraction {
  interaction_id: string;
  agent_id: string;
  activity_id?: string;
  project_id?: string;
  task_id?: string;
  provider: LLMProvider;
  model: string;
  prompt: string;
  system_prompt?: string;
  response?: string;
  prompt_tokens?: number;
  completion_tokens?: number;
  total_tokens?: number;
  latency_ms?: number;
  cost?: number;
  status: string;
  error_message?: string;
  started_at: string;
  completed_at?: string;
}

export interface AgentHandoff {
  handoff_id: string;
  from_agent_id: string;
  to_agent_id: string;
  project_id: string;
  task_id?: string;
  handoff_type: string;
  message: string;
  attachments?: any[];
  status: HandoffStatus;
  initiated_at: string;
  received_at?: string;
  completed_at?: string;
  response?: string;
}

export interface DecisionPoint {
  decision_point_id: string;
  agent_id: string;
  activity_id?: string;
  project_id?: string;
  task_id?: string;
  title: string;
  question: string;
  options?: any[];
  rationale?: string;
  pros_cons?: Record<string, any>;
  impact?: string;
  risk_level?: string;
  requires_approval: boolean;
  approved_by?: string;
  approval_status: string;
  chosen_option?: string;
  created_at: string;
  decided_at?: string;
}

export interface TimelineEvent {
  event_id: string;
  project_id: string;
  agent_id?: string;
  event_type: string;
  event_category?: string;
  title: string;
  description?: string;
  related_activity_id?: string;
  related_task_id?: string;
  is_highlight: boolean;
  highlight_type?: string;
  event_timestamp: string;
}

export interface ProjectEventStream {
  activities: AgentActivity[];
  handoffs: AgentHandoff[];
  timeline: TimelineEvent[];
  pending_decisions: DecisionPoint[];
}

export interface AgentEventStream {
  agent_id: string;
  activities: AgentActivity[];
  thoughts: AgentThought[];
  llm_interactions: LLMInteraction[];
}

// WebSocket message types
export interface WebSocketMessage {
  type: string;
  agent_id?: string;
  project_id?: string;
  task_id?: string;
  data: any;
  timestamp: string;
}

export interface WebSocketEvent {
  type: "activity_created" | "activity_updated" | "activity_completed" |
        "thought_recorded" | "llm_interaction" | "llm_stream_chunk" |
        "agent_handoff" | "decision_created" | "timeline_event" | "error";
  data: any;
}
