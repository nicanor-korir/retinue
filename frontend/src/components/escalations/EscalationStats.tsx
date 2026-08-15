'use client';

import { EscalationStats as StatsType } from '@/types/escalation';

interface EscalationStatsProps {
  stats: StatsType | null;
  loading: boolean;
}

export default function EscalationStats({ stats, loading }: EscalationStatsProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
        {[...Array(6)].map((_, i) => (
          <div key={i} className="bg-card border rounded-lg p-4 animate-pulse">
            <div className="h-4 bg-muted rounded w-24 mb-2"></div>
            <div className="h-8 bg-muted rounded w-16"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!stats) return null;

  const statCards = [
    {
      label: 'Total Escalations',
      value: stats.total_escalations,
      color: 'text-foreground',
    },
    {
      label: 'Open',
      value: stats.open_escalations,
      color: 'text-blue-600 dark:text-blue-400',
    },
    {
      label: 'Resolved Today',
      value: stats.resolved_today,
      color: 'text-green-600 dark:text-green-400',
    },
    {
      label: 'Avg Resolution Time',
      value: `${Math.round(stats.average_resolution_time_minutes)}m`,
      color: 'text-purple-600 dark:text-purple-400',
    },
    {
      label: 'SLA Compliance',
      value: `${stats.sla_compliance_rate.toFixed(1)}%`,
      color: stats.sla_compliance_rate >= 90 ? 'text-green-600 dark:text-green-400' : 'text-orange-600 dark:text-orange-400',
    },
    {
      label: 'Pending Human',
      value: stats.pending_human_decision,
      color: 'text-orange-600 dark:text-orange-400',
    },
  ];

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-6 gap-4">
      {statCards.map((stat, index) => (
        <div
          key={index}
          className="bg-card border rounded-lg p-4 hover:shadow-md transition-shadow"
        >
          <div className="text-xs text-muted-foreground mb-1">{stat.label}</div>
          <div className={`text-2xl font-bold ${stat.color}`}>{stat.value}</div>
        </div>
      ))}
    </div>
  );
}
