/**
 * TypeScript types for Context Intelligence features
 * Phase 2: Frontend Integration
 */

/**
 * Intent types for message classification
 */
export enum MessageIntent {
  QUESTION = "question",
  COMMAND = "command",
  CLARIFICATION = "clarification",
  FEEDBACK = "feedback",
  ESCALATION = "escalation",
  DISCUSSION = "discussion",
}

/**
 * Extracted entities from a message
 */
export interface ExtractedEntities {
  projects: string[];
  tasks: string[];
  agents: string[];
}

/**
 * Semantic analysis results
 */
export interface SemanticAnalysis {
  summary: string;
  key_phrases: string[];
  sentiment: "neutral" | "positive" | "negative" | "urgent";
  topics: string[];
}

/**
 * RAG context retrieved for a message
 */
export interface RAGContext {
  source: string;
  task_id?: string;
  project_id?: string;
  summary: string;
  relevance_score: number;
  metadata?: Record<string, any>;
}

/**
 * Message context with extracted intelligence
 */
export interface MessageContext {
  message_id: string;
  conversation_id: string;
  sender_type: string;
  sender_id: string;
  content: string;
  extracted_entities: ExtractedEntities;
  intent_classification?: MessageIntent;
  semantic_summary?: string;
  rag_contexts: RAGContext[];
  created_at: string;
}

/**
 * Aggregated conversation context
 */
export interface ConversationContext {
  context_id: string;
  conversation_id: string;
  entities: ExtractedEntities;
  context_summary: {
    main_topics?: string[];
    key_decisions?: string[];
    [key: string]: any;
  };
  dominant_intent?: MessageIntent;
  indexed_message_count: number;
  last_indexed_at?: string;
  created_at: string;
  updated_at: string;
}

/**
 * User activity summary
 */
export interface ActivitySummary {
  [activity_type: string]: number;
}

/**
 * User preferences learned from activity
 */
export interface UserPreferences {
  response_format: "brief" | "detailed";
  preferred_agents: string[];
  topics_of_interest: string[];
}

/**
 * User activity profile
 */
export interface UserActivityProfile {
  user_id: string;
  active_projects: string[];
  frequent_agents: string[];
  common_topics: string[];
  activity_summary: ActivitySummary;
  preferences: UserPreferences;
}

/**
 * Entity reference with metadata
 */
export interface EntityReference {
  type: "project" | "task" | "agent";
  id: string;
  name?: string;
  relevance_score?: number;
}

/**
 * Context enrichment event (WebSocket)
 */
export interface ContextEnrichedEvent {
  type: "context_enriched";
  message_id: string;
  conversation_id: string;
  entities: ExtractedEntities;
  intent?: MessageIntent;
  semantic_summary?: string;
}

/**
 * Context extraction request
 */
export interface ExtractContextRequest {
  conversation_id: string;
}

/**
 * Context extraction response
 */
export interface ExtractContextResponse {
  conversation_id: string;
  total_messages: number;
  processed_count: number;
  status: "completed" | "failed" | "in_progress";
}

/**
 * Context panel display options
 */
export interface ContextPanelOptions {
  showEntities?: boolean;
  showIntent?: boolean;
  showTopics?: boolean;
  showHistoricalContext?: boolean;
  showUserActivity?: boolean;
}

/**
 * Entity badge variant
 */
export type EntityBadgeVariant = "project" | "task" | "agent";

/**
 * Context indicator props
 */
export interface ContextIndicatorProps {
  entities: ExtractedEntities;
  intent?: MessageIntent;
  onClick?: (entity: EntityReference) => void;
}

/**
 * Context loading state
 */
export interface ContextLoadingState {
  loading: boolean;
  error?: Error | null;
  lastUpdated?: Date;
}

/**
 * Context intelligence feature flags
 */
export interface ContextFeatureFlags {
  enabled: boolean;
  showInlineIndicators: boolean;
  showContextPanel: boolean;
  showUserProfile: boolean;
  enableRealTimeUpdates: boolean;
}
