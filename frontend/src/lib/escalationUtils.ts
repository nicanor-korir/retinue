/**
 * Utility functions for escalation management
 */
import { 
  EscalationPriority, 
  EscalationStatus, 
  EscalationType,
  EscalationLevel,
  Escalation 
} from '../types/escalation';

/**
 * Get color class for priority badge
 */
export function getPriorityColor(priority: string): string {
  switch (priority.toLowerCase()) {
    case 'critical':
      return 'bg-red-100 text-red-800 border-red-300';
    case 'urgent':
      return 'bg-orange-100 text-orange-800 border-orange-300';
    case 'high':
      return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    case 'medium':
      return 'bg-blue-100 text-blue-800 border-blue-300';
    case 'low':
      return 'bg-gray-100 text-gray-800 border-gray-300';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-300';
  }
}

/**
 * Get color class for status badge
 */
export function getStatusColor(status: string): string {
  switch (status.toLowerCase()) {
    case 'open':
      return 'bg-blue-100 text-blue-800 border-blue-300';
    case 'in_progress':
      return 'bg-indigo-100 text-indigo-800 border-indigo-300';
    case 'pending_agent':
      return 'bg-purple-100 text-purple-800 border-purple-300';
    case 'pending_human':
      return 'bg-orange-100 text-orange-800 border-orange-300';
    case 'blocked':
      return 'bg-red-100 text-red-800 border-red-300';
    case 'resolved':
      return 'bg-green-100 text-green-800 border-green-300';
    case 'escalated':
      return 'bg-yellow-100 text-yellow-800 border-yellow-300';
    case 'closed':
      return 'bg-gray-100 text-gray-800 border-gray-300';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-300';
  }
}

/**
 * Get icon for escalation type
 */
export function getTypeIcon(type: string): string {
  switch (type) {
    case 'technical_decision':
      return '🔧';
    case 'budget_threshold':
      return '💰';
    case 'agent_malfunction':
      return '🤖';
    case 'resource_allocation':
      return '📦';
    case 'cross_dept_conflict':
      return '⚔️';
    case 'deadline_risk':
      return '⏰';
    case 'scope_change':
      return '📋';
    case 'strategic_direction':
      return '🎯';
    case 'resource_conflict':
      return '🔀';
    case 'priority_conflict':
      return '⚡';
    case 'blocked_task':
      return '🚫';
    case 'scope_creep':
      return '📈';
    default:
      return '📌';
  }
}

/**
 * Format escalation type for display
 */
export function formatEscalationType(type: string): string {
  return type
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Format status for display
 */
export function formatStatus(status: string): string {
  return status
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

/**
 * Calculate time remaining until SLA deadline
 */
export function calculateSLARemaining(slaDeadline: string): {
  hours: number;
  minutes: number;
  isAtRisk: boolean;
  isCritical: boolean;
  isBreached: boolean;
} {
  const now = new Date();
  const deadline = new Date(slaDeadline);
  const diffMs = deadline.getTime() - now.getTime();
  const diffMins = Math.floor(diffMs / (1000 * 60));
  
  const hours = Math.floor(diffMins / 60);
  const minutes = diffMins % 60;
  
  // Calculate percentage of time remaining
  const totalMinutes = diffMins;
  const isBreached = totalMinutes < 0;
  const isCritical = totalMinutes > 0 && totalMinutes <= 30; // Less than 30 mins
  const isAtRisk = totalMinutes > 30 && totalMinutes <= 360; // 30 mins - 6 hours
  
  return {
    hours: Math.abs(hours),
    minutes: Math.abs(minutes),
    isAtRisk,
    isCritical,
    isBreached,
  };
}

/**
 * Get SLA status indicator color
 */
export function getSLAStatusColor(slaDeadline: string): string {
  const { isBreached, isCritical, isAtRisk } = calculateSLARemaining(slaDeadline);
  
  if (isBreached) return 'text-red-600 bg-red-50';
  if (isCritical) return 'text-orange-600 bg-orange-50';
  if (isAtRisk) return 'text-yellow-600 bg-yellow-50';
  return 'text-green-600 bg-green-50';
}

/**
 * Format time ago (e.g., "2 hours ago", "5 days ago")
 */
export function formatTimeAgo(dateString: string): string {
  const now = new Date();
  const date = new Date(dateString);
  const diffMs = now.getTime() - date.getTime();
  const diffSecs = Math.floor(diffMs / 1000);
  const diffMins = Math.floor(diffSecs / 60);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);
  
  if (diffSecs < 60) return 'just now';
  if (diffMins < 60) return `${diffMins} min${diffMins !== 1 ? 's' : ''} ago`;
  if (diffHours < 24) return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
  if (diffDays < 7) return `${diffDays} day${diffDays !== 1 ? 's' : ''} ago`;
  if (diffDays < 30) {
    const weeks = Math.floor(diffDays / 7);
    return `${weeks} week${weeks !== 1 ? 's' : ''} ago`;
  }
  const months = Math.floor(diffDays / 30);
  return `${months} month${months !== 1 ? 's' : ''} ago`;
}

/**
 * Format date for display
 */
export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  }).format(date);
}

