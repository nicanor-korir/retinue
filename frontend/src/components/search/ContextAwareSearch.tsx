/**
 * ContextAwareSearch - Smart search with context intelligence
 * Phase 2: Frontend Integration
 */

import React, { useState, useCallback, useMemo } from "react";
import {
  Search,
  X,
  Filter,
  FolderKanban,
  CheckSquare,
  Users,
  Tag,
  Calendar,
  SlidersHorizontal,
} from "lucide-react";
import { ConversationMessage } from "@/types/conversation";
import { MessageIntent, ExtractedEntities } from "@/types/context-intelligence";
import { cn } from "@/lib/utils";

interface ContextAwareSearchProps {
  messages: ConversationMessage[];
  onFilteredResults?: (results: ConversationMessage[]) => void;
  className?: string;
}

interface SearchFilters {
  query: string;
  intent?: MessageIntent;
  projectIds: string[];
  taskIds: string[];
  agentIds: string[];
  dateRange?: {
    start: Date;
    end: Date;
  };
}

export function ContextAwareSearch({
  messages,
  onFilteredResults,
  className,
}: ContextAwareSearchProps) {
  const [filters, setFilters] = useState<SearchFilters>({
    query: "",
    projectIds: [],
    taskIds: [],
    agentIds: [],
  });
  const [showFilters, setShowFilters] = useState(false);

  // Extract all unique entities from messages
  const availableEntities = useMemo(() => {
    const projects = new Set<string>();
    const tasks = new Set<string>();
    const agents = new Set<string>();

    messages.forEach((msg) => {
      if (msg.extracted_entities) {
        msg.extracted_entities.projects.forEach((p) => projects.add(p));
        msg.extracted_entities.tasks.forEach((t) => tasks.add(t));
        msg.extracted_entities.agents.forEach((a) => agents.add(a));
      }
    });

    return {
      projects: Array.from(projects),
      tasks: Array.from(tasks),
      agents: Array.from(agents),
    };
  }, [messages]);

  // Filter messages based on current filters
  const filteredMessages = useMemo(() => {
    let results = messages;

    // Text search
    if (filters.query.trim() !== "") {
      const query = filters.query.toLowerCase();
      results = results.filter(
        (msg) =>
          msg.content.toLowerCase().includes(query) ||
          msg.semantic_summary?.toLowerCase().includes(query)
      );
    }

    // Intent filter
    if (filters.intent) {
      results = results.filter((msg) => msg.intent_classification === filters.intent);
    }

    // Project filter
    if (filters.projectIds.length > 0) {
      results = results.filter((msg) =>
        msg.extracted_entities?.projects.some((p) => filters.projectIds.includes(p))
      );
    }

    // Task filter
    if (filters.taskIds.length > 0) {
      results = results.filter((msg) =>
        msg.extracted_entities?.tasks.some((t) => filters.taskIds.includes(t))
      );
    }

    // Agent filter
    if (filters.agentIds.length > 0) {
      results = results.filter((msg) =>
        msg.extracted_entities?.agents.some((a) => filters.agentIds.includes(a))
      );
    }

    // Date range filter
    if (filters.dateRange) {
      results = results.filter((msg) => {
        const msgDate = new Date(msg.created_at);
        return (
          msgDate >= filters.dateRange!.start &&
          msgDate <= filters.dateRange!.end
        );
      });
    }

    return results;
  }, [messages, filters]);

  // Notify parent of filtered results
  React.useEffect(() => {
    if (onFilteredResults) {
      onFilteredResults(filteredMessages);
    }
  }, [filteredMessages, onFilteredResults]);

  const handleQueryChange = useCallback((query: string) => {
    setFilters((prev) => ({ ...prev, query }));
  }, []);

  const handleIntentFilter = useCallback((intent?: MessageIntent) => {
    setFilters((prev) => ({ ...prev, intent }));
  }, []);

  const toggleEntityFilter = useCallback(
    (type: "projectIds" | "taskIds" | "agentIds", id: string) => {
      setFilters((prev) => {
        const current = prev[type];
        const updated = current.includes(id)
          ? current.filter((i) => i !== id)
          : [...current, id];
        return { ...prev, [type]: updated };
      });
    },
    []
  );

  const clearFilters = useCallback(() => {
    setFilters({
      query: "",
      projectIds: [],
      taskIds: [],
      agentIds: [],
    });
  }, []);

  const hasActiveFilters =
    filters.query !== "" ||
    filters.intent !== undefined ||
    filters.projectIds.length > 0 ||
    filters.taskIds.length > 0 ||
    filters.agentIds.length > 0;

  return (
    <div className={cn("space-y-3", className)}>
      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
        <input
          type="text"
          value={filters.query}
          onChange={(e) => handleQueryChange(e.target.value)}
          placeholder="Search messages and context..."
          className="w-full pl-10 pr-20 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
        <div className="absolute right-2 top-1/2 transform -translate-y-1/2 flex items-center gap-1">
          {hasActiveFilters && (
            <button
              onClick={clearFilters}
              className="p-1 hover:bg-gray-100 rounded transition-colors"
              title="Clear filters"
            >
              <X className="w-4 h-4 text-gray-500" />
            </button>
          )}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              "p-1 hover:bg-gray-100 rounded transition-colors",
              showFilters && "bg-blue-100"
            )}
            title="Toggle filters"
          >
            <SlidersHorizontal className="w-4 h-4 text-gray-600" />
          </button>
        </div>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="p-3 border border-gray-200 rounded-lg bg-gray-50 space-y-3">
          {/* Intent Filter */}
          <div>
            <label className="text-xs font-medium text-gray-700 mb-1 block">
              Intent
            </label>
            <div className="flex flex-wrap gap-1">
              {["question", "command", "clarification", "feedback", "escalation", "discussion"].map(
                (intent) => (
                  <button
                    key={intent}
                    onClick={() =>
                      handleIntentFilter(
                        filters.intent === intent
                          ? undefined
                          : (intent as MessageIntent)
                      )
                    }
                    className={cn(
                      "px-2 py-1 text-xs rounded transition-colors",
                      filters.intent === intent
                        ? "bg-blue-600 text-white"
                        : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-300"
                    )}
                  >
                    {intent}
                  </button>
                )
              )}
            </div>
          </div>

          {/* Project Filter */}
          {availableEntities.projects.length > 0 && (
            <div>
              <label className="text-xs font-medium text-gray-700 mb-1 flex items-center gap-1">
                <FolderKanban className="w-3 h-3" />
                Projects
              </label>
              <div className="flex flex-wrap gap-1">
                {availableEntities.projects.map((projectId) => (
                  <button
                    key={projectId}
                    onClick={() => toggleEntityFilter("projectIds", projectId)}
                    className={cn(
                      "px-2 py-1 text-xs rounded transition-colors",
                      filters.projectIds.includes(projectId)
                        ? "bg-blue-600 text-white"
                        : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-300"
                    )}
                  >
                    {formatEntityId(projectId)}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Task Filter */}
          {availableEntities.tasks.length > 0 && (
            <div>
              <label className="text-xs font-medium text-gray-700 mb-1 flex items-center gap-1">
                <CheckSquare className="w-3 h-3" />
                Tasks
              </label>
              <div className="flex flex-wrap gap-1">
                {availableEntities.tasks.map((taskId) => (
                  <button
                    key={taskId}
                    onClick={() => toggleEntityFilter("taskIds", taskId)}
                    className={cn(
                      "px-2 py-1 text-xs rounded transition-colors",
                      filters.taskIds.includes(taskId)
                        ? "bg-green-600 text-white"
                        : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-300"
                    )}
                  >
                    {formatEntityId(taskId)}
                  </button>
                ))}
              </div>
            </div>
          )}

          {/* Agent Filter */}
          {availableEntities.agents.length > 0 && (
            <div>
              <label className="text-xs font-medium text-gray-700 mb-1 flex items-center gap-1">
                <Users className="w-3 h-3" />
                Agents
              </label>
              <div className="flex flex-wrap gap-1">
                {availableEntities.agents.map((agentId) => (
                  <button
                    key={agentId}
                    onClick={() => toggleEntityFilter("agentIds", agentId)}
                    className={cn(
                      "px-2 py-1 text-xs rounded transition-colors",
                      filters.agentIds.includes(agentId)
                        ? "bg-purple-600 text-white"
                        : "bg-white text-gray-700 hover:bg-gray-100 border border-gray-300"
                    )}
                  >
                    {agentId}
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Results Summary */}
      <div className="flex items-center justify-between text-xs text-gray-600">
        <span>
          {filteredMessages.length} of {messages.length} messages
        </span>
        {hasActiveFilters && (
          <button
            onClick={clearFilters}
            className="text-blue-600 hover:text-blue-700 font-medium"
          >
            Clear all filters
          </button>
        )}
      </div>
    </div>
  );
}

/**
 * Format entity ID for display
 */
function formatEntityId(id: string): string {
  if (id.length > 20 && id.includes("-")) {
    return id.substring(0, 8);
  }
  return id;
}

/**
 * Compact search bar without advanced filters
 */
export function CompactContextSearch({
  messages,
  onFilteredResults,
  className,
}: {
  messages: ConversationMessage[];
  onFilteredResults?: (results: ConversationMessage[]) => void;
  className?: string;
}) {
  const [query, setQuery] = useState("");

  const filteredMessages = useMemo(() => {
    if (query.trim() === "") return messages;

    const lowerQuery = query.toLowerCase();
    return messages.filter(
      (msg) =>
        msg.content.toLowerCase().includes(lowerQuery) ||
        msg.semantic_summary?.toLowerCase().includes(lowerQuery) ||
        msg.extracted_entities?.projects.some((p) =>
          p.toLowerCase().includes(lowerQuery)
        ) ||
        msg.extracted_entities?.tasks.some((t) =>
          t.toLowerCase().includes(lowerQuery)
        )
    );
  }, [messages, query]);

  React.useEffect(() => {
    if (onFilteredResults) {
      onFilteredResults(filteredMessages);
    }
  }, [filteredMessages, onFilteredResults]);

  return (
    <div className={cn("relative", className)}>
      <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
      <input
        type="text"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        placeholder="Search conversations..."
        className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
      />
      {query && (
        <button
          onClick={() => setQuery("")}
          className="absolute right-3 top-1/2 transform -translate-y-1/2 p-1 hover:bg-gray-100 rounded transition-colors"
        >
          <X className="w-3 h-3 text-gray-500" />
        </button>
      )}
    </div>
  );
}
