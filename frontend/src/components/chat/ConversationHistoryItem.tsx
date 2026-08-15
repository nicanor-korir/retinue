/**
 * ConversationHistoryItem - Single conversation in history list
 */

import React from "react";
import { Conversation } from "@/types/conversation";
import { cn } from "@/lib/utils";
import { MessageSquare, Pin } from "lucide-react";

interface ConversationHistoryItemProps {
  conversation: Conversation;
  isActive: boolean;
  onClick: () => void;
}

export function ConversationHistoryItem({
  conversation,
  isActive,
  onClick,
}: ConversationHistoryItemProps) {
  const formatTime = (dateString?: string) => {
    if (!dateString) return "";

    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays === 1) return "Yesterday";
    if (diffDays < 7) return `${diffDays}d ago`;

    return date.toLocaleDateString();
  };

  const getTitle = () => {
    if (conversation.title) return conversation.title;
    if (conversation.message_count === 0) return "New Conversation";
    return `Conversation ${conversation.conversation_id.slice(0, 8)}`;
  };

  const preview = conversation.last_message_preview || "No messages yet";
  const timeAgo = formatTime(conversation.last_message_at || conversation.created_at);

  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full text-left px-3 py-3 rounded-lg transition-colors",
        "hover:bg-gray-100 dark:hover:bg-gray-800",
        isActive && "bg-blue-50 dark:bg-blue-900/20 border-l-2 border-blue-600",
        !isActive && "border-l-2 border-transparent"
      )}
    >
      <div className="flex items-start justify-between gap-2 mb-1">
        <div className="flex items-center gap-2 flex-1 min-w-0">
          <MessageSquare className="w-4 h-4 text-gray-400 flex-shrink-0" />
          <h4 className="text-sm font-medium text-gray-900 dark:text-gray-100 truncate">
            {getTitle()}
          </h4>
          {conversation.is_pinned && (
            <Pin className="w-3 h-3 text-blue-600 flex-shrink-0" />
          )}
        </div>
      </div>

      <p className="text-xs text-gray-600 dark:text-gray-400 truncate mb-1">
        {preview}
      </p>

      <div className="flex items-center justify-between">
        <span className="text-xs text-gray-500 dark:text-gray-500">
          {timeAgo}
        </span>
        {conversation.message_count > 0 && (
          <span className="text-xs text-gray-500 dark:text-gray-500">
            {conversation.message_count} {conversation.message_count === 1 ? "message" : "messages"}
          </span>
        )}
      </div>
    </button>
  );
}
