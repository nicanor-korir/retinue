"use client";

import { useState, useEffect, useRef } from "react";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loader2, AlertCircle, CheckCircle2, Eye, EyeOff, Zap, Clock } from "lucide-react";
import { AgentActivityCard } from "@/components/realtime/agent-activity-card";
import { formatRelativeTime } from "@/lib/utils";
import { useWebSocket } from "@/hooks/use-websocket";

interface TaskActivityEvent {
  type: string;
  timestamp: string;
  agent_id: string;
  event_type: string;
  data: {
    activity_type?: string;
    progress_percentage?: number;
    description?: string;
    stage?: string;
    title?: string;
    [key: string]: any;
  };
}

interface TaskActivityStreamProps {
  taskId: string;
  taskTitle?: string;
  className?: string;
}

export function TaskActivityStream({ taskId, taskTitle, className }: TaskActivityStreamProps) {
  const [activities, setActivities] = useState<TaskActivityEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [showAll, setShowAll] = useState(false);
  const [eventCount, setEventCount] = useState(0);
  const scrollEndRef = useRef<HTMLDivElement>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // WebSocket connection using custom hook
  const { lastMessage, readyState, url } = useWebSocket(
    `ws://localhost:8000/ws/task/${taskId}`,
    {
      onOpen: () => {
        setIsConnected(true);
        console.log("Connected to task activity stream");
      },
      onClose: () => {
        setIsConnected(false);
        console.log("Disconnected from task activity stream");
      },
      onError: (event) => {
        console.error("WebSocket error:", event);
      },
    }
  );

  // Auto-scroll to latest activity
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [activities]);

  // Handle incoming WebSocket messages
  useEffect(() => {
    if (lastMessage) {
      try {
        const event = typeof lastMessage === "string" ? JSON.parse(lastMessage) : lastMessage;

        if (!isPaused) {
          setActivities((prev) => {
            // Keep last 50 events to avoid memory issues
            const updated = [...prev, event].slice(-50);
            return updated;
          });
          setEventCount((prev) => prev + 1);
        }
      } catch (error) {
        console.error("Error parsing WebSocket message:", error);
      }
    }
  }, [lastMessage, isPaused]);

  const displayedActivities = showAll ? activities : activities.slice(-10);

  return (
    <Card className={className}>
      <CardHeader className="space-y-2">
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2">
              <CardTitle>Agent Activity Stream</CardTitle>
              <Badge
                variant={isConnected ? "default" : "secondary"}
                className="ml-2"
              >
                {isConnected ? (
                  <>
                    <Zap className="h-3 w-3 mr-1 animate-pulse" />
                    Live
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-3 w-3 mr-1" />
                    Connecting...
                  </>
                )}
              </Badge>
            </div>
            <CardDescription>
              Real-time agent activities and execution status
            </CardDescription>
          </div>

          <div className="flex items-center space-x-2">
            {eventCount > 0 && (
              <Badge variant="outline" className="text-xs">
                {eventCount} events
              </Badge>
            )}
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setIsPaused(!isPaused)}
              title={isPaused ? "Resume" : "Pause"}
            >
              {isPaused ? (
                <AlertCircle className="h-4 w-4" />
              ) : (
                <Zap className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* Activity List */}
        <div className="space-y-2">
          {displayedActivities.length === 0 ? (
            <div className="flex items-center justify-center py-8 text-muted-foreground">
              <div className="text-center">
                {isConnected ? (
                  <>
                    <Loader2 className="h-8 w-8 mx-auto mb-2 animate-spin" />
                    <p className="text-sm">Waiting for agent activity...</p>
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-8 w-8 mx-auto mb-2" />
                    <p className="text-sm">Connecting to activity stream...</p>
                  </>
                )}
              </div>
            </div>
          ) : (
            <div className="space-y-2 max-h-96 overflow-y-auto pr-4">
              {displayedActivities.map((activity, idx) => (
                <ActivityEventItem
                  key={`${activity.timestamp}-${idx}`}
                  event={activity}
                />
              ))}
              <div ref={messagesEndRef} />
            </div>
          )}
        </div>

        {/* Show More / View All */}
        {activities.length > 10 && (
          <div className="flex items-center justify-between pt-4 border-t">
            <p className="text-xs text-muted-foreground">
              Showing {displayedActivities.length} of {activities.length} events
            </p>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAll(!showAll)}
            >
              {showAll ? "Show Recent" : `View All (${activities.length})`}
            </Button>
          </div>
        )}

        {/* Controls */}
        <div className="flex items-center justify-between pt-2 border-t text-xs text-muted-foreground">
          <div className="flex items-center space-x-2">
            <Clock className="h-3 w-3" />
            <span>Last update: {activities.length > 0 ? formatRelativeTime(activities[activities.length - 1].timestamp) : "—"}</span>
          </div>
          <Button
            variant="ghost"
            size="sm"
            className="text-xs h-7"
            onClick={() => setActivities([])}
          >
            Clear
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

