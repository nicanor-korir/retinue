"use client";

import { useEffect, useState, useRef } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AgentActivityCard } from "./agent-activity-card";
import { useProjectEventStream } from "@/hooks/useWebSocket";
import { AgentActivity, AgentThought, LLMInteraction, AgentHandoff } from "@/types/events";
import { Wifi, WifiOff, Activity, ArrowRight, Loader2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface LiveStreamFeedProps {
  projectId: string;
  className?: string;
}

interface ActivityWithExtras extends AgentActivity {
  thoughts?: string[];
  llmInteraction?: LLMInteraction;
  streamingResponse?: string;
}

export function LiveStreamFeed({ projectId, className }: LiveStreamFeedProps) {
  const { isConnected, events, clearEvents, reconnect } = useProjectEventStream(projectId, true);
  const [activities, setActivities] = useState<ActivityWithExtras[]>([]);
  const [handoffs, setHandoffs] = useState<AgentHandoff[]>([]);
  const [autoScroll, setAutoScroll] = useState(true);
  const scrollRef = useRef<HTMLDivElement>(null);

  // Process WebSocket events
  useEffect(() => {
    events.forEach((event) => {
      switch (event.type) {
        case "activity_created":
        case "activity_updated":
          const activity: AgentActivity = event.data;
          setActivities((prev) => {
            const exists = prev.find((a) => a.activity_id === activity.activity_id);
            if (exists) {
              // Update existing
              return prev.map((a) =>
                a.activity_id === activity.activity_id ? { ...a, ...activity } : a
              );
            } else {
              // Add new
              return [activity, ...prev].slice(0, 50); // Keep last 50
            }
          });
          break;

        case "llm_stream_chunk":
          // Handle streaming LLM response chunks
          const chunkData = event.data;
          setActivities((prev) =>
            prev.map((a) => {
              if (a.agent_id === chunkData.agent_id && a.is_active) {
                // Append chunk to streaming response
                const currentStream = a.streamingResponse || "";
                return { ...a, streamingResponse: currentStream + chunkData.chunk };
              }
              return a;
            })
          );
          break;

        case "thought_recorded":
          const thought: AgentThought = event.data;
          setActivities((prev) =>
            prev.map((a) => {
              if (a.activity_id === thought.activity_id || a.agent_id === thought.agent_id) {
                const thoughts = a.thoughts || [];
                return { ...a, thoughts: [thought.content, ...thoughts].slice(0, 3) };
              }
              return a;
            })
          );
          break;

        case "llm_interaction":
          const llm: LLMInteraction = event.data;
          setActivities((prev) =>
            prev.map((a) => {
              if (a.activity_id === llm.activity_id || a.agent_id === llm.agent_id) {
                // Clear streaming response when LLM interaction completes
                return { ...a, llmInteraction: llm, streamingResponse: undefined };
              }
              return a;
            })
          );
          break;

        case "agent_handoff":
          const handoff: AgentHandoff = event.data;
          setHandoffs((prev) => [handoff, ...prev].slice(0, 10));
          break;
      }
    });
  }, [events]);

  // Auto-scroll to bottom when new activities arrive
  useEffect(() => {
    if (autoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = 0;
    }
  }, [activities, autoScroll]);

  // Active agents
  const activeAgents = activities.filter((a) => a.is_active);
  const uniqueActiveAgents = Array.from(new Set(activeAgents.map((a) => a.agent_id)));

  return (
    <Card className={className}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center space-x-2">
              <Activity className="h-5 w-5" />
              <span>Live Activity Stream</span>
              {isConnected ? (
                <Wifi className="h-4 w-4 text-green-500" />
              ) : (
                <WifiOff className="h-4 w-4 text-red-500" />
              )}
            </CardTitle>
            <CardDescription>
              Real-time updates • {uniqueActiveAgents.length} agent{uniqueActiveAgents.length !== 1 ? "s" : ""} active
            </CardDescription>
          </div>
          <div className="flex items-center space-x-2">
            <Badge variant={isConnected ? "success" : "destructive"}>
              {isConnected ? "Connected" : "Disconnected"}
            </Badge>
            {!isConnected && (
              <Button size="sm" variant="outline" onClick={reconnect}>
                Reconnect
              </Button>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Recent Handoffs */}
        {handoffs.length > 0 && (
          <div className="mb-4 space-y-2">
            <h4 className="text-sm font-semibold text-muted-foreground">Recent Handoffs</h4>
            {handoffs.slice(0, 3).map((handoff) => (
              <div
                key={handoff.handoff_id}
                className="flex items-center space-x-2 p-2 bg-secondary/50 rounded text-sm"
              >
                <span className="font-medium">{handoff.from_agent_id}</span>
                <ArrowRight className="h-4 w-4 text-muted-foreground" />
                <span className="font-medium">{handoff.to_agent_id}</span>
                <span className="text-muted-foreground">•</span>
                <span className="text-muted-foreground flex-1 truncate">{handoff.message}</span>
                <Badge variant="outline" className="text-xs">
                  {handoff.status}
                </Badge>
              </div>
            ))}
          </div>
        )}

        {/* Activity Feed */}
        <ScrollArea className="h-[600px]" ref={scrollRef}>
          {activities.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              {isConnected ? (
                uniqueActiveAgents.length === 0 ? (
                  <>
                    <Activity className="h-8 w-8 text-green-500 mb-3" />
                    <p className="text-muted-foreground">No active agent work</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      All tasks completed or agents idle
                    </p>
                  </>
                ) : (
                  <>
                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground mb-3" />
                    <p className="text-muted-foreground">Waiting for agent activity...</p>
                    <p className="text-xs text-muted-foreground mt-1">
                      Agents will appear here as they start working
                    </p>
                  </>
                )
              ) : (
                <>
                  <WifiOff className="h-8 w-8 text-muted-foreground mb-3" />
                  <p className="text-muted-foreground">Not connected to live stream</p>
                  <Button size="sm" variant="outline" onClick={reconnect} className="mt-3">
                    Try to Reconnect
                  </Button>
                </>
              )}
            </div>
          ) : (
            <div className="space-y-4 pr-4">
              {activities.map((activity) => (
                <AgentActivityCard
                  key={activity.activity_id}
                  activity={activity}
                  llmInteraction={activity.llmInteraction}
                  thoughts={activity.thoughts}
                  agentName={activity.agent_id}
                  streamingResponse={activity.streamingResponse}
                />
              ))}
            </div>
          )}
        </ScrollArea>

        {/* Controls */}
        <div className="mt-4 flex items-center justify-between text-sm">
          <div className="flex items-center space-x-4">
            <label className="flex items-center space-x-2 cursor-pointer">
              <input
                type="checkbox"
                checked={autoScroll}
                onChange={(e) => setAutoScroll(e.target.checked)}
                className="rounded"
              />
              <span className="text-muted-foreground">Auto-scroll</span>
            </label>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearEvents}
              disabled={activities.length === 0}
            >
              Clear All
            </Button>
          </div>
          <span className="text-muted-foreground">
            {activities.length} activit{activities.length !== 1 ? "ies" : "y"}
          </span>
        </div>
      </CardContent>
    </Card>
  );
}
