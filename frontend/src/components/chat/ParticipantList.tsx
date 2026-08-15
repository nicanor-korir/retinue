/**
 * Participant List
 *
 * Displays all active participants in a conversation with real-time presence.
 * Shows agents and users with their current status and activity.
 */

import React from 'react';
import { Users, UserPlus, Bot } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import { AgentPresenceIndicator, AgentPresenceBadge, TypingIndicator } from './AgentPresenceIndicator';
import { cn } from '@/lib/utils';
import type { AgentParticipant } from '@/hooks/useMultiAgent';

export interface ParticipantListProps {
  participants: AgentParticipant[];
  onInviteMore?: () => void;
  currentUserId?: string;
  className?: string;
  compact?: boolean;
}

export function ParticipantList({
  participants,
  onInviteMore,
  currentUserId,
  className,
  compact = false,
}: ParticipantListProps) {
  // Separate agents and users
  const agents = participants;
  const activeAgents = agents.filter(p => p.presence?.status === 'active' || p.presence?.status === 'thinking' || p.presence?.status === 'typing');
  const idleAgents = agents.filter(p => p.presence?.status === 'idle' || p.presence?.status === 'away');

  // Find agents that are typing
  const typingAgents = agents.filter(p => p.presence?.status === 'typing');

  if (compact) {
    return (
      <CompactParticipantList
        participants={participants}
        onInviteMore={onInviteMore}
        className={className}
      />
    );
  }

  return (
    <Card className={cn('', className)}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Users className="h-5 w-5" />
            <CardTitle className="text-base">
              Participants ({participants.length})
            </CardTitle>
          </div>
          {onInviteMore && (
            <Button
              variant="outline"
              size="sm"
              onClick={onInviteMore}
              className="h-7 text-xs"
            >
              <UserPlus className="h-3 w-3 mr-1" />
              Invite
            </Button>
          )}
        </div>
        <CardDescription className="text-xs">
          {activeAgents.length} active • {idleAgents.length} idle
        </CardDescription>
      </CardHeader>

      <CardContent className="pt-0">
        <ScrollArea className="h-[400px] pr-4">
          <div className="space-y-3">
            {/* Active Agents */}
            {activeAgents.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wide">
                  Active ({activeAgents.length})
                </h4>
                <div className="space-y-2">
                  {activeAgents.map((participant) => (
                    <ParticipantCard
                      key={participant.participant_id}
                      participant={participant}
                      isCurrentUser={false}
                    />
                  ))}
                </div>
              </div>
            )}

            {/* Separator if both sections exist */}
            {activeAgents.length > 0 && idleAgents.length > 0 && (
              <Separator className="my-3" />
            )}

            {/* Idle Agents */}
            {idleAgents.length > 0 && (
              <div>
                <h4 className="text-xs font-semibold text-muted-foreground mb-2 uppercase tracking-wide">
                  Idle ({idleAgents.length})
                </h4>
                <div className="space-y-2">
                  {idleAgents.map((participant) => (
                    <ParticipantCard
                      key={participant.participant_id}
                      participant={participant}
                      isCurrentUser={false}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        {/* Typing indicators */}
        {typingAgents.length > 0 && (
          <div className="mt-3 pt-3 border-t">
            {typingAgents.map((agent) => (
              <TypingIndicator
                key={agent.agent_id}
                agentName={agent.agent_name}
                size="sm"
              />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

interface ParticipantCardProps {
  participant: AgentParticipant;
  isCurrentUser: boolean;
}

function ParticipantCard({ participant, isCurrentUser }: ParticipantCardProps) {
  const initials = participant.agent_name
    .split(' ')
    .map((n) => n[0])
    .join('')
    .toUpperCase()
    .slice(0, 2);

  const presenceStatus = participant.presence?.status || 'idle';
  const presenceActivity = participant.presence?.activity;

  return (
    <div className="flex items-start gap-3 rounded-lg p-2 hover:bg-muted/50 transition-colors">
      {/* Avatar with presence badge */}
      <div className="relative">
        <Avatar className="h-10 w-10">
          <AvatarFallback className="bg-primary/10 text-primary">
            <Bot className="h-5 w-5" />
          </AvatarFallback>
        </Avatar>
        <div className="absolute -bottom-0.5 -right-0.5">
          <AgentPresenceBadge status={presenceStatus} size="md" />
        </div>
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <p className="font-medium text-sm truncate">
            {participant.agent_name}
          </p>
          {isCurrentUser && (
            <Badge variant="secondary" className="text-xs px-1.5 py-0 h-4">
              You
            </Badge>
          )}
        </div>

        <p className="text-xs text-muted-foreground mb-1 truncate">
          {participant.agent_role}
        </p>

        {/* Presence */}
        <AgentPresenceIndicator
          status={presenceStatus}
          activity={presenceActivity}
          size="sm"
          showLabel={false}
          showActivity={true}
        />
      </div>
    </div>
  );
}

/**
 * Compact horizontal participant list
 */
function CompactParticipantList({
  participants,
  onInviteMore,
  className,
}: {
  participants: AgentParticipant[];
  onInviteMore?: () => void;
  className?: string;
}) {
  const maxVisible = 5;
  const visibleParticipants = participants.slice(0, maxVisible);
  const hiddenCount = Math.max(0, participants.length - maxVisible);

  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div className="flex items-center -space-x-2">
        {visibleParticipants.map((participant) => {
          const presenceStatus = participant.presence?.status || 'idle';

          return (
            <div key={participant.participant_id} className="relative group">
              <Avatar className="h-8 w-8 border-2 border-background ring-1 ring-border">
                <AvatarFallback className="bg-primary/10 text-primary text-xs">
                  <Bot className="h-4 w-4" />
                </AvatarFallback>
              </Avatar>
              <div className="absolute -bottom-0.5 -right-0.5">
                <AgentPresenceBadge status={presenceStatus} size="sm" />
              </div>

              {/* Tooltip on hover */}
              <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover:block z-10">
                <div className="bg-popover border rounded-md shadow-md p-2 whitespace-nowrap">
                  <p className="text-xs font-medium">{participant.agent_name}</p>
                  <p className="text-xs text-muted-foreground">{participant.agent_role}</p>
                </div>
              </div>
            </div>
          );
        })}

        {hiddenCount > 0 && (
          <Avatar className="h-8 w-8 border-2 border-background ring-1 ring-border">
            <AvatarFallback className="bg-muted text-muted-foreground text-xs">
              +{hiddenCount}
            </AvatarFallback>
          </Avatar>
        )}
      </div>

      {onInviteMore && (
        <Button
          variant="ghost"
          size="sm"
          onClick={onInviteMore}
          className="h-8 text-xs"
        >
          <UserPlus className="h-3 w-3 mr-1" />
          Invite
        </Button>
      )}
    </div>
  );
}

/**
 * Participant count badge
 */
export function ParticipantCount({
  count,
  activeCount,
  onClick,
  className,
}: {
  count: number;
  activeCount?: number;
  onClick?: () => void;
  className?: string;
}) {
  return (
    <Button
      variant="ghost"
      size="sm"
      onClick={onClick}
      className={cn('h-8 gap-2', className)}
    >
      <Users className="h-4 w-4" />
      <span className="text-sm font-medium">{count}</span>
      {activeCount !== undefined && activeCount > 0 && (
        <Badge variant="secondary" className="text-xs px-1.5 py-0 h-4">
          {activeCount} active
        </Badge>
      )}
    </Button>
  );
}

export default ParticipantList;
