/**
 * Agent Involvement Predictions Component
 *
 * Displays AI-powered predictions for which agents should be involved
 * in conversations or projects.
 */

'use client';

import React from 'react';
import { Users, Brain, Clock, Zap, CheckCircle2, AlertCircle } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { useAgentPredictions, AgentPrediction } from '@/hooks/useKnowledge';

interface AgentPredictionsProps {
  conversationId?: string;
  projectId?: string;
  messageIds: string[];
  currentAgentIds?: string[];
  userId?: string;
  onInviteAgent?: (agentId: string) => void;
}

export function AgentPredictions({
  conversationId,
  projectId,
  messageIds,
  currentAgentIds = [],
  userId,
  onInviteAgent,
}: AgentPredictionsProps) {
  const { data: predictions, isLoading } = useAgentPredictions({
    conversation_id: conversationId,
    project_id: projectId,
    message_ids: messageIds,
    current_agent_ids: currentAgentIds,
    user_id: userId,
  }, {
    enabled: messageIds.length > 0,
  });

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-48" />
          <Skeleton className="h-4 w-64" />
        </CardHeader>
        <CardContent className="space-y-3">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-24 w-full" />
          ))}
        </CardContent>
      </Card>
    );
  }

  if (!predictions || predictions.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <Users className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">
            No agent suggestions at this time
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            AI will suggest agents as the conversation develops
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5" />
          AI Agent Suggestions
        </CardTitle>
        <CardDescription>
          Based on conversation analysis, these agents may help
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {predictions.map((prediction) => (
          <AgentPredictionCard
            key={prediction.agent_id}
            prediction={prediction}
            onInvite={onInviteAgent}
          />
        ))}
      </CardContent>
    </Card>
  );
}

interface AgentPredictionCardProps {
  prediction: AgentPrediction;
  onInvite?: (agentId: string) => void;
}

function AgentPredictionCard({ prediction, onInvite }: AgentPredictionCardProps) {
  const getContributionColor = (type: string) => {
    const colors: Record<string, string> = {
      primary_expert: 'bg-purple-500/10 text-purple-500',
      secondary_support: 'bg-blue-500/10 text-blue-500',
      reviewer: 'bg-green-500/10 text-green-500',
      optional: 'bg-gray-500/10 text-gray-500',
    };
    return colors[type] || 'bg-gray-500/10 text-gray-500';
  };

  const getTimingIcon = (timing: string) => {
    switch (timing) {
      case 'immediate':
        return <Zap className="h-3 w-3" />;
      case 'after_initial_discussion':
        return <Clock className="h-3 w-3" />;
      case 'when_topic_arises':
        return <AlertCircle className="h-3 w-3" />;
      default:
        return <CheckCircle2 className="h-3 w-3" />;
    }
  };

  const getProbabilityColor = (prob: number) => {
    if (prob >= 0.9) return 'text-green-500';
    if (prob >= 0.7) return 'text-yellow-500';
    return 'text-blue-500';
  };

  return (
    <Card className="border-2">
      <CardContent className="pt-6">
        <div className="space-y-4">
          {/* Header */}
          <div className="flex items-start justify-between gap-4">
            <div className="flex-1 space-y-2">
              <div className="flex items-center gap-2">
                <h4 className="font-semibold">{prediction.agent_name}</h4>
                <Badge variant="secondary" className="text-xs">
                  {prediction.agent_role}
                </Badge>
              </div>
              <div className="flex items-center gap-2 flex-wrap">
                <Badge
                  variant="outline"
                  className={getContributionColor(prediction.predicted_contribution_type)}
                >
                  {prediction.predicted_contribution_type.replace('_', ' ')}
                </Badge>
                <Badge variant="outline" className="flex items-center gap-1">
                  {getTimingIcon(prediction.suggested_timing)}
                  {prediction.suggested_timing.replace('_', ' ')}
                </Badge>
              </div>
            </div>

            {onInvite && (
              <Button
                size="sm"
                onClick={() => onInvite(prediction.agent_id)}
                variant={prediction.involvement_probability >= 0.9 ? 'default' : 'outline'}
              >
                <Users className="h-4 w-4 mr-2" />
                Invite
              </Button>
            )}
          </div>

          {/* Probability Bar */}
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Match Confidence</span>
              <span className={`font-semibold ${getProbabilityColor(prediction.involvement_probability)}`}>
                {(prediction.involvement_probability * 100).toFixed(0)}%
              </span>
            </div>
            <Progress value={prediction.involvement_probability * 100} className="h-2" />
          </div>

          {/* Reasons */}
          {prediction.trigger_reasons && prediction.trigger_reasons.length > 0 && (
            <div className="space-y-2">
              <p className="text-xs font-medium text-muted-foreground">Why this agent?</p>
              <ul className="space-y-1">
                {prediction.trigger_reasons.slice(0, 3).map((reason, idx) => (
                  <li key={idx} className="text-xs text-muted-foreground flex items-start gap-2">
                    <span className="text-primary mt-0.5">•</span>
                    <span>{reason}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Introduction Approach */}
          <div className="flex items-center gap-2 text-xs text-muted-foreground">
            <span className="font-medium">Approach:</span>
            <span>
              {prediction.introduction_approach === 'auto_join'
                ? '🤖 Auto-join conversation'
                : prediction.introduction_approach === 'suggest_to_user'
                ? '💡 Suggest to user'
                : '⏱️ Standby mode'}
            </span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

export default AgentPredictions;
