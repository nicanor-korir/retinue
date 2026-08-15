/**
 * MessageBubble - Individual message display component
 * Supports markdown rendering for rich agent responses
 */

import React, { memo, useMemo } from "react";
import ReactMarkdown from "react-markdown";
import { ConversationMessage, SenderType } from "@/types/conversation";
import { MessageContextIndicator } from "./MessageContextIndicator";
import { MessageIntent } from "@/types/context-intelligence";
import { cn } from "@/lib/utils";
import { UserPlus, Bot } from "lucide-react";

interface MessageBubbleProps {
  message: ConversationMessage;
  isStreaming?: boolean;
  streamingContent?: string;
}

// Helper to detect and parse agent join notifications
function parseAgentJoinNotification(content: string): {
  isAgentJoin: boolean;
  agentName?: string;
  reason?: string;
  remainingContent?: string;
} {
  // Match patterns like "**Agent Name** has joined the conversation."
  // or "**Legal Counsel Agent** has joined the conversation.\n*Reason: ..."
  const joinPattern = /\*\*([^*]+)\*\*\s+has joined the conversation\.(?:\s*\n\*Reason:\s*([^*\n]+)\*)?/g;

  const matches = [...content.matchAll(joinPattern)];
  if (matches.length === 0) {
    return { isAgentJoin: false };
  }

  // Get the last match (most recent agent join)
  const lastMatch = matches[matches.length - 1];
  const agentName = lastMatch[1];
  const reason = lastMatch[2]?.trim();

  // Remove ALL agent join notifications from content
  let cleanedContent = content;
  for (const match of matches) {
    cleanedContent = cleanedContent.replace(match[0], '');
  }
  cleanedContent = cleanedContent.trim();

  return {
    isAgentJoin: true,
    agentName,
    reason,
    remainingContent: cleanedContent || undefined,
  };
}

