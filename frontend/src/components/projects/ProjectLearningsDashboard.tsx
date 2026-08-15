/**
 * Project Learnings Dashboard Component - Phase 2
 *
 * Displays learnings extracted from completed projects:
 * - Best practices discovered
 * - Quality metrics
 * - Risk analysis
 * - Success scores
 */

import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '@/components/ui/tabs';
import {
  BarChart,
  Bar,
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import {
  Lightbulb,
  TrendingUp,
  AlertTriangle,
  CheckCircle2,
  Loader2,
  RefreshCw,
} from 'lucide-react';
import { useToast } from '@/components/error/error-toast';

interface ProjectLearningsDashboardProps {
  projectId: string;
  projectName: string;
}

interface Learning {
  learning_type: string;
  title: string;
  description: string;
  evidence: string[];
  relevance_score: number;
  tags: string[];
}

interface Metrics {
  project_id: string;
  timeline: {
    planned_days: number;
    actual_days: number;
    efficiency: number;
  };
  tasks: {
    total: number;
    completed: number;
    completion_rate: number;
  };
  decisions: {
    total: number;
    approved: number;
    approval_rate: number;
  };
  escalations: {
    total: number;
    resolved: number;
    resolution_rate: number;
  };
  success_score: number;
}

interface ProjectLearningsData {
  project_id: string;
  total_learnings: number;
  by_type: Record<string, number>;
  learnings: Learning[];
}

const LEARNING_COLORS: Record<string, string> = {
  best_practice: '#10b981',
  pattern: '#3b82f6',
  risk: '#ef4444',
  improvement: '#f59e0b',
};

const LEARNING_ICONS: Record<string, React.ReactNode> = {
  best_practice: <CheckCircle2 className="h-4 w-4" />,
  pattern: <TrendingUp className="h-4 w-4" />,
  risk: <AlertTriangle className="h-4 w-4" />,
  improvement: <Lightbulb className="h-4 w-4" />,
};

export function ProjectLearningsDashboard({
  projectId,
  projectName,
}: ProjectLearningsDashboardProps) {
  const [learnings, setLearnings] = useState<ProjectLearningsData | null>(null);
  const [metrics, setMetrics] = useState<Metrics | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedType, setSelectedType] = useState<string | null>(null);
  const { toast } = useToast();

  useEffect(() => {
    fetchLearnings();
  }, [projectId]);

  const fetchLearnings = async () => {
    setLoading(true);
    try {
      // Fetch learnings
      const learningsRes = await fetch(
        `/api/v1/projects/${projectId}/learnings/extract`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ include_metrics: true }),
        }
      );

      if (!learningsRes.ok) throw new Error('Failed to fetch learnings');
      const learningsData = await learningsRes.json();
      setLearnings(learningsData);

      // Fetch metrics
      const metricsRes = await fetch(
        `/api/v1/projects/${projectId}/metrics`
      );

      if (!metricsRes.ok) throw new Error('Failed to fetch metrics');
      const metricsData = await metricsRes.json();
      setMetrics(metricsData);

      toast({
        title: 'Success',
        description: `Extracted ${learningsData.total_learnings} learnings from project`,
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to fetch learnings',
        variant: 'destructive',
      });
      console.error('Error fetching learnings:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Project Learnings</CardTitle>
          <CardDescription>{projectName}</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    );
  }

  if (!learnings) {
    return (
      <Card className="w-full border-red-200 bg-red-50">
        <CardHeader>
          <CardTitle className="text-red-900">Project Learnings</CardTitle>
          <CardDescription className="text-red-800">
            Failed to load learnings
          </CardDescription>
        </CardHeader>
      </Card>
    );
  }

  // Prepare chart data
  const learningsTypeData = Object.entries(learnings.by_type).map(
    ([type, count]) => ({
      name: type.replace('_', ' '),
      value: count,
      color: LEARNING_COLORS[type] || '#6b7280',
    })
  );

  const metricsData = metrics
    ? [
        {
          name: 'Timeline Efficiency',
          value: Math.round(metrics.timeline.efficiency * 100),
        },
        {
          name: 'Task Completion',
          value: Math.round(metrics.tasks.completion_rate * 100),
        },
        {
          name: 'Decision Quality',
          value: Math.round(metrics.decisions.approval_rate * 100),
        },
        {
          name: 'Escalation Resolution',
          value: Math.round(metrics.escalations.resolution_rate * 100),
        },
      ]
    : [];

  const filteredLearnings = selectedType
    ? learnings.learnings.filter((l) => l.learning_type === selectedType)
    : learnings.learnings;

  return (
    <div className="w-full space-y-6">
      {/* Header */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between space-y-0">
          <div>
            <CardTitle>Project Learnings</CardTitle>
            <CardDescription>{projectName}</CardDescription>
          </div>
          <Button
            onClick={fetchLearnings}
            variant="outline"
            size="sm"
            className="gap-2"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </Button>
        </CardHeader>
      </Card>

      {/* Success Score */}
      {metrics && (
        <Card className="bg-gradient-to-r from-blue-50 to-indigo-50">
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-muted-foreground">
                  Project Success Score
                </p>
                <p className="text-4xl font-bold text-blue-600">
                  {Math.round(metrics.success_score * 100)}%
                </p>
              </div>
              <div className="text-right space-y-2">
                <div className="text-sm">
                  <span className="text-muted-foreground">Tasks: </span>
                  <span className="font-medium">
                    {metrics.tasks.completed}/{metrics.tasks.total}
                  </span>
                </div>
                <div className="text-sm">
                  <span className="text-muted-foreground">Days: </span>
                  <span className="font-medium">
                    {metrics.timeline.actual_days}/{metrics.timeline.planned_days}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Metrics Charts */}
      {metrics && (
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">Performance Metrics</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={metricsData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" fontSize={12} />
                <YAxis domain={[0, 100]} />
                <Tooltip formatter={(value) => `${value}%`} />
                <Bar dataKey="value" fill="#3b82f6" radius={[8, 8, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      )}

      {/* Learnings Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">
            Learnings Overview ({learnings.total_learnings})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {learningsTypeData.map((type) => (
              <div
                key={type.name}
                className="rounded-lg border p-4 text-center cursor-pointer hover:bg-slate-50 transition"
                onClick={() =>
                  setSelectedType(
                    selectedType === type.name.toLowerCase().replace(' ', '_')
                      ? null
                      : type.name.toLowerCase().replace(' ', '_')
                  )
                }
              >
                <p className="text-2xl font-bold" style={{ color: type.color }}>
                  {type.value}
                </p>
                <p className="text-xs text-muted-foreground mt-1">
                  {type.name}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Learnings List */}
      <Tabs defaultValue="all" className="w-full">
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="all">All</TabsTrigger>
          <TabsTrigger value="best_practice">Best Practices</TabsTrigger>
          <TabsTrigger value="pattern">Patterns</TabsTrigger>
          <TabsTrigger value="risk">Risks</TabsTrigger>
          <TabsTrigger value="improvement">Improvements</TabsTrigger>
        </TabsList>

        <TabsContent value="all" className="space-y-4">
          <LearningsList learnings={learnings.learnings} />
        </TabsContent>

        <TabsContent value="best_practice" className="space-y-4">
          <LearningsList
            learnings={learnings.learnings.filter(
              (l) => l.learning_type === 'best_practice'
            )}
          />
        </TabsContent>

        <TabsContent value="pattern" className="space-y-4">
          <LearningsList
            learnings={learnings.learnings.filter(
              (l) => l.learning_type === 'pattern'
            )}
          />
        </TabsContent>

        <TabsContent value="risk" className="space-y-4">
          <LearningsList
            learnings={learnings.learnings.filter(
              (l) => l.learning_type === 'risk'
            )}
          />
        </TabsContent>

        <TabsContent value="improvement" className="space-y-4">
          <LearningsList
            learnings={learnings.learnings.filter(
              (l) => l.learning_type === 'improvement'
            )}
          />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function LearningsList({ learnings }: { learnings: Learning[] }) {
  if (learnings.length === 0) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center py-12 text-muted-foreground">
          No learnings found
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {learnings.map((learning, index) => (
        <Card key={index}>
          <CardContent className="pt-6">
            <div className="space-y-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-3">
                  <div
                    className="rounded-full p-2"
                    style={{
                      backgroundColor: `${LEARNING_COLORS[learning.learning_type] || '#6b7280'}20`,
                    }}
                  >
                    {LEARNING_ICONS[learning.learning_type]}
                  </div>
                  <div>
                    <h3 className="font-semibold">{learning.title}</h3>
                    <p className="text-sm text-muted-foreground">
                      {learning.description}
                    </p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm font-medium">
                    {Math.round(learning.relevance_score * 100)}% Relevant
                  </p>
                  <div className="w-20 h-1 bg-slate-200 rounded-full mt-1 overflow-hidden">
                    <div
                      className="h-full bg-blue-500"
                      style={{
                        width: `${learning.relevance_score * 100}%`,
                      }}
                    />
                  </div>
                </div>
              </div>

              {/* Tags */}
              <div className="flex flex-wrap gap-2">
                {learning.tags.map((tag) => (
                  <Badge key={tag} variant="secondary" className="text-xs">
                    {tag}
                  </Badge>
                ))}
              </div>

              {/* Evidence */}
              {learning.evidence.length > 0 && (
                <div className="mt-3 pt-3 border-t">
                  <p className="text-xs font-medium text-muted-foreground mb-2">
                    Evidence:
                  </p>
                  <ul className="text-sm text-muted-foreground space-y-1">
                    {learning.evidence.map((item, idx) => (
                      <li key={idx} className="flex items-start gap-2">
                        <span className="text-xs mt-1">•</span>
                        <span>{item}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
