/**
 * MessageContextIndicator - Inline context indicators for messages
 * Shows detected entities and intent with visual badges
 * Phase 2: Frontend Integration
 */

import React, { useState } from "react";
import {
  FolderKanban,
  CheckSquare,
  Users,
  HelpCircle,
  Terminal,
  MessageCircle,
  AlertTriangle,
  MessageSquare,
  Lightbulb,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { ExtractedEntities, MessageIntent } from "@/types/context-intelligence";
import { cn } from "@/lib/utils";

interface MessageContextIndicatorProps {
  entities: ExtractedEntities;
  intent?: MessageIntent;
  className?: string;
  compact?: boolean;
  showIntent?: boolean;
  showEntities?: boolean;
}

export function MessageContextIndicator({
  entities,
  intent,
  className,
  compact = false,
  showIntent = true,
  showEntities = true,
}: MessageContextIndicatorProps) {
  const [expanded, setExpanded] = useState(false);

  const hasEntities =
    entities.projects.length > 0 || entities.tasks.length > 0 || entities.agents.length > 0;

  if (!hasEntities && !intent) {
    return null;
  }

  const totalEntities =
    entities.projects.length + entities.tasks.length + entities.agents.length;

  return (
    <div className={cn("flex flex-wrap items-center gap-2 text-xs", className)}>
      {/* Intent Badge */}
      {showIntent && intent && <IntentIcon intent={intent} />}

      {/* Entity Count Summary (Compact Mode) */}
      {compact && hasEntities && !expanded && (
        <button
          onClick={() => setExpanded(true)}
          className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded text-gray-700 transition-colors"
        >
          <span>{totalEntities} reference{totalEntities !== 1 ? "s" : ""}</span>
          <ChevronDown className="w-3 h-3" />
        </button>
      )}

      {/* Entity Badges (Expanded or Non-Compact) */}
      {showEntities && hasEntities && (!compact || expanded) && (
        <>
          {/* Projects */}
          {entities.projects.length > 0 && (
            <EntityCountBadge
              icon={<FolderKanban className="w-3 h-3" />}
              count={entities.projects.length}
              label="Project"
              color="blue"
            />
          )}

          {/* Tasks */}
          {entities.tasks.length > 0 && (
            <EntityCountBadge
              icon={<CheckSquare className="w-3 h-3" />}
              count={entities.tasks.length}
              label="Task"
              color="green"
            />
          )}

          {/* Agents */}
          {entities.agents.length > 0 && (
            <EntityCountBadge
              icon={<Users className="w-3 h-3" />}
              count={entities.agents.length}
              label="Agent"
              color="purple"
            />
          )}

          {/* Collapse Button (Compact Mode) */}
          {compact && expanded && (
            <button
              onClick={() => setExpanded(false)}
              className="inline-flex items-center gap-1 px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded text-gray-700 transition-colors"
            >
              <ChevronUp className="w-3 h-3" />
            </button>
          )}
        </>
      )}
    </div>
  );
}

/**
 * Intent icon component
 */
function IntentIcon({ intent }: { intent: MessageIntent }) {
  const config = {
    question: {
      icon: HelpCircle,
      color: "text-blue-600 bg-blue-50",
      label: "Question",
    },
    command: {
      icon: Terminal,
      color: "text-purple-600 bg-purple-50",
      label: "Command",
    },
    clarification: {
      icon: Lightbulb,
      color: "text-cyan-600 bg-cyan-50",
      label: "Clarification",
    },
    feedback: {
      icon: MessageCircle,
      color: "text-green-600 bg-green-50",
      label: "Feedback",
    },
    escalation: {
      icon: AlertTriangle,
      color: "text-red-600 bg-red-50",
      label: "Escalation",
    },
    discussion: {
      icon: MessageSquare,
      color: "text-gray-600 bg-gray-50",
      label: "Discussion",
    },
  };

  const { icon: Icon, color, label } = config[intent] || config.discussion;

  return (
    <span
      className={cn("inline-flex items-center gap-1 px-2 py-1 rounded", color)}
      title={label}
    >
      <Icon className="w-3 h-3" />
      <span className="font-medium">{label}</span>
    </span>
  );
}

/**
 * Entity count badge component
 */
function EntityCountBadge({
  icon,
  count,
  label,
  color,
}: {
  icon: React.ReactNode;
  count: number;
  label: string;
  color: "blue" | "green" | "purple";
}) {
  const colors = {
    blue: "text-blue-700 bg-blue-50 border-blue-200",
    green: "text-green-700 bg-green-50 border-green-200",
    purple: "text-purple-700 bg-purple-50 border-purple-200",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 px-2 py-1 rounded border",
        colors[color]
      )}
      title={`${count} ${label}${count !== 1 ? "s" : ""}`}
    >
      {icon}
      <span className="font-medium">
        {count} {label}{count !== 1 ? "s" : ""}
      </span>
    </span>
  );
}

