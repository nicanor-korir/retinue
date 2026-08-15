/**
 * ContextPanel - Displays extracted context intelligence for conversations
 * Phase 2: Frontend Integration
 */

import React, { useState } from "react";
import {
  Brain,
  FolderKanban,
  CheckSquare,
  Users,
  TrendingUp,
  Lightbulb,
  ChevronDown,
  ChevronRight,
  RefreshCw,
  Loader2,
} from "lucide-react";
import { useContextIntelligence } from "@/hooks/useContextIntelligence";
import { ExtractedEntities, MessageIntent } from "@/types/context-intelligence";
import { ContextLoadingBoundary, ContextPanelSkeleton } from "@/components/context/ContextLoadingBoundary";
import { cn } from "@/lib/utils";

interface ContextPanelProps {
  conversationId: string;
  className?: string;
  showHeader?: boolean;
  collapsible?: boolean;
}

export function ContextPanel({
  conversationId,
  className,
  showHeader = true,
  collapsible = true,
}: ContextPanelProps) {
  const { context, loading, error, lastUpdated, refetch, realTimeConnected } =
    useContextIntelligence(conversationId, {
      enableRealTimeUpdates: true,
    });

  const [collapsed, setCollapsed] = useState(false);

  const hasEntities = context
    ? context.entities.projects.length > 0 ||
      context.entities.tasks.length > 0 ||
      context.entities.agents.length > 0
    : false;

  return (
    <ContextLoadingBoundary
      loading={loading && !context}
      error={error}
      onRetry={refetch}
      loadingMessage="Loading conversation context..."
      errorMessage="Failed to load context intelligence"
      fallback={<ContextPanelSkeleton className={className} />}
      className={className}
    >
      {!context ? (
        <div className={cn("p-4 border rounded-lg bg-gray-50", className)}>
          <p className="text-sm text-gray-500">No context available yet</p>
        </div>
      ) : (
        <div className={cn("border rounded-lg bg-white shadow-sm", className)}>
          {/* Header */}
          {showHeader && (
        <div className="p-3 border-b bg-gradient-to-r from-blue-50 to-purple-50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Brain className="w-5 h-5 text-blue-600" />
            <h3 className="font-semibold text-gray-900">Conversation Context</h3>
            {realTimeConnected && (
              <span className="flex items-center gap-1 text-xs text-green-600">
                <span className="w-2 h-2 bg-green-500 rounded-full animate-pulse" />
                Live
              </span>
            )}
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => refetch()}
              className="p-1 hover:bg-white rounded transition-colors"
              title="Refresh context"
            >
              <RefreshCw className={cn("w-4 h-4 text-gray-600", loading && "animate-spin")} />
            </button>

            {collapsible && (
              <button
                onClick={() => setCollapsed(!collapsed)}
                className="p-1 hover:bg-white rounded transition-colors"
              >
                {collapsed ? (
                  <ChevronRight className="w-4 h-4 text-gray-600" />
                ) : (
                  <ChevronDown className="w-4 h-4 text-gray-600" />
                )}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Content */}
      {!collapsed && (
        <div className="p-4 space-y-4">
          {/* Dominant Intent */}
          {context.dominant_intent && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Lightbulb className="w-4 h-4 text-amber-500" />
                <span className="text-sm font-medium text-gray-700">Conversation Intent</span>
              </div>
              <IntentBadge intent={context.dominant_intent} />
            </div>
          )}

          {/* Entities */}
          {hasEntities && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-green-500" />
                <span className="text-sm font-medium text-gray-700">Referenced Entities</span>
              </div>
              <EntitiesDisplay entities={context.entities} />
            </div>
          )}

          {/* Statistics */}
          <div className="pt-3 border-t">
            <div className="grid grid-cols-2 gap-3 text-xs text-gray-600">
              <div>
                <span className="font-medium">Messages:</span> {context.indexed_message_count}
              </div>
              {lastUpdated && (
                <div>
                  <span className="font-medium">Updated:</span>{" "}
                  {formatRelativeTime(lastUpdated)}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
        </div>
      )}
    </ContextLoadingBoundary>
  );
}

/**
 * Intent badge component
 */
function IntentBadge({ intent }: { intent: MessageIntent }) {
  const config = {
    question: { label: "Question", color: "bg-blue-100 text-blue-700" },
    command: { label: "Command", color: "bg-purple-100 text-purple-700" },
    clarification: { label: "Clarification", color: "bg-cyan-100 text-cyan-700" },
    feedback: { label: "Feedback", color: "bg-green-100 text-green-700" },
    escalation: { label: "Escalation", color: "bg-red-100 text-red-700" },
    discussion: { label: "Discussion", color: "bg-gray-100 text-gray-700" },
  };

  const { label, color } = config[intent] || config.discussion;

  return (
    <span className={cn("inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium", color)}>
      {label}
    </span>
  );
}

/**
 * Entities display component
 */
function EntitiesDisplay({ entities }: { entities: ExtractedEntities }) {
  return (
    <div className="space-y-2">
      {/* Projects */}
      {entities.projects.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 mb-1">
            <FolderKanban className="w-3.5 h-3.5 text-blue-500" />
            <span className="text-xs font-medium text-gray-600">Projects ({entities.projects.length})</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {entities.projects.map((projectId) => (
              <EntityBadge key={projectId} id={projectId} type="project" />
            ))}
          </div>
        </div>
      )}

      {/* Tasks */}
      {entities.tasks.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 mb-1">
            <CheckSquare className="w-3.5 h-3.5 text-green-500" />
            <span className="text-xs font-medium text-gray-600">Tasks ({entities.tasks.length})</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {entities.tasks.map((taskId) => (
              <EntityBadge key={taskId} id={taskId} type="task" />
            ))}
          </div>
        </div>
      )}

      {/* Agents */}
      {entities.agents.length > 0 && (
        <div>
          <div className="flex items-center gap-1.5 mb-1">
            <Users className="w-3.5 h-3.5 text-purple-500" />
            <span className="text-xs font-medium text-gray-600">Agents ({entities.agents.length})</span>
          </div>
          <div className="flex flex-wrap gap-1.5">
            {entities.agents.map((agentId) => (
              <EntityBadge key={agentId} id={agentId} type="agent" />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Entity badge component
 */
function EntityBadge({ id, type }: { id: string; type: "project" | "task" | "agent" }) {
  const colors = {
    project: "bg-blue-50 text-blue-700 border-blue-200 hover:bg-blue-100",
    task: "bg-green-50 text-green-700 border-green-200 hover:bg-green-100",
    agent: "bg-purple-50 text-purple-700 border-purple-200 hover:bg-purple-100",
  };

  const handleClick = () => {
    // Navigate to entity detail page
    // This can be customized based on your routing
    console.log(`Navigate to ${type}: ${id}`);
  };

  return (
    <button
      onClick={handleClick}
      className={cn(
        "inline-flex items-center px-2 py-1 rounded-md text-xs font-medium border transition-colors",
        colors[type]
      )}
      title={`View ${type}: ${id}`}
    >
      {formatEntityId(id, type)}
    </button>
  );
}

/**
 * Format entity ID for display
 */
function formatEntityId(id: string, type: string): string {
  // If it's a UUID, show shortened version
  if (id.length > 20 && id.includes("-")) {
    return `${type.charAt(0).toUpperCase()}:${id.substring(0, 8)}`;
  }
  // Otherwise show the full ID
  return id;
}

/**
 * Format relative time
 */
function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diff = now.getTime() - date.getTime();
  const seconds = Math.floor(diff / 1000);
  const minutes = Math.floor(seconds / 60);
  const hours = Math.floor(minutes / 60);

  if (seconds < 60) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  if (hours < 24) return `${hours}h ago`;
  return date.toLocaleDateString();
}