/**
 * Get level badge color
 */
export function getLevelColor(level: string): string {
  switch (level.toLowerCase()) {
    case 'department':
      return 'bg-blue-100 text-blue-800 border-blue-300';
    case 'executive':
      return 'bg-purple-100 text-purple-800 border-purple-300';
    case 'human':
      return 'bg-red-100 text-red-800 border-red-300';
    default:
      return 'bg-gray-100 text-gray-800 border-gray-300';
  }
}

/**
 * Get assigned person display name
 */
export function getAssignedName(escalation: Escalation): string {
  if (!escalation.assigned_to_id) return 'Unassigned';
  
  const type = escalation.assigned_to_type;
  const id = escalation.assigned_to_id;
  
  // Format agent IDs
  if (type === 'agent') {
    return id.toUpperCase().replace('_', ' ');
  }
  
  return id;
}

/**
 * Check if escalation is overdue
 */
export function isEscalationOverdue(escalation: Escalation): boolean {
  if (!escalation.sla_deadline) return false;
  return new Date(escalation.sla_deadline) < new Date();
}

/**
 * Get priority sort value (for sorting)
 */
export function getPrioritySortValue(priority: string): number {
  switch (priority.toLowerCase()) {
    case 'critical': return 5;
    case 'urgent': return 4;
    case 'high': return 3;
    case 'medium': return 2;
    case 'low': return 1;
    default: return 0;
  }
}

/**
 * Filter escalations based on search query
 */
export function filterEscalations(
  escalations: Escalation[],
  searchQuery: string
): Escalation[] {
  if (!searchQuery.trim()) return escalations;
  
  const query = searchQuery.toLowerCase();
  
  return escalations.filter(escalation => 
    escalation.title.toLowerCase().includes(query) ||
    escalation.description.toLowerCase().includes(query) ||
    escalation.escalation_number.toLowerCase().includes(query) ||
    escalation.tags.some(tag => tag.toLowerCase().includes(query))
  );
}

/**
 * Get escalation priority from impact and urgency
 */
export function calculatePriority(impact: string, urgency: string): EscalationPriority {
  const impactScore = getPrioritySortValue(impact);
  const urgencyScore = getPrioritySortValue(urgency);
  const avgScore = (impactScore + urgencyScore) / 2;
  
  if (avgScore >= 4.5) return EscalationPriority.CRITICAL;
  if (avgScore >= 3.5) return EscalationPriority.URGENT;
  if (avgScore >= 2.5) return EscalationPriority.HIGH;
  if (avgScore >= 1.5) return EscalationPriority.MEDIUM;
  return EscalationPriority.LOW;
}

/**
 * Generate mock escalation for testing
 */
export function generateMockEscalation(overrides?: Partial<Escalation>): Escalation {
  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  
  return {
    id,
    escalation_number: `ESC-2025-${Math.floor(Math.random() * 1000).toString().padStart(4, '0')}`,
    title: 'Sample Escalation',
    description: 'This is a sample escalation for testing',
    escalation_type: 'technical_decision',
    priority: 'high',
    status: 'open',
    level: 'department',
    created_by_type: 'user',
    created_by_id: 'test_user',
    assigned_to_type: 'agent',
    assigned_to_id: 'pm',
    assigned_at: now,
    escalation_path: [],
    related_task_id: null,
    related_project_id: null,
    related_agent_id: null,
    conflict_parties: [],
    created_at: now,
    updated_at: now,
    resolved_at: null,
    closed_at: null,
    due_date: null,
    sla_deadline: new Date(Date.now() + 4 * 60 * 60 * 1000).toISOString(),
    time_to_first_response: null,
    time_to_resolution: null,
    resolution_notes: null,
    resolution_type: null,
    auto_resolution_attempts: 0,
    resolved_by_type: null,
    resolved_by_id: null,
    impact_assessment: 'medium',
    urgency: 'medium',
    department: null,
    tags: [],
    meta_data: {},
    ...overrides,
  };
}
