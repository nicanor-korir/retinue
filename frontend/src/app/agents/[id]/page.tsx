"use client";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";
import { AgentActivityCard } from "@/components/realtime/agent-activity-card";
import { useAgentEventStream } from "@/hooks/useWebSocket";
import { AgentActivity, AgentThought, LLMInteraction } from "@/types/events";
import {
  ArrowLeft,
  Activity,
  Brain,
  MessageSquare,
  Wifi,
  WifiOff,
  Loader2,
  CheckCircle2,
  Clock,
  MessageSquare as FeedbackIcon
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState, useRef } from "react";
import { useParams } from "next/navigation";
import { useAgentActivity } from "@/hooks/useApi";
import { formatRelativeTime } from "@/lib/utils";
import { FeedbackDialog } from '@/components/feedback/feedback-dialog';
import { FeedbackDisplay } from '@/components/feedback/feedback-display';
import { LearningDashboard } from '@/components/feedback/learning-dashboard';
import { useAgentFeedback } from '@/hooks/useFeedback';
import { ChatWidget } from '@/components/chat/ChatWidget';
import { ConversationType } from '@/types/conversation';

interface ActivityWithExtras extends AgentActivity {
  thoughts?: string[];
  llmInteraction?: LLMInteraction;
  streamingResponse?: string;
}

const AGENT_INFO: Record<string, { name: string; role: string; description: string }> = {
  "ceo_001": {
    name: "CEO Agent",
    role: "Chief Executive Officer",
    description: "Strategic orchestrator making high-level decisions and project approvals",
  },
  "cto_001": {
    name: "CTO Agent",
    role: "Chief Technology Officer",
    description: "Technical oversight, architecture decisions, and code review",
  },
  "pm_001": {
    name: "PM Agent",
    role: "Project Manager",
    description: "Task coordination, breakdown, and progress monitoring",
  },
  "hr_001": {
    name: "HR Agent",
    role: "HR Manager",
    description: "Agent health monitoring, intervention, and escalation",
  },
  "backend_001": {
    name: "Backend Agent",
    role: "Senior Backend Engineer",
    description: "Python/FastAPI code generation and backend development",
  },
  "frontend_001": {
    name: "Frontend Agent",
    role: "Senior Frontend Engineer",
    description: "React/Next.js code generation and UI implementation",
  },
  "designer_001": {
    name: "Designer Agent",
    role: "Product Designer",
    description: "UI/UX specifications and design system creation",
  },
};

