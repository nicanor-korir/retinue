"use client";

import { useState, useMemo } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { MessageCard } from "@/components/messages/message-card";
import { MessageDetailPanel } from "@/components/messages/message-detail-panel";
import { MessageFilters, MessageFilterState } from "@/components/messages/message-filters";
import { MessageMetrics } from "@/components/messages/message-metrics";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useMessages } from "@/hooks/useApi";
import { Message } from "@/types/api";
import { MessageSquare, RefreshCw, Download, Inbox } from "lucide-react";

export default function MessagesPage() {
  const { data: messages, isLoading, refetch } = useMessages({ limit: 100 });
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const [filters, setFilters] = useState<MessageFilterState>({
    search: "",
    messageType: "all",
    priority: "all",
    status: "all",
    agentFrom: "",
    agentTo: "",
    dateRange: "all",
  });

  // Get unique agent IDs for filter dropdowns
  const uniqueAgentIds = useMemo(() => {
    if (!messages) return [];
    const agentIds = new Set<string>();
    messages.forEach((msg) => {
      agentIds.add(msg.from_agent_id);
      agentIds.add(msg.to_agent_id);
    });
    return Array.from(agentIds).sort();
  }, [messages]);

  // Apply filters to messages
  const filteredMessages = useMemo(() => {
    if (!messages) return [];

    return messages.filter((message) => {
      // Search filter
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        const matchesContent = message.content.toLowerCase().includes(searchLower);
        const matchesFrom = message.from_agent_id.toLowerCase().includes(searchLower);
        const matchesTo = message.to_agent_id.toLowerCase().includes(searchLower);
        const matchesMetadata = JSON.stringify(message.metadata)
          .toLowerCase()
          .includes(searchLower);

        if (!matchesContent && !matchesFrom && !matchesTo && !matchesMetadata) {
          return false;
        }
      }

      // Message type filter
      if (filters.messageType !== "all" && message.message_type !== filters.messageType) {
        return false;
      }

      // Priority filter
      if (filters.priority !== "all" && message.priority !== filters.priority) {
        return false;
      }

      // Status filter
      if (filters.status === "read" && !message.read) return false;
      if (filters.status === "unread" && message.read) return false;
      if (filters.status === "requires_action") {
        const requiresAction =
          message.message_type === "approval" || message.message_type === "alert";
        if (!requiresAction) return false;
      }

      // Agent from filter
      if (filters.agentFrom && message.from_agent_id !== filters.agentFrom) {
        return false;
      }

      // Agent to filter
      if (filters.agentTo && message.to_agent_id !== filters.agentTo) {
        return false;
      }

      // Date range filter
      if (filters.dateRange !== "all") {
        // Skip messages without a valid timestamp
        if (!message.created_at) return false;
        
        const messageDate = new Date(message.created_at);
        // Check if date is valid
        if (isNaN(messageDate.getTime())) return false;
        
        const now = new Date();

        if (filters.dateRange === "today") {
          const today = new Date();
          today.setHours(0, 0, 0, 0);
          if (messageDate < today) return false;
        } else if (filters.dateRange === "week") {
          const weekAgo = new Date(now.getTime() - 7 * 24 * 60 * 60 * 1000);
          if (messageDate < weekAgo) return false;
        } else if (filters.dateRange === "month") {
          const monthAgo = new Date(now.getTime() - 30 * 24 * 60 * 60 * 1000);
          if (messageDate < monthAgo) return false;
        }
      }

      return true;
    });
  }, [messages, filters]);

  const handleMarkAsRead = (messageId: string) => {
    // TODO: Implement API call to mark message as read
    console.log("Mark as read:", messageId);
  };

  const handleMarkAsResolved = (messageId: string) => {
    // TODO: Implement API call to mark message as resolved
    console.log("Mark as resolved:", messageId);
  };

  const handleReply = (messageId: string, content: string) => {
    // TODO: Implement API call to reply to message
    console.log("Reply to:", messageId, content);
  };

  const handleExport = () => {
    // TODO: Implement export functionality
    const dataStr = JSON.stringify(filteredMessages, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `messages-export-${new Date().toISOString()}.json`;
    link.click();
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-96">
          <div className="flex flex-col items-center gap-4">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
            <p className="text-sm text-muted-foreground">Loading messages...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Messages</h1>
            <p className="text-muted-foreground mt-1">
              Communication messages between agents
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => refetch()}
              className="gap-2"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={handleExport}
              className="gap-2"
              disabled={filteredMessages.length === 0}
            >
              <Download className="h-4 w-4" />
              Export
            </Button>
          </div>
        </div>

        {/* Metrics Dashboard */}
        {messages && messages.length > 0 && <MessageMetrics messages={filteredMessages} />}

        {/* Filters */}
        <MessageFilters onFilterChange={setFilters} agentIds={uniqueAgentIds} />

        {/* Results Count */}
        {filteredMessages.length > 0 && (
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              Showing {filteredMessages.length} of {messages?.length || 0} messages
            </span>
            {filters.search && (
              <span>
                Search results for: <strong>{filters.search}</strong>
              </span>
            )}
          </div>
        )}

        {/* Messages List */}
        <div className="space-y-3">
          {filteredMessages.length > 0 ? (
            filteredMessages.map((message) => (
              <MessageCard
                key={message.message_id}
                message={message}
                onClick={() => setSelectedMessage(message)}
                onMarkAsRead={handleMarkAsRead}
              />
            ))
          ) : messages && messages.length > 0 ? (
            // No results after filtering
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <Inbox className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No messages match your filters</h3>
                <p className="text-muted-foreground text-center max-w-md">
                  Try adjusting your search criteria or filters to find what you're looking for
                </p>
              </CardContent>
            </Card>
          ) : (
            // No messages at all
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-16">
                <MessageSquare className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No messages yet</h3>
                <p className="text-muted-foreground text-center max-w-md">
                  Messages will appear here as agents communicate with each other
                </p>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Load More Button (if needed) */}
        {filteredMessages.length > 50 && (
          <div className="flex justify-center">
            <Button variant="outline" size="sm">
              Load More Messages
            </Button>
          </div>
        )}
      </div>

      {/* Message Detail Panel */}
      {selectedMessage && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40"
            onClick={() => setSelectedMessage(null)}
          />
          {/* Panel */}
          <MessageDetailPanel
            message={selectedMessage}
            onClose={() => setSelectedMessage(null)}
            onMarkAsRead={handleMarkAsRead}
            onMarkAsResolved={handleMarkAsResolved}
            onReply={handleReply}
          />
        </>
      )}
    </DashboardLayout>
  );
}
