'use client';

import { useState } from 'react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Search, X, Filter } from 'lucide-react';
import { EscalationFilters, EscalationStatus, EscalationPriority, EscalationType } from '@/types/escalation';
import { Card, CardContent } from '@/components/ui/card';

interface EscalationFiltersPanelProps {
  filters: EscalationFilters;
  onFilterChange: (filters: Partial<EscalationFilters>) => void;
  totalResults: number;
}

export default function EscalationFiltersPanel({ filters, onFilterChange, totalResults }: EscalationFiltersPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const updateFilter = (key: keyof EscalationFilters, value: any) => {
    onFilterChange({ [key]: value });
  };

  const resetFilters = () => {
    onFilterChange({
      status: undefined,
      priority: undefined,
      type: undefined,
      search: undefined,
      sla_at_risk: undefined,
    });
  };

  const activeFilterCount = [
    filters.search,
    filters.status && filters.status.length > 0,
    filters.priority && filters.priority.length > 0,
    filters.type,
    filters.sla_at_risk,
  ].filter(Boolean).length;

  const handleStatusChange = (value: string) => {
    if (value === 'all') {
      updateFilter('status', undefined);
    } else {
      updateFilter('status', [value as EscalationStatus]);
    }
  };

  const handlePriorityChange = (value: string) => {
    if (value === 'all') {
      updateFilter('priority', undefined);
    } else {
      updateFilter('priority', [value as EscalationPriority]);
    }
  };

  const handleTypeChange = (value: string) => {
    updateFilter('type', value === 'all' ? undefined : [value as EscalationType]);
  };

  const currentStatus = filters.status && filters.status.length > 0 ? filters.status[0] : 'all';
  const currentPriority = filters.priority && filters.priority.length > 0 ? filters.priority[0] : 'all';
  const currentType = filters.type && filters.type.length > 0 ? filters.type[0] : 'all';

  return (
    <Card>
      <CardContent className="p-4 space-y-4">
        {/* Search Bar */}
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search escalations by title, description, or tags..."
              value={filters.search || ''}
              onChange={(e) => updateFilter('search', e.target.value)}
              className="pl-10"
            />
          </div>
          <Button
            variant="outline"
            size="icon"
            onClick={() => setIsExpanded(!isExpanded)}
            className="relative"
          >
            <Filter className="h-4 w-4" />
            {activeFilterCount > 0 && (
              <Badge
                variant="destructive"
                className="absolute -top-2 -right-2 h-5 w-5 rounded-full p-0 flex items-center justify-center text-xs"
              >
                {activeFilterCount}
              </Badge>
            )}
          </Button>
          {activeFilterCount > 0 && (
            <Button variant="ghost" size="sm" onClick={resetFilters}>
              <X className="h-4 w-4 mr-1" />
              Clear
            </Button>
          )}
        </div>

        {/* Expanded Filters */}
        {isExpanded && (
          <div className="grid gap-4 md:grid-cols-3">
            <div>
              <label className="text-sm font-medium mb-2 block">Status</label>
              <Select value={currentStatus} onValueChange={handleStatusChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Status</SelectItem>
                  {Object.values(EscalationStatus).map((status) => (
                    <SelectItem key={status} value={status}>
                      {status.replace('_', ' ').split(' ').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Priority</label>
              <Select value={currentPriority} onValueChange={handlePriorityChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Priorities</SelectItem>
                  {Object.values(EscalationPriority).map((priority) => (
                    <SelectItem key={priority} value={priority}>
                      {priority.charAt(0).toUpperCase() + priority.slice(1)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">Type</label>
              <Select value={currentType} onValueChange={handleTypeChange}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Types</SelectItem>
                  {Object.values(EscalationType).map((type) => (
                    <SelectItem key={type} value={type}>
                      {type.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">SLA Status</label>
              <Select
                value={filters.sla_at_risk ? 'at_risk' : 'all'}
                onValueChange={(value) => updateFilter('sla_at_risk', value === 'at_risk')}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All SLA Status</SelectItem>
                  <SelectItem value="at_risk">At Risk</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
