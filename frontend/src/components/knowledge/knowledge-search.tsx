/**
 * Knowledge Search Component
 *
 * High-performance search interface with debouncing, caching,
 * and real-time results.
 */

'use client';

import React, { useState, useCallback, useMemo } from 'react';
import { Search, Filter, Sparkles, Tag, Calendar, TrendingUp } from 'lucide-react';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Skeleton } from '@/components/ui/skeleton';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { useKnowledgeSearch, useKnowledgeCategories, KnowledgeEntry } from '@/hooks/useKnowledge';

interface KnowledgeSearchProps {
  userId?: string;
  agentId?: string;
  onSelectEntry?: (entry: KnowledgeEntry) => void;
  defaultQuery?: string;
  className?: string;
}

export function KnowledgeSearch({
  userId,
  agentId,
  onSelectEntry,
  defaultQuery = '',
  className,
}: KnowledgeSearchProps) {
  const [filters, setFilters] = useState<Record<string, any>>({});
  const [selectedType, setSelectedType] = useState<string>('all');
  const [selectedDomain, setSelectedDomain] = useState<string>('all');

  const { data: categories } = useKnowledgeCategories();

  const {
    query,
    setQuery,
    results,
    isLoading,
    isError,
  } = useKnowledgeSearch(defaultQuery, {
    userId,
    agentId,
    filters: selectedType !== 'all' ? { entry_type: selectedType, ...filters } : filters,
    debounceMs: 300,
  });

  const handleFilterChange = useCallback((key: string, value: any) => {
    setFilters((prev) => ({
      ...prev,
      [key]: value === 'all' ? undefined : value,
    }));
  }, []);

  const filteredResults = useMemo(() => {
    if (selectedDomain === 'all') return results;
    return results.filter((r) => r.domain === selectedDomain);
  }, [results, selectedDomain]);

  return (
    <div className={className}>
      {/* Search Bar */}
      <div className="space-y-4">
        <div className="flex gap-2">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input
              placeholder="Search knowledge base..."
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              className="pl-9"
            />
          </div>
          <Select value={selectedType} onValueChange={setSelectedType}>
            <SelectTrigger className="w-[180px]">
              <Filter className="mr-2 h-4 w-4" />
              <SelectValue placeholder="Type" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Types</SelectItem>
              <SelectItem value="solution">Solutions</SelectItem>
              <SelectItem value="best_practice">Best Practices</SelectItem>
              <SelectItem value="lesson_learned">Lessons</SelectItem>
              <SelectItem value="pattern">Patterns</SelectItem>
              <SelectItem value="standard">Standards</SelectItem>
              <SelectItem value="preference">Preferences</SelectItem>
            </SelectContent>
          </Select>
          <Select value={selectedDomain} onValueChange={setSelectedDomain}>
            <SelectTrigger className="w-[180px]">
              <Tag className="mr-2 h-4 w-4" />
              <SelectValue placeholder="Domain" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All Domains</SelectItem>
              <SelectItem value="technical">Technical</SelectItem>
              <SelectItem value="business">Business</SelectItem>
              <SelectItem value="process">Process</SelectItem>
              <SelectItem value="user">User</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Results Count */}
        {query.length >= 2 && (
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              {isLoading ? 'Searching...' : `${filteredResults.length} results`}
            </span>
            {!isLoading && filteredResults.length > 0 && (
              <span className="flex items-center gap-1">
                <Sparkles className="h-3 w-3" />
                Hybrid AI search
              </span>
            )}
          </div>
        )}
      </div>

      {/* Results */}
      <ScrollArea className="h-[600px] mt-4">
        <div className="space-y-3">
          {isLoading && query.length >= 2 && (
            <>
              {[...Array(3)].map((_, i) => (
                <Card key={i}>
                  <CardHeader>
                    <Skeleton className="h-4 w-3/4" />
                    <Skeleton className="h-3 w-1/2" />
                  </CardHeader>
                  <CardContent>
                    <Skeleton className="h-20 w-full" />
                  </CardContent>
                </Card>
              ))}
            </>
          )}

          {!isLoading && query.length >= 2 && filteredResults.length === 0 && (
            <Card>
              <CardContent className="py-8 text-center">
                <p className="text-muted-foreground">
                  No knowledge found for "{query}"
                </p>
                <p className="text-sm text-muted-foreground mt-2">
                  Try different keywords or filters
                </p>
              </CardContent>
            </Card>
          )}

          {!isLoading &&
            filteredResults.map((entry) => (
              <KnowledgeResultCard
                key={entry.entry_id}
                entry={entry}
                onClick={() => onSelectEntry?.(entry)}
              />
            ))}

          {query.length < 2 && (
            <Card>
              <CardContent className="py-8 text-center">
                <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground">
                  Enter at least 2 characters to search
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

interface KnowledgeResultCardProps {
  entry: KnowledgeEntry;
  onClick?: () => void;
}

function KnowledgeResultCard({ entry, onClick }: KnowledgeResultCardProps) {
  const getTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      solution: 'bg-blue-500/10 text-blue-500',
      best_practice: 'bg-green-500/10 text-green-500',
      lesson_learned: 'bg-yellow-500/10 text-yellow-500',
      pattern: 'bg-purple-500/10 text-purple-500',
      standard: 'bg-orange-500/10 text-orange-500',
      preference: 'bg-pink-500/10 text-pink-500',
    };
    return colors[type] || 'bg-gray-500/10 text-gray-500';
  };

  const getValidationColor = (status: string) => {
    const colors: Record<string, string> = {
      organizational_standard: 'bg-emerald-500/10 text-emerald-500',
      human_validated: 'bg-blue-500/10 text-blue-500',
      agent_validated: 'bg-cyan-500/10 text-cyan-500',
      unvalidated: 'bg-gray-500/10 text-gray-500',
    };
    return colors[status] || 'bg-gray-500/10 text-gray-500';
  };

  return (
    <Card
      className="cursor-pointer transition-all hover:shadow-md hover:border-primary/50"
      onClick={onClick}
    >
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-1">
            <CardTitle className="text-base flex items-center gap-2">
              {entry.title}
              {entry.relevance_score && entry.relevance_score > 0.9 && (
                <Sparkles className="h-4 w-4 text-yellow-500" />
              )}
            </CardTitle>
            <CardDescription className="line-clamp-2">
              {entry.summary || entry.content_excerpt}
            </CardDescription>
          </div>
          <div className="flex flex-col gap-2 items-end">
            <Badge variant="outline" className={getTypeColor(entry.entry_type)}>
              {entry.entry_type.replace('_', ' ')}
            </Badge>
            {entry.validation_status && (
              <Badge
                variant="outline"
                className={`text-xs ${getValidationColor(entry.validation_status)}`}
              >
                {entry.validation_status.replace('_', ' ')}
              </Badge>
            )}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {/* Tags */}
          {entry.tags && entry.tags.length > 0 && (
            <div className="flex flex-wrap gap-1">
              {entry.tags.slice(0, 5).map((tag) => (
                <Badge key={tag} variant="secondary" className="text-xs">
                  {tag}
                </Badge>
              ))}
              {entry.tags.length > 5 && (
                <Badge variant="secondary" className="text-xs">
                  +{entry.tags.length - 5}
                </Badge>
              )}
            </div>
          )}

          {/* Metrics */}
          <div className="flex items-center gap-4 text-xs text-muted-foreground">
            <div className="flex items-center gap-1">
              <TrendingUp className="h-3 w-3" />
              <span>Quality: {(entry.quality_score * 100).toFixed(0)}%</span>
            </div>
            <div className="flex items-center gap-1">
              <span>👍 {entry.helpfulness_ratio ? (entry.helpfulness_ratio * 100).toFixed(0) : 0}%</span>
            </div>
            <div className="flex items-center gap-1">
              <span>Used {entry.use_count}x</span>
            </div>
            {entry.relevance_score && (
              <div className="flex items-center gap-1 text-primary">
                <Sparkles className="h-3 w-3" />
                <span>
                  {(entry.relevance_score * 100).toFixed(0)}% match
                </span>
              </div>
            )}
          </div>

          {/* Timestamp */}
          {entry.created_at && (
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Calendar className="h-3 w-3" />
              <span>
                Created {new Date(entry.created_at).toLocaleDateString()}
              </span>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

export default KnowledgeSearch;
