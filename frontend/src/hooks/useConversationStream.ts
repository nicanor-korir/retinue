/**
 * Hook for managing WebSocket connection to conversation
 */

import { useState, useEffect, useCallback, useRef } from "react";
import {
  ConversationMessage,
  SenderType,
  ContentType,
  MessageType,
  WSIncomingMessage,
} from "@/types/conversation";

const WS_BASE_URL =
  process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000";

interface UseConversationStreamOptions {
  conversationId: string;
  userId?: string;
  onMessage?: (message: ConversationMessage) => void;
  onAgentTyping?: (agentId: string) => void;
  onContextEnriched?: (data: any) => void; // Phase 2: Context Intelligence
  onError?: (error: string) => void;
}

export function useConversationStream({
  conversationId,
  userId = "user_1",
  onMessage,
  onAgentTyping,
  onContextEnriched,
  onError,
}: UseConversationStreamOptions) {
  const [connected, setConnected] = useState(false);
  const [isAgentTyping, setIsAgentTyping] = useState(false);
  const [streamingContent, setStreamingContent] = useState("");
  const [streamingAgent, setStreamingAgent] = useState<{ id: string; name: string } | null>(null);
  const [error, setError] = useState<string | null>(null);

  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();
  const currentMessageIdRef = useRef<string | null>(null);
  const accumulatedContentRef = useRef<string>("");
  // Keep a ref copy for access inside callbacks (state can be stale in callbacks)
  const streamingAgentRef = useRef<{ id: string; name: string } | null>(null);

  // Send a message to the agent
  const sendMessage = useCallback(
    (content: string) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        console.error("WebSocket is not connected");
        return;
      }

      wsRef.current.send(
        JSON.stringify({
          type: "user_message",
          content,
        })
      );

      // Reset streaming state
      setStreamingContent("");
      currentMessageIdRef.current = null;
      setStreamingAgent(null);
      streamingAgentRef.current = null;
      accumulatedContentRef.current = "";
    },
    []
  );

  // Connect to WebSocket (memoized to prevent re-creation)
  const connect = useCallback(() => {
    // Don't connect if no conversation ID
    if (!conversationId || conversationId.trim() === "") {
      console.log("Skipping WebSocket connection: no conversation ID");
      return;
    }

    // Don't reconnect if already connected
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    // Don't connect if already connecting
    if (wsRef.current?.readyState === WebSocket.CONNECTING) {
      return;
    }

    const wsUrl = `${WS_BASE_URL}/ws/conversations/${conversationId}?user_id=${userId}`;

    try {
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        console.log("WebSocket connected to conversation:", conversationId);
        setConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const data: WSIncomingMessage = JSON.parse(event.data);

          switch (data.type) {
            case "agent_typing":
              setIsAgentTyping(true);
              // Track which agent is typing (multi-agent support)
              const typingAgent = {
                id: data.responding_agent_id || data.agent_id,
                name: data.responding_agent_name || data.agent_name || "Agent",
              };
              setStreamingAgent(typingAgent);
              streamingAgentRef.current = typingAgent;
              // Reset accumulated content for new agent response
              accumulatedContentRef.current = "";
              setStreamingContent("");
              if (onAgentTyping) {
                onAgentTyping(data.responding_agent_id || data.agent_id);
              }
              break;

            case "agent_thinking_chunk":
              // Could display thinking in UI if needed
              console.log("Agent thinking:", data.thinking);
              break;

            case "agent_message_chunk":
              setIsAgentTyping(false);
              // Accumulate content in both state and ref for safety
              accumulatedContentRef.current += data.content;
              setStreamingContent((prev) => prev + data.content);
              // Track agent info if not already set
              if (!streamingAgentRef.current && (data.responding_agent_id || data.responding_agent_name)) {
                const chunkAgent = {
                  id: data.responding_agent_id || "agent",
                  name: data.responding_agent_name || "Agent",
                };
                streamingAgentRef.current = chunkAgent;
                setStreamingAgent(chunkAgent);
              }
              break;

            case "agent_message_complete":
              setIsAgentTyping(false);
              currentMessageIdRef.current = data.message_id;

              // Debug: Log the complete message data
              console.log("agent_message_complete received:", data);
              console.log("Accumulated content ref:", accumulatedContentRef.current);
              console.log("Streaming agent ref:", streamingAgentRef.current);

              // Use the content from the message, or fall back to accumulated content
              const finalContent = data.content || accumulatedContentRef.current || "";

              // Get agent info from message or refs
              const agentId = data.responding_agent_id || data.agent_id || streamingAgentRef.current?.id || "agent";
              const agentName = data.responding_agent_name || data.agent_name || data.sender_name || streamingAgentRef.current?.name || "Agent";

              // Create a complete message object (with multi-agent support)
              const completeMessage: ConversationMessage = {
                message_id: data.message_id,
                conversation_id: conversationId,
                sender_type: SenderType.AGENT,
                sender_id: agentId,
                sender_name: agentName,
                content: finalContent,
                content_type: ContentType.TEXT,
                message_type: MessageType.MESSAGE,
                created_at: new Date().toISOString(),
                is_edited: false,
                is_deleted: false,
              };

              console.log("Created completeMessage:", completeMessage);
              console.log("Final content length:", finalContent.length);

              if (onMessage) {
                onMessage(completeMessage);
              }

              // Reset state and refs after message is complete
              setStreamingContent("");
              setStreamingAgent(null);
              streamingAgentRef.current = null;
              accumulatedContentRef.current = "";
              break;

            case "agent_error":
              // Handle agent-specific errors in multi-agent scenarios
              setIsAgentTyping(false);
              console.error(`Agent ${data.agent_name || data.agent_id} error:`, data.error);
              if (onError) {
                onError(`${data.agent_name || data.agent_id}: ${data.error}`);
              }
              break;

            case "user_message_created":
              // Echo user message back
              const userMessage: ConversationMessage = {
                message_id: data.message_id,
                conversation_id: conversationId,
                sender_type: SenderType.USER,
                sender_id: userId,
                sender_name: "You",
                content: data.content,
                content_type: ContentType.TEXT,
                message_type: MessageType.MESSAGE,
                created_at: new Date().toISOString(),
                is_edited: false,
                is_deleted: false,
              };

              if (onMessage) {
                onMessage(userMessage);
              }
              break;

            case "context_enriched":
              // Phase 2: Context Intelligence - Handle context enriched events
              console.log("Context enriched for message:", data.message_id);
              if (onContextEnriched) {
                onContextEnriched(data);
              }
              break;

            case "error":
              console.error("WebSocket error:", data.error);
              setError(data.error);
              if (onError) {
                onError(data.error);
              }
              break;

            case "pong":
              // Handle ping/pong for keep-alive
              break;

            default:
              console.log("Unknown message type:", (data as any).type);
          }
        } catch (err) {
          console.error("Error parsing WebSocket message:", err);
        }
      };

      ws.onerror = (event) => {
        console.error("WebSocket error:", event);
        setError("WebSocket connection error");
      };

      ws.onclose = () => {
        console.log("WebSocket disconnected");
        setConnected(false);
        setIsAgentTyping(false);

        // Only attempt to reconnect if we have a valid conversation ID
        if (conversationId && conversationId.trim() !== "") {
          reconnectTimeoutRef.current = setTimeout(() => {
            console.log("Attempting to reconnect...");
            connect();
          }, 3000);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error("Error creating WebSocket:", err);
      setError("Failed to connect to chat");
    }
  }, [conversationId, userId, onMessage, onAgentTyping, onContextEnriched, onError]);

  // Disconnect from WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }

    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }

    setConnected(false);
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    // Only connect if we have a valid conversation ID
    if (conversationId && conversationId.trim() !== "") {
      connect();
    } else {
      // If no conversation ID, make sure we're disconnected
      disconnect();
    }

    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [conversationId]); // Only reconnect when conversationId changes

  // Send periodic ping to keep connection alive
  useEffect(() => {
    if (!connected) return;

    const pingInterval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ type: "ping" }));
      }
    }, 30000); // Every 30 seconds

    return () => clearInterval(pingInterval);
  }, [connected]);

  return {
    connected,
    isAgentTyping,
    streamingContent,
    streamingAgent,
    error,
    sendMessage,
    connect,
    disconnect,
  };
}