// Helper to clean up @approve commands and meta-syntax
function cleanMessageContent(content: string): string {
  let cleaned = content;

  // Remove @approve/@reject agent_id patterns
  cleaned = cleaned.replace(/@(approve|reject)\s+\w+/g, '');

  // Remove fake agent join announcements that AI might generate
  // These patterns indicate AI hallucination about agent joining
  cleaned = cleaned.replace(/\*\*[\w\s]+\*\*\s+has joined the conversation\.?(\s*\n\*Reason:[^\n]+\*)?/gi, '');
  cleaned = cleaned.replace(/\*\*[\w\s]+(Agent|Counsel|Manager|Engineer|Designer|Officer)\*\*\s+(is now here|joined|has been added)/gi, '');
  cleaned = cleaned.replace(/Let me bring in (our|the)\s+[\w\s]+\./gi, '');
  cleaned = cleaned.replace(/I('ll| will) (bring in|invite|add)\s+[\w\s]+\s+(to|into) (the|this) conversation\.?/gi, '');

  // Remove horizontal rules that are just separators
  cleaned = cleaned.replace(/\n---\n/g, '\n\n');

  // Clean up excessive newlines
  cleaned = cleaned.replace(/\n{3,}/g, '\n\n');

  return cleaned.trim();
}

export const MessageBubble = memo(function MessageBubble({
  message,
  isStreaming = false,
  streamingContent = "",
}: MessageBubbleProps) {
  const isUser = message.sender_type === SenderType.USER;
  const isAgent = message.sender_type === SenderType.AGENT;
  const isSystem = message.sender_type === SenderType.SYSTEM;

  const rawContent = isStreaming ? streamingContent : message.content;

  // Parse and process the content
  const processedContent = useMemo(() => {
    // Only parse agent join notifications from SYSTEM messages
    // Agent messages with "joined" text are AI hallucinations
    const joinInfo = isSystem
      ? parseAgentJoinNotification(rawContent)
      : { isAgentJoin: false };

    const cleanedContent = cleanMessageContent(
      joinInfo.remainingContent ?? rawContent
    );

    return {
      ...joinInfo,
      displayContent: cleanedContent,
    };
  }, [rawContent, isSystem]);

  // Render agent join notification as a separate component (ONLY for system messages)
  const AgentJoinBanner = processedContent.isAgentJoin && isSystem ? (
    <div className="flex items-center gap-2 mb-3 pb-3 border-b border-gray-200 dark:border-gray-700">
      <div className="flex items-center justify-center w-6 h-6 rounded-full bg-green-100 dark:bg-green-900/30">
        <UserPlus className="w-3.5 h-3.5 text-green-600 dark:text-green-400" />
      </div>
      <div className="flex-1">
        <span className="text-sm font-medium text-green-700 dark:text-green-400">
          {processedContent.agentName}
        </span>
        <span className="text-sm text-gray-600 dark:text-gray-400"> joined the conversation</span>
        {processedContent.reason && (
          <p className="text-xs text-gray-500 dark:text-gray-500 mt-0.5 italic">
            {processedContent.reason}
          </p>
        )}
      </div>
    </div>
  ) : null;

  return (
    <div
      className={cn(
        "flex w-full mb-4",
        isUser && "justify-end",
        isAgent && "justify-start",
        isSystem && "justify-center"
      )}
    >
      <div
        className={cn(
          "max-w-[80%] rounded-lg px-4 py-3",
          isUser && "bg-blue-600 text-white",
          isAgent && "bg-gray-100 text-gray-900 dark:bg-gray-800 dark:text-gray-100",
          isSystem && "bg-yellow-50 text-yellow-900 dark:bg-yellow-900/20 dark:text-yellow-100 text-sm italic"
        )}
      >
        {/* Sender name for agent messages */}
        {isAgent && message.sender_name && (
          <div className="flex items-center gap-1.5 text-xs font-semibold mb-2 text-gray-600 dark:text-gray-400">
            <Bot className="w-3.5 h-3.5" />
            {message.sender_name}
          </div>
        )}

        {/* Agent join banner if applicable */}
        {AgentJoinBanner}

        {/* Message content with markdown rendering */}
        {processedContent.displayContent && (
          <div className="break-words prose prose-sm dark:prose-invert max-w-none
            prose-p:my-2 prose-p:leading-relaxed
            prose-headings:mt-4 prose-headings:mb-2 prose-headings:font-semibold
            prose-h1:text-lg prose-h2:text-base prose-h3:text-sm
            prose-ul:my-2 prose-ul:pl-4 prose-ol:my-2 prose-ol:pl-4
            prose-li:my-0.5
            prose-strong:font-semibold
            prose-code:px-1 prose-code:py-0.5 prose-code:rounded prose-code:bg-gray-200 prose-code:dark:bg-gray-700 prose-code:text-sm prose-code:before:content-none prose-code:after:content-none
            prose-pre:my-2 prose-pre:p-3 prose-pre:rounded-lg prose-pre:bg-gray-900 prose-pre:dark:bg-gray-950
            prose-blockquote:border-l-2 prose-blockquote:border-gray-300 prose-blockquote:dark:border-gray-600 prose-blockquote:pl-3 prose-blockquote:italic prose-blockquote:my-2
            prose-hr:my-4 prose-hr:border-gray-200 prose-hr:dark:border-gray-700
            [&_ul]:list-disc [&_ol]:list-decimal
          ">
            {isUser ? (
              // User messages - render as plain text (no markdown)
              <p className="whitespace-pre-wrap">{processedContent.displayContent}</p>
            ) : (
              // Agent/System messages - render markdown
              <ReactMarkdown
                components={{
                  // Ensure links open in new tab
                  a: ({ children, href }) => (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 dark:text-blue-400 hover:underline"
                    >
                      {children}
                    </a>
                  ),
                  // Clean paragraph rendering
                  p: ({ children }) => (
                    <p className="my-2 leading-relaxed">{children}</p>
                  ),
                }}
              >
                {processedContent.displayContent}
              </ReactMarkdown>
            )}
            {isStreaming && (
              <span className="inline-block w-2 h-4 ml-1 bg-current animate-pulse" />
            )}
          </div>
        )}

        {/* Context Intelligence Indicators (Phase 2) */}
        {!isStreaming && isUser && message.extracted_entities && (
          <MessageContextIndicator
            entities={message.extracted_entities}
            intent={message.intent_classification as MessageIntent}
            className="mt-2"
            compact={true}
          />
        )}

        {/* Timestamp */}
        {!isStreaming && (
          <div
            className={cn(
              "text-xs mt-1",
              isUser && "text-blue-100",
              isAgent && "text-gray-500 dark:text-gray-500",
              isSystem && "text-yellow-700 dark:text-yellow-300"
            )}
          >
            {new Date(message.created_at).toLocaleTimeString([], {
              hour: "2-digit",
              minute: "2-digit",
            })}
          </div>
        )}

        {/* Agent thinking (optional debug view) */}
        {isAgent && message.agent_thinking && (
          <details className="mt-2 text-xs">
            <summary className="cursor-pointer text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-300">
              Agent Thinking
            </summary>
            <div className="mt-1 p-2 bg-gray-50 dark:bg-gray-900 rounded text-gray-700 dark:text-gray-300 italic">
              {message.agent_thinking}
            </div>
          </details>
        )}
      </div>
    </div>
  );
});
