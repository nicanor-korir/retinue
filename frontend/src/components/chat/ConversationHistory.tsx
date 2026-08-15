/**
 * ConversationHistory - Sidebar showing conversation history
 */

import React, { useEffect, useState } from "react";
import { Conversation, ConversationType, ConversationStatus } from "@/types/conversation";
import { conversationsApi } from "@/lib/api/conversations";
import { ConversationHistoryItem } from "./ConversationHistoryItem";
import { Plus, Loader2, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

interface ConversationHistoryProps {
  agentId?: string;
  projectId?: string;
  conversationType?: ConversationType;
  activeConversationId?: string;
  onSelectConversation: (conversationId: string) => void;
  onNewConversation: () => void;
  className?: string;
  refreshTrigger?: number;
}

export function ConversationHistory({
  agentId,
  projectId,
  conversationType,
  activeConversationId,
  onSelectConversation,
  onNewConversation,
  className,
  refreshTrigger,
}: ConversationHistoryProps) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadConversations = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await conversationsApi.listConversations({
        user_id: "user_1",
        agent_id: agentId,
        project_id: projectId,
        conversation_type: conversationType,
        status: ConversationStatus.ACTIVE,
        limit: 50,
      });

      setConversations(data);
    } catch (err) {
      console.error("Failed to load conversations:", err);
      setError("Failed to load conversations");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadConversations();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [agentId, projectId, conversationType, refreshTrigger]);

  return (
    <div
      className={cn(
        "flex flex-col h-full bg-gray-50 dark:bg-gray-900 border-r border-gray-200 dark:border-gray-700",
        className
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-gray-200 dark:border-gray-700">
        <h3 className="text-sm font-semibold text-gray-900 dark:text-gray-100">
          Chat History
        </h3>
        <div className="flex gap-1">
          <button
            onClick={loadConversations}
            disabled={loading}
            className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-800 rounded transition-colors disabled:opacity-50"
            aria-label="Refresh conversations"
          >
            <RefreshCw className={cn("w-4 h-4", loading && "animate-spin")} />
          </button>
          <button
            onClick={onNewConversation}
            className="p-1.5 hover:bg-gray-200 dark:hover:bg-gray-800 rounded transition-colors"
            aria-label="New conversation"
          >
            <Plus className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Conversation List */}
      <div className="flex-1 overflow-y-auto p-2 space-y-1">
        {loading && conversations.length === 0 && (
          <div className="flex items-center justify-center h-32">
            <Loader2 className="w-6 h-6 animate-spin text-gray-400" />
          </div>
        )}

        {error && (
          <div className="p-4 text-sm text-red-600 dark:text-red-400">
            {error}
          </div>
        )}

        {!loading && conversations.length === 0 && !error && (
          <div className="p-4 text-center text-sm text-gray-500 dark:text-gray-400">
            <p>No conversations yet.</p>
            <p className="mt-1">Start a new one!</p>
          </div>
        )}

        {conversations.map((conversation) => (
          <ConversationHistoryItem
            key={conversation.conversation_id}
            conversation={conversation}
            isActive={conversation.conversation_id === activeConversationId}
            onClick={() => onSelectConversation(conversation.conversation_id)}
          />
        ))}
      </div>
    </div>
  );
}
