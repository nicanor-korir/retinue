/**
 * Agent Suggestions Panel
 *
 * Displays AI-powered agent recommendations for conversations.
 * Shows relevance scores, expertise match, and reasoning.
 */

import React, { useState } from 'react';
import { Sparkles, X, UserPlus, ChevronDown, ChevronUp, Info, Zap } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from '@/components/ui/tooltip';
import { cn } from '@/lib/utils';
import type { AgentSuggestion } from '@/hooks/useMultiAgent';

export interface AgentSuggestionsPanelProps {
  suggestions: AgentSuggestion[];
  onInvite: (agentId: string) => void;
  onDismiss: (agentId: string) => void;
  onClose?: () => void;
  isInviting?: boolean;
  className?: string;
}

export function AgentSuggestionsPanel({
  suggestions,
  onInvite,
  onDismiss,
  onClose,
  isInviting = false,
  className,
}: AgentSuggestionsPanelProps) {
  if (suggestions.length === 0) {
    return null;
  }

  return (
    <Card className={cn('border-primary/30 bg-primary/5 shadow-md', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="h-5 w-5 text-primary animate-pulse" />
            <CardTitle className="text-base">AI Suggests Inviting</CardTitle>
          </div>
          {onClose && (
            <Button
              variant="ghost"
              size="sm"
              className="h-6 w-6 p-0"
              onClick={onClose}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>
        <CardDescription className="text-xs">
          These agents may be helpful based on the conversation context
        </CardDescription>
      </CardHeader>

      <CardContent className="space-y-3">
        {suggestions.map((suggestion) => (
          <AgentSuggestionCard
            key={suggestion.agent_id}
            suggestion={suggestion}
            onInvite={() => onInvite(suggestion.agent_id)}
            onDismiss={() => onDismiss(suggestion.agent_id)}
            isInviting={isInviting}
          />
        ))}
      </CardContent>
    </Card>
  );
}

interface AgentSuggestionCardProps {
  suggestion: AgentSuggestion;
  onInvite: () => void;
  onDismiss: () => void;
  isInviting: boolean;
}

function AgentSuggestionCard({
  suggestion,
  onInvite,
  onDismiss,
  isInviting,
}: AgentSuggestionCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const relevancePercentage = Math.round(suggestion.relevance_score * 100);
  const isHighRelevance = suggestion.relevance_score >= 0.9;

  return (
    <div
      className={cn(
        'rounded-lg border bg-card p-3 transition-all hover:shadow-sm',
        isHighRelevance && 'border-primary/50 bg-primary/5'
      )}
    >
      {/* Header with agent info */}
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          {/* Agent name and role */}
          <div className="flex items-center gap-2 mb-1">
            <h4 className="font-semibold text-sm truncate">
              {suggestion.agent_name}
            </h4>
            {isHighRelevance && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger>
                    <Badge variant="default" className="text-xs px-1.5 py-0 h-5">
                      <Zap className="h-3 w-3 mr-1" />
                      Auto-Join
                    </Badge>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p className="text-xs">High relevance - will join automatically</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </div>

          <p className="text-xs text-muted-foreground mb-2">
            {suggestion.agent_role}
          </p>

          {/* Relevance score */}
          <div className="mb-2">
            <div className="flex items-center justify-between mb-1">
              <span className="text-xs font-medium">Relevance</span>
              <span className="text-xs font-bold text-primary">
                {relevancePercentage}%
              </span>
            </div>
            <Progress
              value={relevancePercentage}
              className="h-1.5"
            />
          </div>

          {/* Expertise tags */}
          <div className="flex flex-wrap gap-1 mb-2">
            {suggestion.expertise_match.slice(0, 3).map((expertise) => (
              <Badge
                key={expertise}
                variant="secondary"
                className="text-xs px-2 py-0 h-5"
              >
                {expertise.replace('_', ' ')}
              </Badge>
            ))}
            {suggestion.expertise_match.length > 3 && (
              <Badge variant="outline" className="text-xs px-2 py-0 h-5">
                +{suggestion.expertise_match.length - 3}
              </Badge>
            )}
          </div>

          {/* Reasoning */}
          <p className="text-xs text-muted-foreground italic line-clamp-2">
            {suggestion.reasoning}
          </p>
        </div>

        {/* Actions */}
        <div className="flex flex-col gap-1">
          <Button
            size="sm"
            onClick={onInvite}
            disabled={isInviting}
            className="h-7 text-xs px-2"
          >
            <UserPlus className="h-3 w-3 mr-1" />
            Invite
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={onDismiss}
            className="h-7 text-xs px-2"
          >
            <X className="h-3 w-3 mr-1" />
            Dismiss
          </Button>
        </div>
      </div>

      {/* Expandable details */}
      <Collapsible open={isExpanded} onOpenChange={setIsExpanded}>
        <CollapsibleTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="w-full h-6 mt-2 text-xs"
          >
            {isExpanded ? (
              <>
                <ChevronUp className="h-3 w-3 mr-1" />
                Hide Details
              </>
            ) : (
              <>
                <ChevronDown className="h-3 w-3 mr-1" />
                Show Details
              </>
            )}
          </Button>
        </CollapsibleTrigger>

        <CollapsibleContent className="mt-2 space-y-2">
          {/* Prediction factors */}
          <div className="bg-muted/50 rounded p-2 space-y-1.5">
            <div className="flex items-center gap-1 mb-1">
              <Info className="h-3 w-3 text-muted-foreground" />
              <span className="text-xs font-medium">Match Factors</span>
            </div>

            {Object.entries(suggestion.prediction_factors).map(([factor, score]) => (
              <div key={factor} className="space-y-0.5">
                <div className="flex items-center justify-between">
                  <span className="text-xs text-muted-foreground capitalize">
                    {factor.replace('_', ' ')}
                  </span>
                  <span className="text-xs font-medium">
                    {Math.round((score as number) * 100)}%
                  </span>
                </div>
                <Progress
                  value={(score as number) * 100}
                  className="h-1"
                />
              </div>
            ))}
          </div>

          {/* All expertise areas */}
          {suggestion.expertise_match.length > 3 && (
            <div>
              <p className="text-xs font-medium mb-1">All Expertise Areas:</p>
              <div className="flex flex-wrap gap-1">
                {suggestion.expertise_match.map((expertise) => (
                  <Badge
                    key={expertise}
                    variant="outline"
                    className="text-xs px-2 py-0 h-5"
                  >
                    {expertise.replace('_', ' ')}
                  </Badge>
                ))}
              </div>
            </div>
          )}

          {/* Confidence */}
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">AI Confidence</span>
            <span className="font-medium">
              {Math.round(suggestion.confidence * 100)}%
            </span>
          </div>
        </CollapsibleContent>
      </Collapsible>
    </div>
  );
}

/**
 * Compact suggestions banner for inline display
 */
export function AgentSuggestionsBanner({
  suggestion,
  onInvite,
  onDismiss,
  className,
}: {
  suggestion: AgentSuggestion;
  onInvite: () => void;
  onDismiss: () => void;
  className?: string;
}) {
  return (
    <div
      className={cn(
        'flex items-center justify-between gap-3 rounded-lg border border-primary/30 bg-primary/5 p-3',
        className
      )}
    >
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <Sparkles className="h-4 w-4 text-primary flex-shrink-0" />
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium truncate">
            Suggest: {suggestion.agent_name}
          </p>
          <p className="text-xs text-muted-foreground truncate">
            {suggestion.reasoning}
          </p>
        </div>
        <Badge variant="secondary" className="text-xs">
          {Math.round(suggestion.relevance_score * 100)}% match
        </Badge>
      </div>
      <div className="flex gap-1">
        <Button size="sm" onClick={onInvite} className="h-7 text-xs">
          Invite
        </Button>
        <Button
          variant="ghost"
          size="sm"
          onClick={onDismiss}
          className="h-7 w-7 p-0"
        >
          <X className="h-3 w-3" />
        </Button>
      </div>
    </div>
  );
}

export default AgentSuggestionsPanel;