/**
 * Simple context badge for minimal display
 */
export function SimpleContextBadge({
  entities,
  intent,
}: {
  entities: ExtractedEntities;
  intent?: MessageIntent;
}) {
  const totalEntities =
    entities.projects.length + entities.tasks.length + entities.agents.length;

  if (totalEntities === 0 && !intent) {
    return null;
  }

  return (
    <div className="flex items-center gap-1 text-xs text-gray-500">
      {intent && (
        <span className="inline-flex items-center">
          {getIntentIcon(intent)}
        </span>
      )}
      {totalEntities > 0 && (
        <span className="inline-flex items-center gap-0.5">
          <span className="w-1.5 h-1.5 rounded-full bg-blue-500" />
          <span>{totalEntities}</span>
        </span>
      )}
    </div>
  );
}

function getIntentIcon(intent: MessageIntent) {
  const icons = {
    question: <HelpCircle className="w-3 h-3" />,
    command: <Terminal className="w-3 h-3" />,
    clarification: <Lightbulb className="w-3 h-3" />,
    feedback: <MessageCircle className="w-3 h-3" />,
    escalation: <AlertTriangle className="w-3 h-3" />,
    discussion: <MessageSquare className="w-3 h-3" />,
  };

  return icons[intent] || icons.discussion;
}

/**
 * Tooltip with detailed context information
 */
export function ContextTooltip({
  entities,
  intent,
  children,
}: {
  entities: ExtractedEntities;
  intent?: MessageIntent;
  children: React.ReactNode;
}) {
  const [showTooltip, setShowTooltip] = useState(false);

  const hasContent =
    entities.projects.length > 0 ||
    entities.tasks.length > 0 ||
    entities.agents.length > 0 ||
    intent;

  if (!hasContent) {
    return <>{children}</>;
  }

  return (
    <div
      className="relative inline-block"
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {children}

      {showTooltip && (
        <div className="absolute z-50 bottom-full left-0 mb-2 p-3 bg-white border border-gray-200 rounded-lg shadow-lg min-w-[200px]">
          <div className="space-y-2">
            {intent && (
              <div>
                <div className="text-xs font-medium text-gray-500 mb-1">Intent</div>
                <div className="text-xs text-gray-700">{intent}</div>
              </div>
            )}

            {entities.projects.length > 0 && (
              <div>
                <div className="text-xs font-medium text-gray-500 mb-1">Projects</div>
                <div className="text-xs text-gray-700">
                  {entities.projects.slice(0, 3).join(", ")}
                  {entities.projects.length > 3 && ` +${entities.projects.length - 3} more`}
                </div>
              </div>
            )}

            {entities.tasks.length > 0 && (
              <div>
                <div className="text-xs font-medium text-gray-500 mb-1">Tasks</div>
                <div className="text-xs text-gray-700">
                  {entities.tasks.slice(0, 3).join(", ")}
                  {entities.tasks.length > 3 && ` +${entities.tasks.length - 3} more`}
                </div>
              </div>
            )}

            {entities.agents.length > 0 && (
              <div>
                <div className="text-xs font-medium text-gray-500 mb-1">Agents</div>
                <div className="text-xs text-gray-700">
                  {entities.agents.slice(0, 3).join(", ")}
                  {entities.agents.length > 3 && ` +${entities.agents.length - 3} more`}
                </div>
              </div>
            )}
          </div>

          {/* Tooltip arrow */}
          <div className="absolute top-full left-4 w-2 h-2 bg-white border-r border-b border-gray-200 transform rotate-45 -mt-1" />
        </div>
      )}
    </div>
  );
}
