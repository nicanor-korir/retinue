/**
 * ChatWidget - Main chat interface component
 */

import React, { useState, useEffect, useMemo, useCallback } from "react";
import { MessageSquare, X, Minimize2, Maximize2, Brain, Users } from "lucide-react";
import { useConversation } from "@/hooks/useConversation";
import { useConversationStream } from "@/hooks/useConversationStream";
import { useMultiAgentChat } from "@/hooks/useMultiAgent";
import { MessageList } from "./MessageList";
import { MessageInput } from "./MessageInput";
import { ConversationHistory } from "./ConversationHistory";
import { ContextPanel } from "./ContextPanel";
import { AgentSuggestionsPanel } from "./AgentSuggestionsPanel";
import { ParticipantList, ParticipantCount } from "./ParticipantList";
import { ConversationType, ConversationMessage } from "@/types/conversation";
import { cn } from "@/lib/utils";

interface ChatWidgetProps {
  conversationId?: string;
  agentId?: string;
  projectId?: string;
  conversationType?: ConversationType;
  title?: string;
  className?: string;
  fullScreen?: boolean;
  showHistory?: boolean;
  showContextPanel?: boolean; // Phase 2: Context Intelligence
  autoFocus?: boolean;
}

export function ChatWidget({
  conversationId: initialConversationId,
  agentId,
  projectId,
  conversationType = ConversationType.AGENT_CHAT,
  title,
  className,
  fullScreen = false,
  showHistory = true,
  showContextPanel = true, // Phase 2: Context Intelligence
  autoFocus = false,
}: ChatWidgetProps) {
  const [conversationId, setConversationId] = useState<string | undefined>(
    initialConversationId
  );
  const [historyRefreshTrigger, setHistoryRefreshTrigger] = useState(0);
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [showContext, setShowContext] = useState(false); // Phase 2: Toggle context panel
  const [showParticipants, setShowParticipants] = useState(false); // Multi-agent: Toggle participants panel
  const [creationError, setCreationError] = useState<string | null>(null);

  const {
    conversation,
    messages,
    loading,
    error: conversationError,
    createConversation,
    addMessage: addMessageToState,
  } = useConversation(conversationId);

  // Multi-agent chat features
  const userId = "user_1"; // TODO: Get from auth context
  const {
    suggestions,
    suggestionsLoading,
    suggestionsError,
    participants,
    participantsLoading,
    inviteAgent,
    dismissSuggestion,
    showSuggestions,
    setShowSuggestions,
    refetchSuggestions,
    isInviting,
  } = useMultiAgentChat(conversationId || "", userId);

  // Initialize conversation if needed (only once per agent)
  const [isCreating, setIsCreating] = useState(false);

  // Track pending creation operations to prevent duplicates
  // This ref persists across re-renders and is checked synchronously
  const pendingCreationRef = React.useRef<Set<string>>(new Set());

  useEffect(() => {
    // Cleanup: remove this agentId from pending when component unmounts or agentId changes
    const currentAgentId = agentId;
    return () => {
      if (currentAgentId) {
        pendingCreationRef.current.delete(currentAgentId);
      }
    };
  }, [agentId]);

  useEffect(() => {
    let isCancelled = false;

    async function initConversation() {
      // Don't auto-create if no agentId
      if (!agentId) {
        return;
      }

      // Skip if already have a conversation
      if (conversationId) {
        return;
      }

      // Synchronous check: prevent duplicate creation for same agent
      if (pendingCreationRef.current.has(agentId)) {
        return;
      }

      // Mark as pending immediately (synchronous)
      pendingCreationRef.current.add(agentId);

      setIsCreating(true);
      setCreationError(null);

      try {
        const newConversation = await createConversation({
          conversation_type: conversationType,
          primary_agent_id: agentId,
          project_id: projectId,
          title: title || `Chat with ${agentId}`,
        });

        // Only update state if not cancelled
        if (!isCancelled) {
          setConversationId(newConversation.conversation_id);
          setHistoryRefreshTrigger((prev) => prev + 1);
        }
      } catch (err: any) {
        console.error("Failed to create conversation:", err);
        const errorMsg = err?.message || "Failed to create conversation";

        if (!isCancelled) {
          // Check for specific error types
          if (errorMsg.includes("foreign key") || errorMsg.includes("ForeignKeyViolation")) {
            setCreationError(`Agent "${agentId}" not found. Please check if the agent exists.`);
          } else {
            setCreationError(errorMsg);
          }
        }

        // Allow retry on error
        pendingCreationRef.current.delete(agentId);
      } finally {
        if (!isCancelled) {
          setIsCreating(false);
        }
      }
    }

    initConversation();

    return () => {
      isCancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agentId]); // Only run when agentId changes

  // Handle conversation switching
  const handleSelectConversation = useCallback((newConversationId: string) => {
    setConversationId(newConversationId);
  }, []);

  // Handle new conversation
  const handleNewConversation = useCallback(async () => {
    setCreationError(null);

    try {
      const newConversation = await createConversation({
        conversation_type: conversationType,
        primary_agent_id: agentId,
        project_id: projectId,
        title: title || `Chat with ${agentId}`,
      });
      setConversationId(newConversation.conversation_id);
      // Trigger history refresh to show the new conversation
      setHistoryRefreshTrigger((prev) => prev + 1);
    } catch (err: any) {
      console.error("Failed to create conversation:", err);
      const errorMsg = err?.message || "Failed to create conversation";

      // Check for specific error types
      if (errorMsg.includes("foreign key") || errorMsg.includes("ForeignKeyViolation")) {
        setCreationError(`Agent "${agentId}" not found. Please check if the agent exists in the database.`);
      } else {
        setCreationError(errorMsg);
      }
    }
  }, [createConversation, conversationType, agentId, projectId, title]);

  // Toggle fullscreen mode
  const toggleFullscreen = useCallback(() => {
    setIsFullscreen((prev) => !prev);
  }, []);

  // Handle ESC key to exit fullscreen
  useEffect(() => {
    const handleEscape = (e: KeyboardEvent) => {
      if (e.key === "Escape" && isFullscreen) {
        setIsFullscreen(false);
      }
    };

    if (isFullscreen) {
      document.addEventListener("keydown", handleEscape);
      // Prevent body scroll when fullscreen
      document.body.style.overflow = "hidden";
    } else {
      document.body.style.overflow = "";
    }

    return () => {
      document.removeEventListener("keydown", handleEscape);
      document.body.style.overflow = "";
    };
  }, [isFullscreen]);

  // Memoize the onMessage callback to prevent re-creating WebSocket connection
  const handleNewMessage = useCallback((message: ConversationMessage) => {
    addMessageToState(message);
  }, [addMessageToState]);

  // Handle context enriched events (Phase 2: Context Intelligence)
  const handleContextEnriched = useCallback((data: any) => {
    console.log("Context enriched event received:", data);
    // The ContextPanel will auto-refresh via useContextIntelligence hook
    // which listens to WebSocket updates. No action needed here.
  }, []);

  // WebSocket connection
  const {
    connected,
    isAgentTyping,
    streamingContent,
    streamingAgent,
    error: wsError,
    sendMessage,
  } = useConversationStream({
    conversationId: conversationId || "",
    onMessage: handleNewMessage,
    onContextEnriched: handleContextEnriched,
  });

  const handleSendMessage = useCallback((content: string) => {
    if (!conversationId || !connected) {
      console.error("Cannot send message: not connected");
      return;
    }

    sendMessage(content);
  }, [conversationId, connected, sendMessage]);

  const chatTitle = title || conversation?.title || "Chat with Agent";
  const error = conversationError || wsError || creationError;

  // Determine if we should use fullscreen mode
  const useFullscreen = fullScreen || isFullscreen;

  return (
    <div
      className={cn(
        "flex bg-white dark:bg-gray-900 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 overflow-hidden",
        useFullscreen ? "fixed inset-0 z-50 rounded-none" : "h-[600px]",
        className
      )}
    >
      {/* Conversation History Sidebar */}
      {showHistory && (
        <ConversationHistory
          agentId={agentId}
          projectId={projectId}
          conversationType={conversationType}
          activeConversationId={conversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          refreshTrigger={historyRefreshTrigger}
          className="w-64 flex-shrink-0"
        />
      )}

      {/* Main Chat Area */}
      <div className="flex flex-col flex-1 min-w-0">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          <div className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-blue-600" />
            <h3 className="font-semibold text-gray-900 dark:text-gray-100">
              {chatTitle}
            </h3>
            {connected && (
              <span className="w-2 h-2 bg-green-500 rounded-full" title="Connected" />
            )}
            {!connected && conversationId && (
              <span className="w-2 h-2 bg-red-500 rounded-full" title="Disconnected" />
            )}
          </div>

          {/* Header Actions */}
          <div className="flex items-center gap-2">
            {/* Multi-Agent Participants Toggle */}
            {conversationId && (
              <button
                onClick={() => setShowParticipants(!showParticipants)}
                className={cn(
                  "p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors flex items-center gap-1",
                  showParticipants && "bg-blue-100 dark:bg-blue-900"
                )}
                aria-label={showParticipants ? "Hide participants" : "Show participants"}
                title="Participants"
              >
                <Users className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                {participants.length > 0 && (
                  <span className="text-xs text-gray-600 dark:text-gray-400">{participants.length}</span>
                )}
              </button>
            )}

            {/* Context Intelligence Toggle (Phase 2) */}
            {showContextPanel && conversationId && (
              <button
                onClick={() => setShowContext(!showContext)}
                className={cn(
                  "p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors",
                  showContext && "bg-blue-100 dark:bg-blue-900"
                )}
                aria-label={showContext ? "Hide context" : "Show context"}
                title="Context Intelligence"
              >
                <Brain className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              </button>
            )}

            <button
              onClick={toggleFullscreen}
              className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
              aria-label={isFullscreen ? "Exit fullscreen" : "Enter fullscreen"}
              title={isFullscreen ? "Exit fullscreen (ESC)" : "Enter fullscreen"}
            >
              {isFullscreen ? (
                <Minimize2 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              ) : (
                <Maximize2 className="w-4 h-4 text-gray-600 dark:text-gray-400" />
              )}
            </button>
          </div>
        </div>

        {/* Error message */}
        {error && (
          <div className="px-4 py-2 bg-red-50 dark:bg-red-900/20 border-b border-red-200 dark:border-red-800">
            <p className="text-sm text-red-600 dark:text-red-400">{error}</p>
          </div>
        )}

        {/* Agent Suggestions Panel (Multi-Agent) */}
        {conversationId && showSuggestions && (
          <div className="px-4 py-2 border-b border-gray-200 dark:border-gray-700">
            {suggestionsLoading ? (
              <div className="flex items-center justify-center py-3 text-sm text-gray-500">
                <div className="w-4 h-4 border-2 border-blue-500 border-t-transparent rounded-full animate-spin mr-2" />
                Finding relevant agents...
              </div>
            ) : suggestionsError ? (
              <div className="flex items-center justify-between py-3 text-sm bg-red-50 dark:bg-red-900/20 rounded-lg px-3">
                <span className="text-red-600 dark:text-red-400">
                  Failed to load suggestions.
                  <button
                    onClick={() => refetchSuggestions()}
                    className="ml-2 underline hover:no-underline"
                  >
                    Try again
                  </button>
                </span>
                <button
                  onClick={() => setShowSuggestions(false)}
                  className="text-red-400 hover:text-red-600"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            ) : suggestions.length > 0 ? (
              <AgentSuggestionsPanel
                suggestions={suggestions}
                onInvite={(agentId) => inviteAgent(agentId, "Invited from suggestions")}
                onDismiss={dismissSuggestion}
                onClose={() => setShowSuggestions(false)}
                isInviting={isInviting}
              />
            ) : (
              <div className="flex items-center justify-between py-3 text-sm text-gray-500 bg-gray-50 dark:bg-gray-800 rounded-lg px-3">
                <span>No agent suggestions available for this conversation yet.</span>
                <button
                  onClick={() => setShowSuggestions(false)}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-4 h-4" />
                </button>
              </div>
            )}
          </div>
        )}

        {/* Messages */}
        <MessageList
          messages={messages}
          isAgentTyping={isAgentTyping}
          streamingContent={streamingContent}
          streamingAgentName={streamingAgent?.name}
          loading={loading && !conversationId}
          emptyMessage={
            !conversationId
              ? "Select a conversation or start a new one!"
              : agentId
              ? "Start chatting with the agent! Ask questions or discuss ideas."
              : "Loading conversation..."
          }
        />

        {/* Input */}
        <MessageInput
          onSend={handleSendMessage}
          disabled={!connected || !conversationId}
          placeholder={
            !conversationId
              ? "Select or start a conversation..."
              : !connected
              ? "Connecting..."
              : "Type your message..."
          }
          autoFocus={autoFocus}
        />
      </div>

      {/* Participants Panel (Multi-Agent) */}
      {showParticipants && conversationId && (
        <div className="w-72 flex-shrink-0 border-l border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 overflow-y-auto">
          <ParticipantList
            participants={participants}
            onInviteMore={() => setShowSuggestions(true)}
            currentUserId={userId}
            className="m-4"
          />
        </div>
      )}

      {/* Context Intelligence Panel (Phase 2) */}
      {showContextPanel && showContext && conversationId && (
        <div className="w-80 flex-shrink-0 border-l border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900 overflow-y-auto">
          <ContextPanel
            conversationId={conversationId}
            className="m-4"
            showHeader={true}
            collapsible={false}
          />
        </div>
      )}
    </div>
  );
}
