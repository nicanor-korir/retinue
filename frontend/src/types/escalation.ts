/**
 * TypeScript types for Escalation Management System
 */

export enum EscalationType {
  TECHNICAL_DECISION = 'technical_decision',
  BUDGET_THRESHOLD = 'budget_threshold',
  AGENT_MALFUNCTION = 'agent_malfunction',
  RESOURCE_ALLOCATION = 'resource_allocation',
  CROSS_DEPT_CONFLICT = 'cross_dept_conflict',
  DEADLINE_RISK = 'deadline_risk',
  SCOPE_CHANGE = 'scope_change',
  STRATEGIC_DIRECTION = 'strategic_direction',
  RESOURCE_CONFLICT = 'resource_conflict',
  PRIORITY_CONFLICT = 'priority_conflict',
  BLOCKED_TASK = 'blocked_task',
  SCOPE_CREEP = 'scope_creep',
}

export enum EscalationPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
  URGENT = 'urgent',
}

export enum EscalationStatus {
  OPEN = 'open',
  IN_PROGRESS = 'in_progress',
  PENDING_AGENT = 'pending_agent',
  PENDING_HUMAN = 'pending_human',
  BLOCKED = 'blocked',
  RESOLVED = 'resolved',
  ESCALATED = 'escalated',
  CLOSED = 'closed',
}

export enum EscalationLevel {
  DEPARTMENT = 'department',
  EXECUTIVE = 'executive',
  HUMAN = 'human',
}

export enum ResolutionType {
  AUTO_RESOLVED = 'auto_resolved',
  HUMAN_DECISION = 'human_decision',
  AGENT_COLLABORATION = 'agent_collaboration',
  ESCALATED_RESOLVED = 'escalated_resolved',
}

export enum ImpactLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

export enum UrgencyLevel {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

export interface Escalation {
  id: string;
  escalation_number: string;
  title: string;
  description: string;
  escalation_type: string;
  priority: string;
  status: string;
  level: string;
  created_by_type: string;
  created_by_id: string;
  assigned_to_type: string | null;
  assigned_to_id: string | null;
  assigned_at: string | null;
  escalation_path: EscalationPathItem[];
  related_task_id: string | null;
  related_project_id: string | null;
  related_agent_id: string | null;
  conflict_parties: ConflictParty[];
  created_at: string;
  updated_at: string;
  resolved_at: string | null;
  closed_at: string | null;
  due_date: string | null;
  sla_deadline: string;
  time_to_first_response: number | null;
  time_to_resolution: number | null;
  resolution_notes: string | null;
  resolution_type: string | null;
  auto_resolution_attempts: number;
  resolved_by_type: string | null;
  resolved_by_id: string | null;
  impact_assessment: string;
  urgency: string;
  department: string | null;
  tags: string[];
  meta_data: Record<string, any>;
}

export interface EscalationPathItem {
  assigned_to_type: string;
  assigned_to_id: string;
  level: string;
  timestamp: string;
  reason?: string;
}

export interface ConflictParty {
  type: string;
  id: string;
  role?: string;
}

export interface TimelineEvent {
  id: string;
  escalation_id: string;
  event_type: string;
  actor_type: string;
  actor_id: string;
  timestamp: string;
  description: string;
  details: Record<string, any>;
  previous_state: Record<string, any> | null;
  new_state: Record<string, any> | null;
}

export interface Comment {
  id: string;
  escalation_id: string;
  author_type: string;
  author_id: string;
  content: string;
  created_at: string;
  updated_at: string;
  is_internal: boolean;
  parent_comment_id: string | null;
  attachments: any[];
  mentions: string[];
}

export interface EscalationStats {
  total_escalations: number;
  open_escalations: number;
  resolved_today: number;
  average_resolution_time_minutes: number;
  sla_compliance_rate: number;
  pending_human_decision: number;
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
}

export interface CreateEscalationRequest {
  title: string;
  description: string;
  escalation_type: EscalationType;
  priority: EscalationPriority;
  impact: ImpactLevel;
  urgency: UrgencyLevel;
  created_by_type: string;
  created_by_id: string;
  related_task_id?: string;
  related_project_id?: string;
  related_agent_id?: string;
  conflict_parties?: ConflictParty[];
  department?: string;
  tags?: string[];
  due_date?: string;
}

export interface UpdateEscalationRequest {
  title?: string;
  description?: string;
  priority?: EscalationPriority;
  status?: EscalationStatus;
  department?: string;
  tags?: string[];
  due_date?: string;
}

export interface ResolveEscalationRequest {
  resolution_type: ResolutionType;
  resolution_notes: string;
  resolved_by_type: string;
  resolved_by_id: string;
}

export interface EscalateRequest {
  actor_type: string;
  actor_id: string;
  reason: string;
}

export interface ReassignRequest {
  new_assigned_to_type: string;
  new_assigned_to_id: string;
  actor_type: string;
  actor_id: string;
  reason?: string;
}

export interface AddCommentRequest {
  author_type: string;
  author_id: string;
  content: string;
  is_internal?: boolean;
  parent_comment_id?: string;
  mentions?: string[];
}

export interface EscalationFilters {
  status?: EscalationStatus[];
  priority?: EscalationPriority[];
  type?: EscalationType[];
  level?: EscalationLevel[];
  assigned_to_id?: string;
  department?: string;
  tags?: string[];
  sla_at_risk?: boolean;
  search?: string;
  page?: number;
  per_page?: number;
  order_by?: string;
  order_desc?: boolean;
}

export interface EscalationListResponse {
  escalations: Escalation[];
  total: number;
  page: number;
  per_page: number;
}
