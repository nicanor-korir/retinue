/**
 * Similar Projects Widget Component - Phase 2
 *
 * Displays similar projects and recommendations:
 * - Similar completed projects
 * - Actionable recommendations
 * - Knowledge reuse ROI
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
  AlertCircle,
  Lightbulb,
  TrendingUp,
  Loader2,
  ExternalLink,
  Target,
  DollarSign,
  Clock,
} from 'lucide-react';
import { useToast } from '@/components/error/error-toast';

interface SimilarProjectsWidgetProps {
  projectId: string;
  projectName: string;
}

interface SimilarProject {
  project_id: string;
  name: string;
  similarity_score: number;
  learnings: any[];
  metrics: {
    success_score: number;
    tasks: { completion_rate: number };
  };
}

interface Recommendation {
  title: string;
  description: string;
  category: string;
  confidence: number;
  source_projects: string[];
  evidence: string[];
}

interface KnowledgeReuse {
  project_id: string;
  similar_projects_count: number;
  average_similarity: number;
  average_success_rate: number;
  total_applicable_learnings: number;
  knowledge_reuse_potential: string;
  estimated_time_savings_hours: number;
  estimated_cost_savings_percent: number;
}

const CATEGORY_COLORS: Record<string, string> = {
  best_practice: 'bg-green-100 text-green-800',
  caution: 'bg-red-100 text-red-800',
  opportunity: 'bg-blue-100 text-blue-800',
};

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  best_practice: <Lightbulb className="h-4 w-4" />,
  caution: <AlertCircle className="h-4 w-4" />,
  opportunity: <TrendingUp className="h-4 w-4" />,
};

export function SimilarProjectsWidget({
  projectId,
  projectName,
}: SimilarProjectsWidgetProps) {
  const [similarProjects, setSimilarProjects] = useState<SimilarProject[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [knowledge, setKnowledge] = useState<KnowledgeReuse | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('similar');
  const { toast } = useToast();

  useEffect(() => {
    fetchData();
  }, [projectId]);

  const fetchData = async () => {
    setLoading(true);
    try {
      // Fetch similar projects
      const similarRes = await fetch(
        `/api/v1/projects/${projectId}/similar?top_k=5`
      );
      if (!similarRes.ok) throw new Error('Failed to fetch similar projects');
      const similarData = await similarRes.json();
      setSimilarProjects(similarData.similar_projects);

      // Fetch recommendations
      const recRes = await fetch(
        `/api/v1/projects/${projectId}/recommendations?top_k=5`
      );
      if (!recRes.ok) throw new Error('Failed to fetch recommendations');
      const recData = await recRes.json();
      setRecommendations(recData.recommendations);

      // Fetch knowledge reuse insights
      const knowledgeRes = await fetch(
        `/api/v1/projects/${projectId}/knowledge-reuse`
      );
      if (!knowledgeRes.ok) throw new Error('Failed to fetch knowledge insights');
      const knowledgeData = await knowledgeRes.json();
      setKnowledge(knowledgeData);

      toast({
        title: 'Success',
        description: 'Loaded similar projects and recommendations',
      });
    } catch (error) {
      toast({
        title: 'Error',
        description: 'Failed to load similar projects',
        variant: 'destructive',
      });
      console.error('Error fetching data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Card className="w-full">
        <CardHeader>
          <CardTitle>Similar Projects & Insights</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="w-full space-y-6">
      {/* Knowledge Reuse ROI Card */}
      {knowledge && (
        <Card className="bg-gradient-to-r from-green-50 to-emerald-50 border-green-200">
          <CardContent className="pt-6">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div>
                <p className="text-xs font-medium text-muted-foreground">
                  Similar Projects
                </p>
                <p className="text-2xl font-bold text-green-600">
                  {knowledge.similar_projects_count}
                </p>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground">
                  Avg. Similarity
                </p>
                <p className="text-2xl font-bold text-green-600">
                  {Math.round(knowledge.average_similarity * 100)}%
                </p>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground">
                  Time Savings
                </p>
                <div className="flex items-baseline gap-1">
                  <p className="text-2xl font-bold text-green-600">
                    {knowledge.estimated_time_savings_hours}
                  </p>
                  <p className="text-xs text-muted-foreground">hrs</p>
                </div>
              </div>
              <div>
                <p className="text-xs font-medium text-muted-foreground">
                  Reuse Potential
                </p>
                <Badge
                  className={`mt-1 ${
                    knowledge.knowledge_reuse_potential === 'high'
                      ? 'bg-green-600'
                      : knowledge.knowledge_reuse_potential === 'medium'
                      ? 'bg-yellow-600'
                      : 'bg-gray-600'
                  }`}
                >
                  {knowledge.knowledge_reuse_potential}
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Tabs */}
      <Tabs
        value={activeTab}
        onValueChange={setActiveTab}
        className="w-full"
      >
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="similar">
            Similar Projects ({similarProjects.length})
          </TabsTrigger>
          <TabsTrigger value="recommendations">
            Recommendations ({recommendations.length})
          </TabsTrigger>
          <TabsTrigger value="insights">Insights</TabsTrigger>
        </TabsList>

        {/* Similar Projects Tab */}
        <TabsContent value="similar" className="space-y-4">
          {similarProjects.length === 0 ? (
            <Card>
              <CardContent className="flex items-center justify-center py-12 text-muted-foreground">
                No similar projects found
              </CardContent>
            </Card>
          ) : (
            similarProjects.map((project) => (
              <Card key={project.project_id}>
                <CardContent className="pt-6">
                  <div className="space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-semibold">{project.name}</h3>
                        <p className="text-sm text-muted-foreground">
                          Success: {Math.round(project.metrics.success_score * 100)}%
                        </p>
                      </div>
                      <div className="text-right">
                        <p className="text-sm font-medium">
                          {Math.round(project.similarity_score * 100)}% Similar
                        </p>
                        <div className="w-32 h-2 bg-slate-200 rounded-full mt-2 overflow-hidden">
                          <div
                            className="h-full bg-blue-500"
                            style={{
                              width: `${project.similarity_score * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Quick Stats */}
                    <div className="grid grid-cols-3 gap-2 pt-2 border-t">
                      <div className="text-center">
                        <p className="text-xs text-muted-foreground">Learnings</p>
                        <p className="text-lg font-semibold">
                          {project.learnings.length}
                        </p>
                      </div>
                      <div className="text-center">
                        <p className="text-xs text-muted-foreground">Completion</p>
                        <p className="text-lg font-semibold">
                          {Math.round(project.metrics.tasks.completion_rate * 100)}%
                        </p>
                      </div>
                      <Button
                        size="sm"
                        variant="ghost"
                        className="col-span-1 h-auto flex flex-col"
                      >
                        <ExternalLink className="h-4 w-4" />
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        {/* Recommendations Tab */}
        <TabsContent value="recommendations" className="space-y-4">
          {recommendations.length === 0 ? (
            <Card>
              <CardContent className="flex items-center justify-center py-12 text-muted-foreground">
                No recommendations available
              </CardContent>
            </Card>
          ) : (
            recommendations.map((rec, index) => (
              <Card key={index}>
                <CardContent className="pt-6">
                  <div className="space-y-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-start gap-3 flex-1">
                        <div
                          className={`rounded-full p-2 ${CATEGORY_COLORS[rec.category]}`}
                        >
                          {CATEGORY_ICONS[rec.category]}
                        </div>
                        <div>
                          <h3 className="font-semibold">{rec.title}</h3>
                          <p className="text-sm text-muted-foreground">
                            {rec.description}
                          </p>
                        </div>
                      </div>
                      <div className="text-right ml-4">
                        <p className="text-sm font-medium">
                          {Math.round(rec.confidence * 100)}% Confidence
                        </p>
                        <div className="w-24 h-2 bg-slate-200 rounded-full mt-2 overflow-hidden">
                          <div
                            className="h-full bg-green-500"
                            style={{
                              width: `${rec.confidence * 100}%`,
                            }}
                          />
                        </div>
                      </div>
                    </div>

                    {/* Evidence */}
                    {rec.evidence.length > 0 && (
                      <div className="mt-3 pt-3 border-t">
                        <p className="text-xs font-medium text-muted-foreground mb-2">
                          Evidence:
                        </p>
                        <ul className="text-sm text-muted-foreground space-y-1">
                          {rec.evidence.map((item, idx) => (
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
            ))
          )}
        </TabsContent>

        {/* Insights Tab */}
        <TabsContent value="insights" className="space-y-4">
          {knowledge ? (
            <>
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Knowledge Reuse Metrics</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="rounded-lg border p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <Clock className="h-4 w-4 text-blue-600" />
                        <p className="text-sm font-medium">Estimated Time Savings</p>
                      </div>
                      <p className="text-2xl font-bold">
                        {knowledge.estimated_time_savings_hours}
                        <span className="text-sm text-muted-foreground ml-1">hours</span>
                      </p>
                    </div>

                    <div className="rounded-lg border p-4">
                      <div className="flex items-center gap-2 mb-2">
                        <DollarSign className="h-4 w-4 text-green-600" />
                        <p className="text-sm font-medium">Cost Savings</p>
                      </div>
                      <p className="text-2xl font-bold">
                        {knowledge.estimated_cost_savings_percent}
                        <span className="text-sm text-muted-foreground ml-1">%</span>
                      </p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">
                        Applicable Learnings
                      </p>
                      <p className="text-2xl font-bold">
                        {knowledge.total_applicable_learnings}
                      </p>
                    </div>

                    <div>
                      <p className="text-sm font-medium text-muted-foreground">
                        Avg. Success Rate
                      </p>
                      <p className="text-2xl font-bold">
                        {Math.round(knowledge.average_success_rate * 100)}%
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Recommendation</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="rounded-lg bg-blue-50 p-4 border border-blue-200">
                    <p className="text-sm text-blue-900">
                      <span className="font-semibold">
                        {knowledge.knowledge_reuse_potential.toUpperCase()}
                      </span>{' '}
                      Knowledge Reuse Potential:{' '}
                      {knowledge.knowledge_reuse_potential === 'high'
                        ? 'Consider applying learnings from similar projects to potentially save time and reduce costs.'
                        : knowledge.knowledge_reuse_potential === 'medium'
                        ? 'Some learnings from similar projects may be applicable to this project.'
                        : 'Limited opportunities for knowledge reuse from similar projects.'}
                    </p>
                  </div>
                </CardContent>
              </Card>
            </>
          ) : (
            <Card>
              <CardContent className="flex items-center justify-center py-12 text-muted-foreground">
                No insights available
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
