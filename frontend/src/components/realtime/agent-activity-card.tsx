"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { AgentActivity, ActivityType, LLMInteraction } from "@/types/events";
import { Brain, Code, Clock, MessageSquare, Eye, Loader2, CheckCircle2, AlertCircle, Pause } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";
import { useState } from "react";
import { Button } from "@/components/ui/button";

interface AgentActivityCardProps {
  activity: AgentActivity;
  llmInteraction?: LLMInteraction;
  thoughts?: string[];
  agentName?: string;
  streamingResponse?: string;
  className?: string;
}

function getActivityIcon(type: ActivityType) {
  switch (type) {
    case ActivityType.THINKING:
      return <Brain className="h-5 w-5 text-blue-500" />;
    case ActivityType.GENERATING:
      return <Code className="h-5 w-5 text-green-500 animate-pulse" />;
    case ActivityType.DECIDING:
      return <AlertCircle className="h-5 w-5 text-yellow-500" />;
    case ActivityType.MESSAGING:
      return <MessageSquare className="h-5 w-5 text-purple-500" />;
    case ActivityType.REVIEWING:
      return <Eye className="h-5 w-5 text-orange-500" />;
    case ActivityType.WAITING:
      return <Pause className="h-5 w-5 text-gray-500" />;
    case ActivityType.COMPLETED:
      return <CheckCircle2 className="h-5 w-5 text-green-600" />;
    case ActivityType.ERROR:
      return <AlertCircle className="h-5 w-5 text-red-500" />;
    default:
      return <Loader2 className="h-5 w-5 text-gray-400 animate-spin" />;
  }
}

function getActivityColor(type: ActivityType): "default" | "secondary" | "success" | "warning" | "info" | "destructive" {
  switch (type) {
    case ActivityType.THINKING:
      return "info";
    case ActivityType.GENERATING:
      return "success";
    case ActivityType.DECIDING:
      return "warning";
    case ActivityType.WAITING:
      return "secondary";
    case ActivityType.COMPLETED:
      return "success";
    case ActivityType.ERROR:
      return "destructive";
    default:
      return "default";
  }
}

export function AgentActivityCard({
  activity,
  llmInteraction,
  thoughts,
  agentName,
  streamingResponse,
  className,
}: AgentActivityCardProps) {
  const [showLLMDetails, setShowLLMDetails] = useState(false);
  const [showThoughts, setShowThoughts] = useState(true);

  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            {getActivityIcon(activity.activity_type)}
            <div>
              <CardTitle className="text-base">
                {agentName || activity.agent_id}
              </CardTitle>
              <p className="text-xs text-muted-foreground">
                {formatRelativeTime(activity.created_at)}
              </p>
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {activity.is_active && (
              <Badge variant="secondary" className="animate-pulse">
                Active
              </Badge>
            )}
            <Badge variant={getActivityColor(activity.activity_type)}>
              {activity.activity_type}
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Current Activity */}
        <div>
          <h4 className="font-medium mb-1">{activity.title}</h4>
          {activity.description && (
            <p className="text-sm text-muted-foreground">{activity.description}</p>
          )}
        </div>

        {/* Progress Bar */}
        {activity.is_active && activity.progress_percentage > 0 && (
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">{activity.stage || "Processing"}</span>
              <span className="font-medium">{activity.progress_percentage}%</span>
            </div>
            <div className="w-full bg-secondary rounded-full h-2">
              <div
                className="bg-primary rounded-full h-2 transition-all duration-300"
                style={{ width: `${activity.progress_percentage}%` }}
              />
            </div>
          </div>
        )}

        {/* Current Thoughts */}
        {thoughts && thoughts.length > 0 && (
          <div className="border-l-2 border-blue-500 pl-3 py-2 bg-blue-50 dark:bg-blue-950/20 rounded-r">
            <div className="flex items-center justify-between mb-2">
              <h5 className="text-xs font-semibold text-blue-700 dark:text-blue-300 flex items-center">
                <Brain className="h-3 w-3 mr-1" />
                Current Thought
              </h5>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 text-xs"
                onClick={() => setShowThoughts(!showThoughts)}
              >
                {showThoughts ? "Hide" : "Show"}
              </Button>
            </div>
            {showThoughts && (
              <div className="space-y-2">
                {thoughts.map((thought, idx) => (
                  <p key={idx} className="text-sm text-blue-900 dark:text-blue-100 italic">
                    "{thought}"
                  </p>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Streaming LLM Response */}
        {streamingResponse && (
          <div className="border-l-2 border-green-500 pl-3 py-2 bg-green-50 dark:bg-green-950/20 rounded-r animate-pulse">
            <h5 className="text-xs font-semibold text-green-700 dark:text-green-300 flex items-center mb-2">
              <Brain className="h-3 w-3 mr-1 animate-spin" />
              AI Generating Response...
            </h5>
            <div className="text-sm text-green-900 dark:text-green-100 font-mono whitespace-pre-wrap max-h-40 overflow-y-auto">
              {streamingResponse}
              <span className="inline-block w-2 h-4 bg-green-600 animate-pulse ml-1">|</span>
            </div>
          </div>
        )}

        {/* LLM Interaction (Completed) */}
        {llmInteraction && !streamingResponse && (
          <div className="border-l-2 border-purple-500 pl-3 py-2 bg-purple-50 dark:bg-purple-950/20 rounded-r">
            <div className="flex items-center justify-between mb-2">
              <h5 className="text-xs font-semibold text-purple-700 dark:text-purple-300 flex items-center">
                <Brain className="h-3 w-3 mr-1" />
                LLM Interaction
              </h5>
              <Button
                variant="ghost"
                size="sm"
                className="h-6 text-xs"
                onClick={() => setShowLLMDetails(!showLLMDetails)}
              >
                {showLLMDetails ? "Hide" : "Details"}
              </Button>
            </div>
            <div className="text-xs text-muted-foreground space-y-1">
              <div className="flex items-center justify-between">
                <span>Model: {llmInteraction.model}</span>
                <Badge variant="outline" className="text-xs">
                  {llmInteraction.status}
                </Badge>
              </div>
              {llmInteraction.total_tokens && (
                <div className="flex items-center justify-between">
                  <span>Tokens: {llmInteraction.total_tokens}</span>
                  {llmInteraction.latency_ms && (
                    <span>Latency: {llmInteraction.latency_ms}ms</span>
                  )}
                </div>
              )}
            </div>

            {showLLMDetails && llmInteraction.response && (
              <div className="mt-3 p-2 bg-background rounded border text-xs">
                <p className="text-muted-foreground mb-1">Response:</p>
                <p className="whitespace-pre-wrap line-clamp-3">{llmInteraction.response}</p>
              </div>
            )}
          </div>
        )}

        {/* Recent Actions */}
        <div className="text-xs text-muted-foreground">
          <Clock className="h-3 w-3 inline mr-1" />
          {activity.completed_at ? (
            <span>Completed {formatRelativeTime(activity.completed_at)}</span>
          ) : (
            <span>Started {formatRelativeTime(activity.created_at)}</span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
