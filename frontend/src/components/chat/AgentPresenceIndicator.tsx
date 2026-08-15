/**
 * Agent Presence Indicator
 *
 * Displays real-time presence status for agents in conversations.
 * Shows visual indicators for: active, idle, thinking, typing, away
 */

import React from 'react';
import { Loader2, Zap, MessageSquare, Moon, Circle } from 'lucide-react';
import { cn } from '@/lib/utils';

export interface AgentPresenceIndicatorProps {
  status: 'active' | 'idle' | 'thinking' | 'typing' | 'away';
  activity?: string | null;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
  showActivity?: boolean;
  className?: string;
}

const statusConfig = {
  active: {
    color: 'bg-green-500',
    pulseColor: 'bg-green-400',
    textColor: 'text-green-600',
    label: 'Active',
    icon: Circle,
    animate: false,
  },
  thinking: {
    color: 'bg-blue-500',
    pulseColor: 'bg-blue-400',
    textColor: 'text-blue-600',
    label: 'Thinking',
    icon: Loader2,
    animate: true,
  },
  typing: {
    color: 'bg-purple-500',
    pulseColor: 'bg-purple-400',
    textColor: 'text-purple-600',
    label: 'Typing',
    icon: MessageSquare,
    animate: true,
  },
  idle: {
    color: 'bg-gray-400',
    pulseColor: 'bg-gray-300',
    textColor: 'text-gray-600',
    label: 'Idle',
    icon: Moon,
    animate: false,
  },
  away: {
    color: 'bg-gray-300',
    pulseColor: 'bg-gray-200',
    textColor: 'text-gray-500',
    label: 'Away',
    icon: Circle,
    animate: false,
  },
};

const sizeConfig = {
  sm: {
    dot: 'h-2 w-2',
    icon: 'h-3 w-3',
    text: 'text-xs',
  },
  md: {
    dot: 'h-3 w-3',
    icon: 'h-4 w-4',
    text: 'text-sm',
  },
  lg: {
    dot: 'h-4 w-4',
    icon: 'h-5 w-5',
    text: 'text-base',
  },
};

export function AgentPresenceIndicator({
  status,
  activity,
  size = 'md',
  showLabel = true,
  showActivity = true,
  className,
}: AgentPresenceIndicatorProps) {
  const config = statusConfig[status] || statusConfig.idle;
  const sizeClass = sizeConfig[size];
  const Icon = config.icon;

  return (
    <div className={cn('flex items-center gap-2', className)}>
      {/* Status Indicator */}
      <div className="relative">
        {/* Main dot */}
        <div
          className={cn(
            'rounded-full',
            sizeClass.dot,
            config.color,
            config.animate && 'animate-pulse'
          )}
        />

        {/* Pulse ring for active/animated states */}
        {config.animate && (
          <div
            className={cn(
              'absolute top-0 left-0 rounded-full animate-ping',
              sizeClass.dot,
              config.pulseColor,
              'opacity-75'
            )}
          />
        )}
      </div>

      {/* Label and Activity */}
      {(showLabel || showActivity) && (
        <div className="flex items-center gap-1.5">
          {/* Icon for thinking/typing states */}
          {config.animate && (
            <Icon
              className={cn(
                sizeClass.icon,
                config.textColor,
                config.animate && 'animate-spin'
              )}
            />
          )}

          <div className="flex flex-col">
            {/* Status label */}
            {showLabel && (
              <span
                className={cn(
                  'font-medium',
                  sizeClass.text,
                  config.textColor
                )}
              >
                {config.label}
              </span>
            )}

            {/* Activity description */}
            {showActivity && activity && (
              <span
                className={cn(
                  'text-muted-foreground italic',
                  size === 'sm' ? 'text-xs' : 'text-xs'
                )}
              >
                {activity}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Compact presence badge for avatars
 */
export function AgentPresenceBadge({
  status,
  size = 'md',
  className,
}: {
  status: 'active' | 'idle' | 'thinking' | 'typing' | 'away';
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}) {
  const config = statusConfig[status] || statusConfig.idle;
  const sizeClass = size === 'sm' ? 'h-2 w-2' : size === 'lg' ? 'h-4 w-4' : 'h-3 w-3';

  return (
    <div className={cn('relative inline-block', className)}>
      <div
        className={cn(
          'rounded-full border-2 border-background',
          sizeClass,
          config.color,
          config.animate && 'animate-pulse'
        )}
      />
      {config.animate && (
        <div
          className={cn(
            'absolute top-0 left-0 rounded-full animate-ping opacity-75',
            sizeClass,
            config.pulseColor
          )}
        />
      )}
    </div>
  );
}

/**
 * Typing indicator with animated dots
 */
export function TypingIndicator({
  agentName,
  size = 'md',
  className,
}: {
  agentName?: string;
  size?: 'sm' | 'md' | 'lg';
  className?: string;
}) {
  const dotSize = size === 'sm' ? 'h-1.5 w-1.5' : size === 'lg' ? 'h-3 w-3' : 'h-2 w-2';
  const textSize = size === 'sm' ? 'text-xs' : size === 'lg' ? 'text-base' : 'text-sm';

  return (
    <div className={cn('flex items-center gap-2 text-muted-foreground', className)}>
      <div className="flex items-center gap-1">
        <div className={cn('rounded-full bg-gray-400 animate-bounce', dotSize)} style={{ animationDelay: '0ms' }} />
        <div className={cn('rounded-full bg-gray-400 animate-bounce', dotSize)} style={{ animationDelay: '150ms' }} />
        <div className={cn('rounded-full bg-gray-400 animate-bounce', dotSize)} style={{ animationDelay: '300ms' }} />
      </div>
      {agentName && (
        <span className={cn('italic', textSize)}>
          {agentName} is typing...
        </span>
      )}
    </div>
  );
}

/**
 * Activity indicator for specific actions
 */
export function AgentActivityIndicator({
  activity,
  icon: CustomIcon,
  className,
}: {
  activity: string;
  icon?: React.ComponentType<{ className?: string }>;
  className?: string;
}) {
  const Icon = CustomIcon || Zap;

  return (
    <div className={cn('flex items-center gap-1.5 text-xs text-muted-foreground', className)}>
      <Icon className="h-3 w-3 animate-pulse" />
      <span className="italic">{activity}</span>
    </div>
  );
}

export default AgentPresenceIndicator;
