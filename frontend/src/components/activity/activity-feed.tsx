"use client";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Activity,
  MessageSquare,
  Lightbulb,
  FileEdit,
  CheckCircle2,
  AlertCircle,
  Clock,
  Zap,
  User,
  UserCircle
} from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";

interface ActivityItem {
  type: "audit" | "message" | "decision" | "human_input";
  timestamp: string;
  agent_id?: string;
  action?: string;
  entity_type?: string;
  entity_id?: string;
  details?: any;
  from_agent?: string;
  to_agent?: string;
  message_type?: string;
  content?: string;
  priority?: string;
  decision_type?: string;
  question?: string;
  decision?: string;
  rationale?: string;
  interaction_type?: string;
  request?: string;
  response?: string;
  status?: string;
  target_agent?: string;
}

interface ActivityFeedProps {
  activities: ActivityItem[];
  isLoading?: boolean;
  title?: string;
  description?: string;
}

function getActivityIcon(activity: ActivityItem) {
  switch (activity.type) {
    case "message":
      return <MessageSquare className="h-4 w-4" />;
    case "decision":
      return <Lightbulb className="h-4 w-4" />;
    case "human_input":
      return <UserCircle className="h-4 w-4" />;
    case "audit":
      if (activity.action?.includes("status")) {
        return <Activity className="h-4 w-4" />;
      }
      if (activity.action?.includes("created")) {
        return <Zap className="h-4 w-4" />;
      }
      if (activity.action?.includes("updated")) {
        return <FileEdit className="h-4 w-4" />;
      }
      if (activity.action?.includes("completed")) {
        return <CheckCircle2 className="h-4 w-4" />;
      }
      return <Activity className="h-4 w-4" />;
    default:
      return <Activity className="h-4 w-4" />;
  }
}

function getActivityColor(activity: ActivityItem) {
  switch (activity.type) {
    case "message":
      if (activity.priority === "high" || activity.priority === "critical") {
        return "text-red-500 bg-red-50 dark:bg-red-950";
      }
      return "text-blue-500 bg-blue-50 dark:bg-blue-950";
    case "decision":
      return "text-purple-500 bg-purple-50 dark:bg-purple-950";
    case "human_input":
      return "text-orange-500 bg-orange-50 dark:bg-orange-950";
    case "audit":
      if (activity.action?.includes("completed")) {
        return "text-green-500 bg-green-50 dark:bg-green-950";
      }
      if (activity.action?.includes("failed") || activity.action?.includes("error")) {
        return "text-red-500 bg-red-50 dark:bg-red-950";
      }
      return "text-gray-500 bg-gray-50 dark:bg-gray-950";
    default:
      return "text-gray-500 bg-gray-50 dark:bg-gray-950";
  }
}

function formatActivityTitle(activity: ActivityItem): string {
  switch (activity.type) {
    case "message":
      return `Message from ${activity.from_agent} to ${activity.to_agent}`;
    case "decision":
      return `Decision: ${activity.decision_type}`;
    case "human_input":
      return `Human Input ${activity.target_agent ? `to ${activity.target_agent}` : ""}`;
    case "audit":
      return activity.action?.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase()) || "Activity";
    default:
      return "Activity";
  }
}

function formatActivityDetails(activity: ActivityItem): React.ReactNode {
  switch (activity.type) {
    case "message":
      return (
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {activity.message_type}
            </Badge>
            {activity.priority && activity.priority !== "medium" && (
              <Badge
                variant={activity.priority === "high" || activity.priority === "critical" ? "destructive" : "secondary"}
                className="text-xs"
              >
                {activity.priority}
              </Badge>
            )}
          </div>
          <p className="text-sm text-muted-foreground line-clamp-2">
            {activity.content}
          </p>
        </div>
      );
    case "decision":
      return (
        <div className="space-y-1">
          <p className="text-sm font-medium">{activity.question}</p>
          <p className="text-sm text-muted-foreground">
            <span className="font-semibold">Decision:</span> {activity.decision}
          </p>
          {activity.rationale && (
            <p className="text-xs text-muted-foreground line-clamp-2">
              {activity.rationale}
            </p>
          )}
        </div>
      );
    case "human_input":
      return (
        <div className="space-y-2 p-3 rounded-md bg-orange-50 dark:bg-orange-950/50 border border-orange-200 dark:border-orange-900">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs bg-orange-100 dark:bg-orange-900 border-orange-300">
              Human Interruption
            </Badge>
            {activity.status && (
              <Badge variant="secondary" className="text-xs">
                {activity.status}
              </Badge>
            )}
          </div>
          {activity.request && (
            <p className="text-xs text-muted-foreground italic">
              {activity.request}
            </p>
          )}
          {activity.response && (
            <p className="text-sm font-medium text-orange-900 dark:text-orange-100">
              "{activity.response}"
            </p>
          )}
        </div>
      );
    case "audit":
      if (activity.details && typeof activity.details === "object") {
        return (
          <div className="space-y-1">
            {activity.details.status && (
              <Badge variant="outline" className="text-xs">
                {activity.details.status}
              </Badge>
            )}
            {activity.entity_type && (
              <p className="text-xs text-muted-foreground">
                {activity.entity_type}
              </p>
            )}
          </div>
        );
      }
      return null;
    default:
      return null;
  }
}

export function ActivityFeed({
  activities,
  isLoading,
  title = "Live Activity Feed",
  description = "Real-time updates on agent work"
}: ActivityFeedProps) {
  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5 animate-pulse" />
            {title}
          </CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!activities || activities.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="h-5 w-5" />
            {title}
          </CardTitle>
          <CardDescription>{description}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center justify-center py-8 text-center">
            <Clock className="h-12 w-12 text-muted-foreground mb-3 opacity-50" />
            <p className="text-sm text-muted-foreground">
              No activity yet. Activity will appear here as agents work on this project.
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5 animate-pulse text-green-500" />
          {title}
          <Badge variant="outline" className="ml-auto">
            {activities.length} events
          </Badge>
        </CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
          {activities.map((activity, index) => (
            <div
              key={`${activity.timestamp}-${index}`}
              className="flex gap-3 p-3 rounded-lg border bg-card hover:bg-accent/50 transition-colors"
            >
              {/* Icon */}
              <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${getActivityColor(activity)}`}>
                {getActivityIcon(activity)}
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0 space-y-1">
                <div className="flex items-start justify-between gap-2">
                  <p className="text-sm font-medium">
                    {formatActivityTitle(activity)}
                  </p>
                  <span className="text-xs text-muted-foreground whitespace-nowrap">
                    {formatRelativeTime(activity.timestamp)}
                  </span>
                </div>

                {/* Agent info */}
                {activity.agent_id && (
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <User className="h-3 w-3" />
                    {activity.agent_id}
                  </div>
                )}

                {/* Details */}
                {formatActivityDetails(activity)}
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
