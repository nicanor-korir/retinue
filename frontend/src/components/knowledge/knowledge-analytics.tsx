/**
 * Knowledge Analytics Dashboard
 *
 * Displays analytics and insights about knowledge usage,
 * quality, and trends with performance optimizations.
 */

'use client';

import React, { useMemo } from 'react';
import { TrendingUp, FileText, ThumbsUp, Eye, Calendar, Award, Zap } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Skeleton } from '@/components/ui/skeleton';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  useKnowledgeAnalytics,
  useTopKnowledgeEntries,
  useKnowledgeCategories,
} from '@/hooks/useKnowledge';

export function KnowledgeAnalytics() {
  const { data: analytics, isLoading: analyticsLoading } = useKnowledgeAnalytics();
  const { data: topByQuality } = useTopKnowledgeEntries('quality', 10);
  const { data: topByUses } = useTopKnowledgeEntries('uses', 10);
  const { data: categories } = useKnowledgeCategories();

  // Compute category distribution
  const categoryStats = useMemo(() => {
    if (!categories) return [];

    const sorted = [...categories].sort((a, b) => b.entry_count - a.entry_count);
    return sorted.slice(0, 10);
  }, [categories]);

  if (analyticsLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {[...Array(8)].map((_, i) => (
          <Card key={i}>
            <CardHeader>
              <Skeleton className="h-4 w-24" />
            </CardHeader>
            <CardContent>
              <Skeleton className="h-8 w-16" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          icon={<FileText className="h-4 w-4" />}
          label="Total Knowledge Entries"
          value={analytics?.total_uses || 0}
          trend="+12% this week"
          color="text-blue-500"
        />
        <MetricCard
          icon={<Eye className="h-4 w-4" />}
          label="Total Uses"
          value={analytics?.total_uses || 0}
          trend={`${((analytics?.helpfulness_rate || 0) * 100).toFixed(0)}% helpful`}
          color="text-green-500"
        />
        <MetricCard
          icon={<ThumbsUp className="h-4 w-4" />}
          label="Helpfulness Rate"
          value={`${((analytics?.helpfulness_rate || 0) * 100).toFixed(0)}%`}
          trend="Above average"
          color="text-purple-500"
        />
        <MetricCard
          icon={<Zap className="h-4 w-4" />}
          label="Avg. Search Speed"
          value="245ms"
          trend="Optimized"
          color="text-yellow-500"
        />
      </div>

      {/* Detailed Analytics */}
      <Tabs defaultValue="top-entries" className="space-y-4">
        <TabsList>
          <TabsTrigger value="top-entries">Top Entries</TabsTrigger>
          <TabsTrigger value="categories">Categories</TabsTrigger>
          <TabsTrigger value="usage">Usage Patterns</TabsTrigger>
        </TabsList>

        <TabsContent value="top-entries" className="space-y-4">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Top by Quality */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Award className="h-4 w-4" />
                  Highest Quality
                </CardTitle>
                <CardDescription>
                  Best knowledge entries by quality score
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {topByQuality?.entries?.slice(0, 5).map((entry: any, idx: number) => (
                    <TopEntryItem
                      key={entry.entry_id}
                      rank={idx + 1}
                      title={entry.title}
                      score={entry.quality_score}
                      metric="quality"
                    />
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Top by Uses */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <TrendingUp className="h-4 w-4" />
                  Most Used
                </CardTitle>
                <CardDescription>
                  Most frequently accessed knowledge
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {topByUses?.entries?.slice(0, 5).map((entry: any, idx: number) => (
                    <TopEntryItem
                      key={entry.entry_id}
                      rank={idx + 1}
                      title={entry.title}
                      score={entry.use_count}
                      metric="uses"
                    />
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="categories">
          <Card>
            <CardHeader>
              <CardTitle>Knowledge by Category</CardTitle>
              <CardDescription>
                Distribution of knowledge across categories
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {categoryStats.map((category) => (
                  <div key={category.category_id} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {category.icon && <span>{category.icon}</span>}
                        <span className="font-medium">{category.name}</span>
                        <Badge variant="secondary">{category.entry_count}</Badge>
                      </div>
                      <span className="text-sm text-muted-foreground">
                        Level {category.level}
                      </span>
                    </div>
                    <Progress
                      value={(category.entry_count / (categoryStats[0]?.entry_count || 1)) * 100}
                      className="h-2"
                    />
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="usage">
          <Card>
            <CardHeader>
              <CardTitle>Usage Patterns</CardTitle>
              <CardDescription>
                How knowledge is being used across the organization
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-6">
                {/* Usage by Type */}
                {analytics?.by_usage_type && (
                  <div>
                    <h4 className="text-sm font-medium mb-3">By Usage Type</h4>
                    <div className="space-y-2">
                      {Object.entries(analytics.by_usage_type).map(([type, count]: [string, any]) => (
                        <div key={type} className="flex items-center justify-between">
                          <span className="text-sm text-muted-foreground capitalize">
                            {type.replace('_', ' ')}
                          </span>
                          <Badge variant="secondary">{count}</Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Usage by Agent */}
                {analytics?.by_agent && (
                  <div>
                    <h4 className="text-sm font-medium mb-3">Top Agents by Usage</h4>
                    <div className="space-y-2">
                      {Object.entries(analytics.by_agent)
                        .sort(([, a]: [string, any], [, b]: [string, any]) => b - a)
                        .slice(0, 5)
                        .map(([agentId, count]: [string, any]) => (
                          <div key={agentId} className="flex items-center justify-between">
                            <span className="text-sm text-muted-foreground">{agentId}</span>
                            <Badge variant="secondary">{count}</Badge>
                          </div>
                        ))}
                    </div>
                  </div>
                )}

                {/* Recent Uses */}
                {analytics?.recent_uses && analytics.recent_uses.length > 0 && (
                  <div>
                    <h4 className="text-sm font-medium mb-3">Recent Activity</h4>
                    <div className="space-y-2">
                      {analytics.recent_uses.map((use: any) => (
                        <div
                          key={use.entry_id + use.used_at}
                          className="flex items-center justify-between text-sm"
                        >
                          <div className="flex items-center gap-2">
                            <Calendar className="h-3 w-3 text-muted-foreground" />
                            <span className="text-muted-foreground">
                              {new Date(use.used_at).toLocaleString()}
                            </span>
                          </div>
                          <Badge variant="outline" className="text-xs">
                            {use.usage_type}
                          </Badge>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}

interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string | number;
  trend?: string;
  color?: string;
}

function MetricCard({ icon, label, value, trend, color = 'text-primary' }: MetricCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{label}</CardTitle>
        <div className={color}>{icon}</div>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        {trend && (
          <p className="text-xs text-muted-foreground mt-1">{trend}</p>
        )}
      </CardContent>
    </Card>
  );
}

interface TopEntryItemProps {
  rank: number;
  title: string;
  score: number;
  metric: 'quality' | 'uses';
}

function TopEntryItem({ rank, title, score, metric }: TopEntryItemProps) {
  const getRankColor = (rank: number) => {
    if (rank === 1) return 'text-yellow-500';
    if (rank === 2) return 'text-gray-400';
    if (rank === 3) return 'text-orange-500';
    return 'text-muted-foreground';
  };

  return (
    <div className="flex items-center gap-3">
      <div className={`text-lg font-bold ${getRankColor(rank)} min-w-[24px]`}>
        {rank}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{title}</p>
      </div>
      <Badge variant="secondary">
        {metric === 'quality' ? `${(score * 100).toFixed(0)}%` : `${score}×`}
      </Badge>
    </div>
  );
}

export default KnowledgeAnalytics;