export default function AgentDetailPage() {
  const params = useParams();
  const agentId = params.id as string;
  const { isConnected, events, clearEvents, reconnect } = useAgentEventStream(agentId, true);
  const { data: agentHistory, isLoading: historyLoading } = useAgentActivity(agentId);
  const [activities, setActivities] = useState<ActivityWithExtras[]>([]);
  const [stats, setStats] = useState({
    totalActivities: 0,
    totalThoughts: 0,
    totalLLMCalls: 0,
  });
  const scrollRef = useRef<HTMLDivElement>(null);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const { feedback, fetchFeedback } = useAgentFeedback(agentId);
  const [systemLearnings, setSystemLearnings] = useState([]);

  const agentInfo = AGENT_INFO[agentId] || {
    name: agentId,
    role: "Unknown",
    description: "No description available",
  };

  // Fetch feedback on mount
  useEffect(() => {
    fetchFeedback();
  }, [agentId, fetchFeedback]);

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
              return prev.map((a) =>
                a.activity_id === activity.activity_id ? { ...a, ...activity } : a
              );
            } else {
              setStats((s) => ({ ...s, totalActivities: s.totalActivities + 1 }));
              return [activity, ...prev].slice(0, 50);
            }
          });
          break;

        case "llm_stream_chunk":
          const chunkData = event.data;
          setActivities((prev) =>
            prev.map((a) => {
              if (a.is_active) {
                const currentStream = a.streamingResponse || "";
                return { ...a, streamingResponse: currentStream + chunkData.chunk };
              }
              return a;
            })
          );
          break;

        case "thought_recorded":
          const thought: AgentThought = event.data;
          setStats((s) => ({ ...s, totalThoughts: s.totalThoughts + 1 }));
          setActivities((prev) =>
            prev.map((a) => {
              if (a.activity_id === thought.activity_id) {
                const thoughts = a.thoughts || [];
                return { ...a, thoughts: [thought.content, ...thoughts].slice(0, 5) };
              }
              return a;
            })
          );
          break;

        case "llm_interaction":
          const llm: LLMInteraction = event.data;
          setStats((s) => ({ ...s, totalLLMCalls: s.totalLLMCalls + 1 }));
          setActivities((prev) =>
            prev.map((a) => {
              if (a.activity_id === llm.activity_id) {
                return { ...a, llmInteraction: llm, streamingResponse: undefined };
              }
              return a;
            })
          );
          break;
      }
    });
  }, [events]);

  const activeActivities = activities.filter((a) => a.is_active);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Link href="/agents">
              <Button variant="ghost" size="sm">
                <ArrowLeft className="h-4 w-4 mr-2" />
                Back to Agents
              </Button>
            </Link>
            <div>
              <h1 className="text-3xl font-bold tracking-tight">{agentInfo.name}</h1>
              <p className="text-muted-foreground">{agentInfo.role}</p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            <Button
              size="sm"
              variant="outline"
              className="gap-2"
              onClick={() => setFeedbackOpen(true)}
            >
              <FeedbackIcon className="h-4 w-4" />
              Feedback
            </Button>
            <Badge variant={isConnected ? "success" : "destructive"} className="gap-2">
              {isConnected ? (
                <>
                  <Wifi className="h-3 w-3" />
                  Live
                </>
              ) : (
                <>
                  <WifiOff className="h-3 w-3" />
                  Disconnected
                </>
              )}
            </Badge>
            {!isConnected && (
              <Button size="sm" variant="outline" onClick={reconnect}>
                Reconnect
              </Button>
            )}
          </div>
        </div>

        {/* Agent Info */}
        <Card>
          <CardHeader>
            <CardTitle>Agent Information</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">{agentInfo.description}</p>
          </CardContent>
        </Card>

        {/* Chat with Agent */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <MessageSquare className="h-5 w-5 text-blue-500" />
              <span>Chat & Brainstorm</span>
            </CardTitle>
            <CardDescription>
              Have a conversation with {agentInfo.name} - ask questions, discuss ideas, or brainstorm solutions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ChatWidget
              agentId={agentId}
              conversationType={ConversationType.AGENT_CHAT}
              title={`Chat with ${agentInfo.name}`}
            />
          </CardContent>
        </Card>

        {/* Stats */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
                <Activity className="h-4 w-4 mr-2" />
                Active Now
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {activeActivities.length}
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Total Activities
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalActivities}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
                <Brain className="h-4 w-4 mr-2" />
                Thoughts
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalThoughts}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground flex items-center">
                <MessageSquare className="h-4 w-4 mr-2" />
                LLM Calls
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.totalLLMCalls}</div>
            </CardContent>
          </Card>
        </div>

        {/* Live Activity Stream */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="flex items-center space-x-2">
                  <Activity className="h-5 w-5 text-green-500" />
                  <span>Live Activity Stream</span>
                </CardTitle>
                <CardDescription>
                  Real-time updates as they happen
                </CardDescription>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={clearEvents}
                disabled={activities.length === 0}
              >
                Clear All
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            <ScrollArea className="h-[600px]" ref={scrollRef}>
              {activities.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-12 text-center">
                  {isConnected ? (
                    activeActivities.length === 0 ? (
                      <>
                        <Activity className="h-8 w-8 text-green-500 mb-3" />
                        <p className="text-muted-foreground">Agent is idle</p>
                        <p className="text-xs text-muted-foreground mt-1">
                          Waiting for new tasks to be assigned
                        </p>
                      </>
                    ) : (
                      <>
                        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground mb-3" />
                        <p className="text-muted-foreground">Loading agent activity...</p>
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
                      agentName={agentInfo.name}
                      streamingResponse={activity.streamingResponse}
                    />
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Agent History */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-blue-500" />
              <span>Activity History</span>
            </CardTitle>
            <CardDescription>
              Complete history of agent activities and decisions
            </CardDescription>
          </CardHeader>
          <CardContent>
            {historyLoading ? (
              <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
              </div>
            ) : agentHistory && agentHistory.length > 0 ? (
              <ScrollArea className="h-[500px]">
                <div className="space-y-4 pr-4">
                  {agentHistory.map((activity: any, idx: number) => (
                    <div
                      key={idx}
                      className="border rounded-lg p-4 space-y-2 hover:bg-accent/50 transition-colors"
                    >
                      {/* Activity Type & Time */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Badge variant="outline" className="text-xs">
                            {activity.type}
                          </Badge>
                          {activity.entity_type && (
                            <Badge variant="secondary" className="text-xs">
                              {activity.entity_type}
                            </Badge>
                          )}
                        </div>
                        <span className="text-xs text-muted-foreground">
                          {formatRelativeTime(activity.timestamp)}
                        </span>
                      </div>

                      {/* Action */}
                      <div>
                        <h4 className="font-medium text-sm">{activity.action}</h4>
                      </div>

                      {/* Details */}
                      {activity.details && (
                        <div className="text-xs text-muted-foreground bg-secondary/50 rounded p-2 mt-2">
                          <pre className="whitespace-pre-wrap font-mono">
                            {JSON.stringify(activity.details, null, 2)}
                          </pre>
                        </div>
                      )}

                      {/* Entity Info */}
                      {activity.entity_id && (
                        <div className="text-xs text-muted-foreground flex items-center mt-2">
                          <span className="font-mono bg-secondary px-2 py-1 rounded">
                            {activity.entity_id}
                          </span>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </ScrollArea>
            ) : (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <Activity className="h-8 w-8 text-muted-foreground mb-3" />
                <p className="text-muted-foreground">No activity history yet</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Activities will appear here as the agent works
                </p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Feedback Components Section */}
        <div className="space-y-6">
          {/* Feedback Dialog */}
          <FeedbackDialog
            entityType="agent"
            entityId={agentId}
            entityName={agentInfo.name}
            isOpen={feedbackOpen}
            onOpenChange={setFeedbackOpen}
            onFeedbackSubmitted={() => {
              fetchFeedback();
            }}
          />

          {/* Learning Dashboard */}
          <LearningDashboard
            systemLearnings={systemLearnings}
            agentId={agentId}
          />

          {/* Feedback Display */}
          <FeedbackDisplay
            entityType="agent"
            entityId={agentId}
          />
        </div>
      </div>
    </DashboardLayout>
  );
}
