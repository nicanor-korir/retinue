"use client";

import { useState, useMemo, useCallback } from "react";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Search, X, Users } from "lucide-react";
import { Button } from "@/components/ui/button";

export interface AgentOption {
  id: string;
  name: string;
  role: string;
  description: string;
  department: string;
  color: string;
  icon: React.ReactNode;
  isAvailable?: boolean;
  specializations?: string[];
}

interface AgentSelectorProps {
  agents: AgentOption[];
  selectedAgents: string[];
  onSelectionChange: (agentIds: string[]) => void;
  maxSelectable?: number;
  searchPlaceholder?: string;
  showDepartmentFilter?: boolean;
}

export function AgentSelector({
  agents,
  selectedAgents,
  onSelectionChange,
  maxSelectable,
  searchPlaceholder = "Search agents by name, role, or department...",
  showDepartmentFilter = true,
}: AgentSelectorProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDepartment, setSelectedDepartment] = useState<string | null>(null);

  // Get unique departments
  const departments = useMemo(() => {
    const depts = new Set(agents.map((a) => a.department));
    return Array.from(depts).sort();
  }, [agents]);

  // Filter agents based on search and department
  const filteredAgents = useMemo(() => {
    return agents.filter((agent) => {
      // Department filter
      if (selectedDepartment && agent.department !== selectedDepartment) {
        return false;
      }

      // Search filter
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        return (
          agent.name.toLowerCase().includes(query) ||
          agent.role.toLowerCase().includes(query) ||
          agent.department.toLowerCase().includes(query) ||
          agent.description.toLowerCase().includes(query) ||
          agent.specializations?.some((s) => s.toLowerCase().includes(query))
        );
      }

      return true;
    });
  }, [agents, searchQuery, selectedDepartment]);

  const handleToggleAgent = useCallback(
    (agentId: string) => {
      const agent = agents.find((a) => a.id === agentId);
      if (!agent?.isAvailable) return;

      const newSelected = selectedAgents.includes(agentId)
        ? selectedAgents.filter((id) => id !== agentId)
        : maxSelectable && selectedAgents.length >= maxSelectable
          ? selectedAgents
          : [...selectedAgents, agentId];

      onSelectionChange(newSelected);
    },
    [selectedAgents, agents, maxSelectable, onSelectionChange]
  );

  const handleRemoveAgent = useCallback(
    (agentId: string) => {
      onSelectionChange(selectedAgents.filter((id) => id !== agentId));
    },
    [selectedAgents, onSelectionChange]
  );

  const selectedAgentObjects = selectedAgents
    .map((id) => agents.find((a) => a.id === id))
    .filter(Boolean) as AgentOption[];

  const isMaxReached = !!(maxSelectable && selectedAgents.length >= maxSelectable);

  return (
    <div className="space-y-4">
      {/* Selected Agents Display */}
      {selectedAgents.length > 0 && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">
            Selected Agents ({selectedAgents.length})
          </p>
          <div className="flex flex-wrap gap-2">
            {selectedAgentObjects.map((agent) => (
              <div
                key={agent.id}
                className="flex items-center gap-2 bg-primary/10 border border-primary/30 rounded-full px-3 py-1.5"
              >
                <div className={`inline-block p-1 rounded bg-gradient-to-br ${agent.color}`}>
                  {agent.icon}
                </div>
                <div>
                  <p className="text-xs font-medium">{agent.name}</p>
                  <p className="text-xs text-muted-foreground">{agent.role}</p>
                </div>
                <button
                  onClick={() => handleRemoveAgent(agent.id)}
                  className="ml-1 text-muted-foreground hover:text-foreground transition-colors"
                >
                  <X className="h-3 w-3" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Search Input */}
      <div className="relative">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          type="text"
          placeholder={searchPlaceholder}
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-10"
        />
      </div>

      {/* Department Filter */}
      {showDepartmentFilter && departments.length > 1 && (
        <div className="space-y-2">
          <p className="text-sm font-medium text-muted-foreground">Filter by Department</p>
          <div className="flex flex-wrap gap-2">
            <Button
              type="button"
              variant={selectedDepartment === null ? "default" : "outline"}
              size="sm"
              onClick={(e) => {
                e.preventDefault();
                setSelectedDepartment(null);
              }}
              className="rounded-full"
            >
              All Departments
            </Button>
            {departments.map((dept) => (
              <Button
                key={dept}
                type="button"
                variant={selectedDepartment === dept ? "default" : "outline"}
                size="sm"
                onClick={(e) => {
                  e.preventDefault();
                  setSelectedDepartment(dept);
                }}
                className="rounded-full capitalize"
              >
                {dept}
              </Button>
            ))}
          </div>
        </div>
      )}

      {/* Agents Grid */}
      <div className="space-y-2">
        <p className="text-sm font-medium text-muted-foreground">
          Available Agents ({filteredAgents.length})
          {maxSelectable && (
            <span className="text-xs">
              {" "}
              - Select up to {maxSelectable}
            </span>
          )}
        </p>

        {filteredAgents.length === 0 ? (
          <div className="text-center py-8 text-muted-foreground">
            <Users className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p>No agents found matching your criteria</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 max-h-96 overflow-y-auto p-1">
            {filteredAgents.map((agent) => {
              const isSelected = selectedAgents.includes(agent.id);
              const isDisabled = !agent.isAvailable || (isMaxReached && !isSelected);

              return (
                <button
                  key={agent.id}
                  onClick={() => handleToggleAgent(agent.id)}
                  disabled={isDisabled}
                  className={`p-3 rounded-lg border-2 transition-all text-left group ${
                    isSelected
                      ? "border-primary bg-primary/10 shadow-md"
                      : "border-border/50 hover:border-primary/50 disabled:opacity-50 disabled:cursor-not-allowed"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div
                      className={`inline-block p-2 rounded-lg text-white flex-shrink-0 group-hover:shadow-lg transition-all ${
                        isSelected
                          ? `bg-gradient-to-br ${agent.color} shadow-lg scale-110`
                          : `bg-gradient-to-br ${agent.color} opacity-75 group-hover:opacity-100`
                      }`}
                    >
                      {agent.icon}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-semibold text-foreground">{agent.name}</p>
                      <p className="text-xs text-muted-foreground">{agent.role}</p>
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">
                        {agent.description}
                      </p>
                      {agent.specializations && agent.specializations.length > 0 && (
                        <div className="mt-2 flex flex-wrap gap-1">
                          {agent.specializations.slice(0, 2).map((spec) => (
                            <Badge key={spec} variant="secondary" className="text-xs">
                              {spec}
                            </Badge>
                          ))}
                          {agent.specializations.length > 2 && (
                            <Badge variant="secondary" className="text-xs">
                              +{agent.specializations.length - 2}
                            </Badge>
                          )}
                        </div>
                      )}
                      {isSelected && (
                        <div className="mt-2 text-xs text-primary font-semibold flex items-center gap-1">
                          <span>✓ Selected</span>
                        </div>
                      )}
                    </div>
                  </div>
                </button>
              );
            })}
          </div>
        )}
      </div>

      {maxSelectable && isMaxReached && (
        <p className="text-xs text-amber-600 text-center">
          Maximum {maxSelectable} agents selected
        </p>
      )}
    </div>
  );
}
