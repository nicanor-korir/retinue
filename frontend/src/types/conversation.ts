/**
 * Types for conversation and chat feature
 */

export enum ConversationType {
  AGENT_CHAT = "agent_chat",
  PROJECT_DISCUSSION = "project_discussion",
  BRAINSTORM = "brainstorm",
}

export enum ConversationStatus {
  ACTIVE = "active",
  ARCHIVED = "archived",
  CONVERTED_TO_PROJECT = "converted_to_project",
}

export enum SenderType {
  USER = "user",
  AGENT = "agent",
  SYSTEM = "system",
}

export enum ContentType {
  TEXT = "text",
  CODE = "code",
  MARKDOWN = "markdown",
  STRUCTURED = "structured",
}

export enum MessageType {
  MESSAGE = "message",
  SYSTEM = "system",
  PROJECT_SUGGESTION = "project_suggestion",
  QUESTION = "question",
}

export interface Conversation {
  conversation_id: string;
  conversation_type: ConversationType;
  title?: string;
  description?: string;
  primary_agent_id?: string;
  project_id?: string;
  created_by_user_id: string;
  status: ConversationStatus;
  is_pinned: boolean;
  participant_count: number;
  message_count: number;
  created_at: string;
  updated_at: string;
  last_message_at?: string;
  last_message_preview?: string;
}

export interface ConversationMessage {
  message_id: string;
  conversation_id: string;
  sender_type: SenderType;
  sender_id: string;
  sender_name?: string;
  content: string;
  content_type: ContentType;
  message_type: MessageType;
  agent_thinking?: string;
  created_at: string;
  is_edited: boolean;
  is_deleted: boolean;
  // Context Intelligence fields (Phase 2)
  extracted_entities?: {
    projects: string[];
    tasks: string[];
    agents: string[];
  };
  intent_classification?: string;
  semantic_summary?: string;
}

export interface CreateConversationRequest {
  conversation_type: ConversationType;
  primary_agent_id?: string;
  project_id?: string;
  title?: string;
  description?: string;
  user_id?: string;
}

export interface CreateMessageRequest {
  content: string;
  sender_id?: string;
  sender_name?: string;
  content_type?: ContentType;
  reply_to_message_id?: string;
}

export interface UpdateConversationRequest {
  title?: string;
  description?: string;
  is_pinned?: boolean;
  status?: ConversationStatus;
}

// WebSocket message types
export interface WSMessage {
  type: string;
  [key: string]: any;
}

export interface WSUserMessage {
  type: "user_message";
  content: string;
}

export interface WSAgentTyping {
  type: "agent_typing";
  agent_id: string;
  agent_name?: string;
  responding_agent_id?: string;
  responding_agent_name?: string;
}

export interface WSAgentThinking {
  type: "agent_thinking_chunk";
  thinking: string;
}

export interface WSAgentMessageChunk {
  type: "agent_message_chunk";
  content: string;
  is_complete: boolean;
  responding_agent_id?: string;
  responding_agent_name?: string;
}

export interface WSAgentMessageComplete {
  type: "agent_message_complete";
  message_id: string;
  content: string;
  is_complete: true;
  agent_id?: string;
  agent_name?: string;
  sender_name?: string;
  responding_agent_id?: string;
  responding_agent_name?: string;
}

export interface WSAgentError {
  type: "agent_error";
  agent_id: string;
  agent_name?: string;
  error: string;
}

export interface WSError {
  type: "error";
  error: string;
}

export interface WSUserMessageCreated {
  type: "user_message_created";
  message_id: string;
  content: string;
}

export interface WSContextEnriched {
  type: "context_enriched";
  message_id: string;
  [key: string]: any;
}

export interface WSPong {
  type: "pong";
  timestamp?: string;
}

export type WSIncomingMessage =
  | WSAgentTyping
  | WSAgentThinking
  | WSAgentMessageChunk
  | WSAgentMessageComplete
  | WSAgentError
  | WSError
  | WSUserMessageCreated
  | WSContextEnriched
  | WSPong;
