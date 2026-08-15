/**
 * Hook for managing conversation state and operations
 */

import { useState, useEffect, useCallback } from "react";
import {
  Conversation,
  ConversationMessage,
  CreateConversationRequest,
  UpdateConversationRequest,
} from "@/types/conversation";
import { conversationsApi } from "@/lib/api/conversations";

export function useConversation(conversationId?: string) {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [messages, setMessages] = useState<ConversationMessage[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Load conversation details
  const loadConversation = useCallback(async () => {
    if (!conversationId) return;

    setLoading(true);
    setError(null);

    try {
      const data = await conversationsApi.getConversation(conversationId);
      setConversation(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load conversation");
    } finally {
      setLoading(false);
    }
  }, [conversationId]);

  // Load messages
  const loadMessages = useCallback(async () => {
    if (!conversationId) return;

    setLoading(true);
    setError(null);

    try {
      const data = await conversationsApi.listMessages(conversationId, {
        limit: 100,
      });
      setMessages(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load messages");
    } finally {
      setLoading(false);
    }
  }, [conversationId]);

  // Create a new conversation
  const createConversation = useCallback(
    async (request: CreateConversationRequest): Promise<Conversation> => {
      setLoading(true);
      setError(null);

      try {
        const data = await conversationsApi.createConversation(request);
        setConversation(data);
        return data;
      } catch (err) {
        const message = err instanceof Error ? err.message : "Failed to create conversation";
        setError(message);
        throw new Error(message);
      } finally {
        setLoading(false);
      }
    },
    []
  );

  // Update conversation
  const updateConversation = useCallback(
    async (request: UpdateConversationRequest) => {
      if (!conversationId) return;

      setLoading(true);
      setError(null);

      try {
        const data = await conversationsApi.updateConversation(
          conversationId,
          request
        );
        setConversation(data);
      } catch (err) {
        setError(err instanceof Error ? err.message : "Failed to update conversation");
      } finally {
        setLoading(false);
      }
    },
    [conversationId]
  );

  // Add a message to the local state (for real-time updates)
  const addMessage = useCallback((message: ConversationMessage) => {
    setMessages((prev) => [...prev, message]);
  }, []);

  // Update a message in the local state (for streaming updates)
  const updateMessage = useCallback(
    (messageId: string, updates: Partial<ConversationMessage>) => {
      setMessages((prev) =>
        prev.map((msg) =>
          msg.message_id === messageId ? { ...msg, ...updates } : msg
        )
      );
    },
    []
  );

  // Load conversation and messages on mount
  useEffect(() => {
    if (conversationId) {
      loadConversation();
      loadMessages();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId]); // Only re-run when conversationId changes

  return {
    conversation,
    messages,
    loading,
    error,
    createConversation,
    updateConversation,
    loadConversation,
    loadMessages,
    addMessage,
    updateMessage,
  };
}
