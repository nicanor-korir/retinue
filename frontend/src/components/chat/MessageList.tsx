/**
 * MessageList - Scrollable list of messages
 */

import React, { useEffect, useRef, memo, useState } from "react";
import { ConversationMessage } from "@/types/conversation";
import { MessageBubble } from "./MessageBubble";
import { Loader2, ArrowDown } from "lucide-react";

interface MessageListProps {
  messages: ConversationMessage[];
  isAgentTyping?: boolean;
  streamingContent?: string;
  streamingAgentName?: string;
  loading?: boolean;
  emptyMessage?: string;
}

export const MessageList = memo(function MessageList({
  messages,
  isAgentTyping = false,
  streamingContent = "",
  streamingAgentName = "Agent",
  loading = false,
  emptyMessage = "No messages yet. Start the conversation!",
}: MessageListProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const prevMessageCountRef = useRef(messages.length);
  const isUserScrolledUpRef = useRef(false);
  const [showScrollButton, setShowScrollButton] = useState(false);

  // Check if user has scrolled up manually
  const handleScroll = () => {
    if (!containerRef.current) return;

    const { scrollTop, scrollHeight, clientHeight } = containerRef.current;
    const distanceFromBottom = scrollHeight - scrollTop - clientHeight;

    // Consider user at bottom if within 100px of bottom
    const isScrolledUp = distanceFromBottom > 100;
    isUserScrolledUpRef.current = isScrolledUp;
    setShowScrollButton(isScrolledUp);
  };

  // Function to scroll to bottom
  const scrollToBottom = () => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
      isUserScrolledUpRef.current = false;
      setShowScrollButton(false);
    }
  };

  // Initial scroll to bottom when messages first load
  useEffect(() => {
    if (messages.length > 0 && containerRef.current && prevMessageCountRef.current === 0) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
      prevMessageCountRef.current = messages.length;
      isUserScrolledUpRef.current = false;
    }
  }, [messages.length]);

  // Auto-scroll to bottom when new messages arrive or content streams
  useEffect(() => {
    // Only scroll if user hasn't manually scrolled up
    if (isUserScrolledUpRef.current) {
      return;
    }

    const messageCountChanged = messages.length !== prevMessageCountRef.current;

    if ((messageCountChanged || streamingContent) && containerRef.current) {
      // Use scrollTop instead of scrollIntoView to keep scroll contained
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
      prevMessageCountRef.current = messages.length;
    }
  }, [messages.length, streamingContent]);

  if (loading) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-gray-400" />
      </div>
    );
  }

  if (messages.length === 0 && !isAgentTyping) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center text-gray-500 dark:text-gray-400">
          <p className="text-lg mb-2">{emptyMessage}</p>
          <p className="text-sm">
            Ask questions, discuss ideas, or brainstorm solutions
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 relative overflow-hidden">
      <div
        ref={containerRef}
        onScroll={handleScroll}
        className="h-full overflow-y-auto px-4 py-6 space-y-4"
      >
        {messages.map((message) => (
          <MessageBubble key={message.message_id} message={message} />
        ))}

        {/* Show streaming message */}
        {isAgentTyping && streamingContent && (
          <MessageBubble
            message={{
              message_id: "streaming",
              conversation_id: "",
              sender_type: "agent" as any,
              sender_id: "agent",
              sender_name: streamingAgentName,
              content: streamingContent,
              content_type: "text" as any,
              message_type: "message" as any,
              created_at: new Date().toISOString(),
              is_edited: false,
              is_deleted: false,
            }}
            isStreaming={true}
            streamingContent={streamingContent}
          />
        )}

        {/* Show typing indicator */}
        {isAgentTyping && !streamingContent && (
          <div className="flex justify-start">
            <div className="bg-gray-100 dark:bg-gray-800 rounded-lg px-4 py-3">
              <div className="text-xs font-semibold mb-1 text-gray-600 dark:text-gray-400">
                {streamingAgentName}
              </div>
              <div className="flex gap-1">
                <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: "0.1s" }}
                />
                <div
                  className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
                  style={{ animationDelay: "0.2s" }}
                />
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Scroll to bottom button */}
      {showScrollButton && (
        <button
          onClick={scrollToBottom}
          className="absolute bottom-4 right-4 p-2 bg-blue-600 hover:bg-blue-700 text-white rounded-full shadow-lg transition-all duration-200 hover:scale-110 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
          aria-label="Scroll to bottom"
        >
          <ArrowDown className="w-5 h-5" />
        </button>
      )}
    </div>
  );
});