interface ActivityEventItemProps {
  event: TaskActivityEvent;
}

function ActivityEventItem({ event }: ActivityEventItemProps) {
  const [expanded, setExpanded] = useState(false);

  const getEventIcon = (type: string) => {
    switch (type) {
      case "activity_created":
      case "activity_progress":
        return <Zap className="h-4 w-4 text-blue-500" />;
      case "activity_complete":
        return <CheckCircle2 className="h-4 w-4 text-green-600" />;
      case "thought_recorded":
        return <Eye className="h-4 w-4 text-purple-500" />;
      case "llm_interaction":
        return <Loader2 className="h-4 w-4 text-amber-500 animate-spin" />;
      default:
        return <Zap className="h-4 w-4 text-gray-400" />;
    }
  };

  const getEventBadgeColor = (type: string): "default" | "secondary" | "success" | "warning" | "destructive" | "outline" => {
    switch (type) {
      case "activity_complete":
      case "task_rag_indexed":
        return "success";
      case "activity_progress":
      case "task_rag_indexing_started":
        return "default";
      case "thought_recorded":
      case "llm_interaction":
        return "secondary";
      default:
        return "outline";
    }
  };

  // Get summary for the event
  const getSummary = (): string => {
    const data = event.data;
    switch (event.event_type) {
      case "activity_created":
        return `Started: ${data.description || data.activity_type || "Task"}`;
      case "activity_progress":
        return `Progress: ${data.progress_percentage || 0}% - ${data.stage || "Processing"}`;
      case "activity_complete":
        return "Activity completed";
      case "thought_recorded":
        return "Agent reasoning captured";
      case "task_rag_indexing_started":
        return `Indexing: ${data.title || "Task"}`;
      case "task_rag_indexed":
        return `Indexed with score: ${data.similarity_score || "N/A"}%`;
      case "llm_interaction":
        return `LLM Call: ${data.model || "Unknown"} (${data.tokens || 0} tokens)`;
      default:
        return event.event_type.replace(/_/g, " ");
    }
  };

  return (
    <div className="rounded-lg border bg-card p-3 hover:bg-accent/50 transition-colors">
      <div
        className="flex items-center justify-between cursor-pointer"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex items-center space-x-2 flex-1 min-w-0">
          {getEventIcon(event.event_type)}
          <div className="flex-1 min-w-0">
            <p className="text-sm font-medium truncate">
              {getSummary()}
            </p>
            <div className="flex items-center space-x-2 mt-1">
              <Badge variant="outline" className="text-xs">
                {event.agent_id}
              </Badge>
              <Badge
                variant={getEventBadgeColor(event.event_type)}
                className="text-xs"
              >
                {event.event_type.replace(/_/g, " ")}
              </Badge>
              <span className="text-xs text-muted-foreground">
                {formatRelativeTime(event.timestamp)}
              </span>
            </div>
          </div>
        </div>
        {Object.keys(event.data).length > 0 && (
          expanded ? (
            <EyeOff className="h-4 w-4 text-muted-foreground ml-2 flex-shrink-0" />
          ) : (
            <Eye className="h-4 w-4 text-muted-foreground ml-2 flex-shrink-0" />
          )
        )}
      </div>

      {/* Expanded Details */}
      {expanded && Object.keys(event.data).length > 0 && (
        <div className="mt-3 pt-3 border-t bg-muted/30 rounded p-2">
          <dl className="space-y-2 text-xs">
            {Object.entries(event.data).map(([key, value]) => (
              <div key={key} className="grid grid-cols-3 gap-2">
                <dt className="font-medium text-muted-foreground">{key}:</dt>
                <dd className="col-span-2 break-words font-mono text-foreground">
                  {typeof value === "object" ? JSON.stringify(value) : String(value)}
                </dd>
              </div>
            ))}
          </dl>
        </div>
      )}
    </div>
  );
}
