'use client';

import { Escalation } from '@/types/escalation';
import { getPriorityColor, getStatusColor, getTypeIcon, formatTimeAgo, formatStatus, calculateSLARemaining, getAssignedName } from '@/lib/escalationUtils';
import { Card, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Clock, User, AlertCircle, MoreVertical } from 'lucide-react';

interface EscalationListProps {
  escalations: Escalation[];
  loading: boolean;
  error: string | null;
  selectedId: string | null;
  onSelect: (id: string) => void;
  onRefresh: () => void;
}

function getEscalationTypeColor(priority: string): string {
  switch (priority) {
    case 'critical':
      return 'border-red-500/50 bg-red-500/5 hover:bg-red-500/10';
    case 'high':
      return 'border-orange-500/50 bg-orange-500/5 hover:bg-orange-500/10';
    case 'medium':
      return 'border-yellow-500/50 bg-yellow-500/5 hover:bg-yellow-500/10';
    default:
      return 'border-border hover:bg-accent/50';
  }
}

export default function EscalationList({ escalations, loading, error, selectedId, onSelect, onRefresh }: EscalationListProps) {
  if (loading) {
    return (
      <div className="space-y-3">
        {[...Array(5)].map((_, i) => (
          <Card key={i} className="animate-pulse">
            <CardContent className="p-4">
              <div className="space-y-3">
                <div className="h-4 bg-muted rounded w-32"></div>
                <div className="h-6 bg-muted rounded w-full"></div>
                <div className="h-4 bg-muted rounded w-3/4"></div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <Card className="border-destructive/50">
        <CardContent className="p-6 text-center">
          <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-3" />
          <p className="text-destructive text-sm mb-3">{error}</p>
          <Button onClick={onRefresh} variant="outline" size="sm">
            Try again
          </Button>
        </CardContent>
      </Card>
    );
  }

  if (escalations.length === 0) {
    return (
      <Card>
        <CardContent className="p-12 text-center">
          <div className="text-6xl mb-4">🎉</div>
          <h3 className="text-lg font-medium mb-2">No escalations found</h3>
          <p className="text-sm text-muted-foreground">Try adjusting your filters or create a new escalation</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      {escalations.map((escalation) => {
        const sla = calculateSLARemaining(escalation.sla_deadline);
        const isSelected = escalation.id === selectedId;

        return (
          <Card
            key={escalation.id}
            className={`transition-all duration-200 cursor-pointer border-l-4 ${
              getEscalationTypeColor(escalation.priority)
            } ${isSelected ? 'ring-2 ring-primary shadow-lg' : 'shadow-sm hover:shadow-md'}`}
            onClick={() => onSelect(escalation.id)}
          >
            <CardContent className="p-4">
              <div className="space-y-3">
                {/* Header Row */}
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    {/* Icon */}
                    <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0 text-xl">
                      {getTypeIcon(escalation.escalation_type)}
                    </div>

                    {/* Escalation Number */}
                    <div className="flex flex-col min-w-0 flex-1">
                      <span className="font-mono text-sm text-muted-foreground">
                        {escalation.escalation_number}
                      </span>
                    </div>
                  </div>

                  {/* Status & Priority Badges */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <Badge className={`text-xs ${getPriorityColor(escalation.priority)}`}>
                      {escalation.priority.toUpperCase()}
                    </Badge>
                    <Badge className={`text-xs ${getStatusColor(escalation.status)}`}>
                      {formatStatus(escalation.status)}
                    </Badge>
                  </div>
                </div>

                {/* Title */}
                <div className="pl-[52px]">
                  <h3 className="font-semibold text-base mb-1 line-clamp-1">
                    {escalation.title}
                  </h3>
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {escalation.description}
                  </p>
                </div>

                {/* SLA Indicator */}
                <div className="pl-[52px]">
                  <div className={`inline-flex items-center gap-1.5 text-xs px-2 py-1 rounded ${
                    sla.isBreached ? 'bg-red-500/10 text-red-600 dark:text-red-400' :
                    sla.isCritical ? 'bg-orange-500/10 text-orange-600 dark:text-orange-400' :
                    sla.isAtRisk ? 'bg-yellow-500/10 text-yellow-600 dark:text-yellow-400' :
                    'bg-green-500/10 text-green-600 dark:text-green-400'
                  }`}>
                    <Clock className="h-3 w-3" />
                    <span className="font-medium">
                      SLA: {sla.isBreached ? 'Breached' : `${sla.hours}h ${sla.minutes}m remaining`}
                    </span>
                  </div>
                </div>

                {/* Footer Row */}
                <div className="flex items-center justify-between pt-2 border-t">
                  <div className="flex items-center gap-3 text-xs text-muted-foreground">
                    <div className="flex items-center gap-1.5">
                      <User className="h-3 w-3" />
                      <span>{getAssignedName(escalation)}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Clock className="h-3 w-3" />
                      <span>{formatTimeAgo(escalation.created_at)}</span>
                    </div>
                  </div>

                  <Button
                    variant="ghost"
                    size="sm"
                    className="h-7 px-2"
                    onClick={(e) => {
                      e.stopPropagation();
                      onSelect(escalation.id);
                    }}
                  >
                    <MoreVertical className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        );
      })}
    </>
  );
}
