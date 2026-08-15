/**
 * API client for conversation endpoints
 */

import {
  Conversation,
  ConversationMessage,
  CreateConversationRequest,
  CreateMessageRequest,
  UpdateConversationRequest,
  ConversationType,
  ConversationStatus,
} from "@/types/conversation";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export const conversationsApi = {
  /**
   * Create a new conversation
   */
  async createConversation(
    request: CreateConversationRequest
  ): Promise<Conversation> {
    const response = await fetch(`${API_BASE_URL}/api/v1/conversations`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Failed to create conversation: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * List conversations with filters
   */
  async listConversations(params?: {
    user_id?: string;
    agent_id?: string;
    project_id?: string;
    conversation_type?: ConversationType;
    status?: ConversationStatus;
    limit?: number;
    offset?: number;
  }): Promise<Conversation[]> {
    const queryParams = new URLSearchParams();

    if (params?.user_id) queryParams.append("user_id", params.user_id);
    if (params?.agent_id) queryParams.append("agent_id", params.agent_id);
    if (params?.project_id) queryParams.append("project_id", params.project_id);
    if (params?.conversation_type)
      queryParams.append("conversation_type", params.conversation_type);
    if (params?.status) queryParams.append("status", params.status);
    if (params?.limit) queryParams.append("limit", params.limit.toString());
    if (params?.offset) queryParams.append("offset", params.offset.toString());

    const response = await fetch(
      `${API_BASE_URL}/api/v1/conversations?${queryParams}`
    );

    if (!response.ok) {
      throw new Error(`Failed to list conversations: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Get conversation by ID
   */
  async getConversation(conversationId: string): Promise<Conversation> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/conversations/${conversationId}`
    );

    if (!response.ok) {
      throw new Error(`Failed to get conversation: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Update conversation
   */
  async updateConversation(
    conversationId: string,
    request: UpdateConversationRequest
  ): Promise<Conversation> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/conversations/${conversationId}`,
      {
        method: "PATCH",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to update conversation: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Archive conversation
   */
  async archiveConversation(conversationId: string): Promise<void> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/conversations/${conversationId}`,
      {
        method: "DELETE",
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to archive conversation: ${response.statusText}`);
    }
  },

  /**
   * Create a message in a conversation
   */
  async createMessage(
    conversationId: string,
    request: CreateMessageRequest
  ): Promise<ConversationMessage> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/conversations/${conversationId}/messages`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(request),
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to create message: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * List messages in a conversation
   */
  async listMessages(
    conversationId: string,
    params?: {
      limit?: number;
      offset?: number;
    }
  ): Promise<ConversationMessage[]> {
    const queryParams = new URLSearchParams();

    if (params?.limit) queryParams.append("limit", params.limit.toString());
    if (params?.offset) queryParams.append("offset", params.offset.toString());

    const response = await fetch(
      `${API_BASE_URL}/api/v1/conversations/${conversationId}/messages?${queryParams}`
    );

    if (!response.ok) {
      throw new Error(`Failed to list messages: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Get a specific message
   */
  async getMessage(
    conversationId: string,
    messageId: string
  ): Promise<ConversationMessage> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/conversations/${conversationId}/messages/${messageId}`
    );

    if (!response.ok) {
      throw new Error(`Failed to get message: ${response.statusText}`);
    }

    return response.json();
  },

  /**
   * Mark message as read
   */
  async markMessageRead(
    conversationId: string,
    messageId: string,
    userId: string = "user_1"
  ): Promise<void> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/conversations/${conversationId}/messages/${messageId}/read?user_id=${userId}`,
      {
        method: "POST",
      }
    );

    if (!response.ok) {
      throw new Error(`Failed to mark message as read: ${response.statusText}`);
    }
  },

  /**
   * Mark all messages in conversation as read
   */
  async markAllRead(
    conversationId: string,
    userId: string = "user_1"
  ): Promise<void> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/conversations/${conversationId}/read-all?user_id=${userId}`,
      {
        method: "POST",
      }
    );

    if (!response.ok) {
      throw new Error(
        `Failed to mark all messages as read: ${response.statusText}`
      );
    }
  },

  /**
   * Create or get project discussion (group chat with all project agents)
   */
  async createOrGetProjectDiscussion(
    projectId: string,
    userId: string = "user_1"
  ): Promise<Conversation> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/conversations/projects/${projectId}/discussion?user_id=${userId}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error(
        `Failed to create/get project discussion: ${response.statusText}`
      );
    }

    return response.json();
  },

  /**
   * Create or get task discussion (chat for a specific task)
   */
  async createOrGetTaskDiscussion(
    taskId: string,
    userId: string = "user_1"
  ): Promise<Conversation> {
    const response = await fetch(
      `${API_BASE_URL}/api/v1/conversations/tasks/${taskId}/discussion?user_id=${userId}`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      }
    );

    if (!response.ok) {
      throw new Error(
        `Failed to create/get task discussion: ${response.statusText}`
      );
    }

    return response.json();
  },
};
