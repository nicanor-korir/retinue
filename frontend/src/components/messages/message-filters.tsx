"use client";

import { useState } from "react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Search, X, Filter, Calendar } from "lucide-react";
import { MessageType, Priority } from "@/types/api";
import { Card, CardContent } from "@/components/ui/card";

interface MessageFiltersProps {
  onFilterChange: (filters: MessageFilterState) => void;
  agentIds: string[];
}

export interface MessageFilterState {
  search: string;
  messageType: MessageType | "all";
  priority: Priority | "all";
  status: "all" | "read" | "unread" | "requires_action";
  agentFrom: string;
  agentTo: string;
  dateRange: "all" | "today" | "week" | "month";
}

const initialFilters: MessageFilterState = {
  search: "",
  messageType: "all",
  priority: "all",
  status: "all",
  agentFrom: "",
  agentTo: "",
  dateRange: "all",
};

export function MessageFilters({ onFilterChange, agentIds }: MessageFiltersProps) {
  const [filters, setFilters] = useState<MessageFilterState>(initialFilters);
  const [isExpanded, setIsExpanded] = useState(false);

  const updateFilter = (key: keyof MessageFilterState, value: any) => {
    const newFilters = { ...filters, [key]: value };
    setFilters(newFilters);
    onFilterChange(newFilters);
  };

  const resetFilters = () => {
    setFilters(initialFilters);
    onFilterChange(initialFilters);
  };

  const activeFilterCount = Object.entries(filters).filter(([key, value]) => {
    if (key === "search") return value !== "";
    return value !== "all" && value !== "";
  }).length;

  return (
    <Card>
      <CardContent className="p-4 space-y-4">
        {/* Search Bar */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search messages by content, agent, or metadata..."
              value={filters.search}
              onChange={(e) => updateFilter("search", e.target.value)}
              className="pl-10"
            />
          </div>
          <Button
            variant="outline"
            size="icon"
            onClick={() => setIsExpanded(!isExpanded)}
            className="relative"
          >
            <Filter className="h-4 w-4" />
            {activeFilterCount > 0 && (
              <Badge
                variant="destructive"
                className="absolute -top-2 -right-2 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
              >
                {activeFilterCount}
              </Badge>
            )}
          </Button>
          {activeFilterCount > 0 && (
            <Button variant="ghost" size="sm" onClick={resetFilters}>
              <X className="h-4 w-4 mr-1" />
              Clear
            </Button>
          )}
        </div>

        {/* Expanded Filters */}
        {isExpanded && (
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <label className="text-sm font-medium mb-2 block">Message Type</label>
              <Select
                value={filters.messageType}
                onValueChange={(value: string) => updateFilter("messageType", value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  <SelectItem value={MessageType.INFO}>Info</SelectItem>
                  <SelectItem value={MessageType.TASK_ASSIGNMENT}>Task Assignment</SelectItem>
                  <SelectItem value={MessageType.APPROVAL}>Approval</SelectItem>
                  <SelectItem value={MessageType.ALERT}>Alert</SelectItem>
                  <SelectItem value={MessageType.STATUS_UPDATE}>Status Update</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Priority</label>
              <Select
                value={filters.priority}
                onValueChange={(value: string) => updateFilter("priority", value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Priorities</SelectItem>
                  <SelectItem value={Priority.CRITICAL}>Critical</SelectItem>
                  <SelectItem value={Priority.HIGH}>High</SelectItem>
                  <SelectItem value={Priority.MEDIUM}>Medium</SelectItem>
                  <SelectItem value={Priority.LOW}>Low</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Status</label>
              <Select
                value={filters.status}
                onValueChange={(value: string) => updateFilter("status", value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  <SelectItem value="unread">Unread</SelectItem>
                  <SelectItem value="read">Read</SelectItem>
                  <SelectItem value="requires_action">Requires Action</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">From Agent</label>
              <Select
                value={filters.agentFrom}
                onValueChange={(value: string) => updateFilter("agentFrom", value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Any agent" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Any agent</SelectItem>
                  {agentIds.map((agentId) => (
                    <SelectItem key={agentId} value={agentId}>
                      {agentId}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">To Agent</label>
              <Select
                value={filters.agentTo}
                onValueChange={(value: string) => updateFilter("agentTo", value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Any agent" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">Any agent</SelectItem>
                  {agentIds.map((agentId) => (
                    <SelectItem key={agentId} value={agentId}>
                      {agentId}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">
                <Calendar className="inline h-4 w-4 mr-1" />
                Date Range
              </label>
              <Select
                value={filters.dateRange}
                onValueChange={(value: string) => updateFilter("dateRange", value)}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Time</SelectItem>
                  <SelectItem value="today">Today</SelectItem>
                  <SelectItem value="week">This Week</SelectItem>
                  <SelectItem value="month">This Month</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
