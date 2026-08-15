'use client';

import { useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';
import { Badge } from '@/components/ui/badge';
import { TrendingUp, TrendingDown, AlertTriangle, CheckCircle, Clock } from 'lucide-react';
import { ProjectFeedback } from '@/hooks/useFeedback';

interface ProjectHealthProps {
  feedback: ProjectFeedback[];
  projectStatus?: string;
}

interface HealthMetrics {
  overallScore: number;
  qualityTrend: 'up' | 'down' | 'stable';
  averageQuality: number;
  satisfactionLevel: number;
  criticalIssues: number;
  recommendations: string[];
  healthStatus: 'excellent' | 'good' | 'fair' | 'poor';
}

function calculateHealthMetrics(feedback: ProjectFeedback[]): HealthMetrics {
  if (feedback.length === 0) {
    return {
      overallScore: 0,
      qualityTrend: 'stable',
      averageQuality: 0,
      satisfactionLevel: 0,
      criticalIssues: 0,
      recommendations: ['No feedback yet. Encourage team to provide feedback.'],
      healthStatus: 'fair',
    };
  }

  // Calculate quality scores
  const qualityRatings = feedback
    .filter((f) => f.quality_rating !== null)
    .map((f) => f.quality_rating || 0);

  const satisfactionRatings = feedback
    .filter((f) => f.satisfaction_rating !== null)
    .map((f) => f.satisfaction_rating || 0);

  const averageQuality =
    qualityRatings.length > 0 ? qualityRatings.reduce((a, b) => a + b, 0) / qualityRatings.length : 0;

  const satisfactionLevel =
    satisfactionRatings.length > 0
      ? satisfactionRatings.reduce((a, b) => a + b, 0) / satisfactionRatings.length
      : 0;

  // Count issues by type
  const criticalIssues = feedback.filter((f) => f.priority === 'critical').length;
  const blockingIssues = feedback.filter((f) => f.type === 'blocking_issue').length;
  const enhancementRequests = feedback.filter((f) => f.type === 'enhancement').length;

  // Determine trend (recent vs older feedback)
  const recentFeedback = feedback.slice(0, Math.ceil(feedback.length / 2));
  const olderFeedback = feedback.slice(Math.ceil(feedback.length / 2));

  const recentQuality =
    recentFeedback.length > 0
      ? recentFeedback
          .filter((f) => f.quality_rating)
          .reduce((sum, f) => sum + (f.quality_rating || 0), 0) / recentFeedback.length
      : 0;

  const olderQuality =
    olderFeedback.length > 0
      ? olderFeedback
          .filter((f) => f.quality_rating)
          .reduce((sum, f) => sum + (f.quality_rating || 0), 0) / olderFeedback.length
      : 0;

  const qualityTrend: 'up' | 'down' | 'stable' =
    Math.abs(recentQuality - olderQuality) < 0.5 ? 'stable' : recentQuality > olderQuality ? 'up' : 'down';

  // Overall score calculation
  const weightedScore =
    averageQuality * 0.5 +
    satisfactionLevel * 0.3 +
    Math.max(0, 5 - blockingIssues) * 0.2;

  const overallScore = Math.min(100, (weightedScore / 5) * 100);

  // Determine health status
  let healthStatus: 'excellent' | 'good' | 'fair' | 'poor' = 'excellent';
  if (overallScore < 40) {
    healthStatus = 'poor';
  } else if (overallScore < 60) {
    healthStatus = 'fair';
  } else if (overallScore < 80) {
    healthStatus = 'good';
  }

  // Generate recommendations
  const recommendations: string[] = [];

  if (blockingIssues > 0) {
    recommendations.push(`${blockingIssues} blocking issue${blockingIssues > 1 ? 's' : ''} need immediate attention`);
  }

  if (averageQuality < 3) {
    recommendations.push('Quality needs improvement - focus on output standards');
  }

  if (satisfactionLevel < 2.5) {
    recommendations.push('User satisfaction is low - review feedback for common complaints');
  }

  if (enhancementRequests > 2) {
    recommendations.push(`${enhancementRequests} enhancement requests pending - prioritize implementations`);
  }

  if (criticalIssues > 0) {
    recommendations.push(`${criticalIssues} critical issue${criticalIssues > 1 ? 's' : ''} to resolve`);
  }

  if (recommendations.length === 0) {
    recommendations.push('Project health is good! Continue monitoring feedback.');
  }

  return {
    overallScore,
    qualityTrend,
    averageQuality: Math.round(averageQuality * 10) / 10,
    satisfactionLevel: Math.round(satisfactionLevel * 10) / 10,
    criticalIssues,
    recommendations,
    healthStatus,
  };
}

export function ProjectHealth({ feedback, projectStatus }: ProjectHealthProps) {
  const metrics = useMemo(() => calculateHealthMetrics(feedback), [feedback]);

  const healthColors = {
    excellent: {
      bg: 'bg-green-50',
      border: 'border-green-200',
      badge: 'bg-green-100 text-green-800',
      progress: 'bg-green-600',
    },
    good: {
      bg: 'bg-blue-50',
      border: 'border-blue-200',
      badge: 'bg-blue-100 text-blue-800',
      progress: 'bg-blue-600',
    },
    fair: {
      bg: 'bg-yellow-50',
      border: 'border-yellow-200',
      badge: 'bg-yellow-100 text-yellow-800',
      progress: 'bg-yellow-600',
    },
    poor: {
      bg: 'bg-red-50',
      border: 'border-red-200',
      badge: 'bg-red-100 text-red-800',
      progress: 'bg-red-600',
    },
  };

  const colors = healthColors[metrics.healthStatus];

  return (
    <Card className={`${colors.bg} border ${colors.border}`}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              {metrics.healthStatus === 'excellent' || metrics.healthStatus === 'good' ? (
                <CheckCircle className="h-5 w-5 text-green-600" />
              ) : metrics.healthStatus === 'fair' ? (
                <Clock className="h-5 w-5 text-yellow-600" />
              ) : (
                <AlertTriangle className="h-5 w-5 text-red-600" />
              )}
              Project Health
            </CardTitle>
            <CardDescription>Based on {feedback.length} feedback item(s)</CardDescription>
          </div>
          <Badge className={colors.badge}>{metrics.healthStatus.toUpperCase()}</Badge>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Overall Score */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm font-semibold">Overall Health Score</span>
            <span className="text-2xl font-bold">{Math.round(metrics.overallScore)}%</span>
          </div>
          <Progress value={metrics.overallScore} className="h-3" />
        </div>

        {/* Metrics Grid */}
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          {/* Quality Rating */}
          <div className="p-3 bg-white rounded-lg border border-gray-200">
            <div className="text-xs text-gray-600 mb-1">Avg Quality</div>
            <div className="flex items-baseline justify-between">
              <span className="text-2xl font-bold">{metrics.averageQuality}</span>
              <span className="text-xs text-gray-600">/5</span>
            </div>
            <div className="text-xs mt-1">
              {metrics.qualityTrend === 'up' ? (
                <span className="text-green-600 flex items-center gap-1">
                  <TrendingUp className="h-3 w-3" /> Improving
                </span>
              ) : metrics.qualityTrend === 'down' ? (
                <span className="text-red-600 flex items-center gap-1">
                  <TrendingDown className="h-3 w-3" /> Declining
                </span>
              ) : (
                <span className="text-gray-600">Stable</span>
              )}
            </div>
          </div>

          {/* Satisfaction */}
          <div className="p-3 bg-white rounded-lg border border-gray-200">
            <div className="text-xs text-gray-600 mb-1">Satisfaction</div>
            <div className="flex items-baseline justify-between">
              <span className="text-2xl font-bold">{metrics.satisfactionLevel}</span>
              <span className="text-xs text-gray-600">/5</span>
            </div>
            <div className="text-xs mt-1 text-gray-600">
              {metrics.satisfactionLevel >= 4 ? '😊 Happy' : metrics.satisfactionLevel >= 3 ? '😐 Okay' : '😞 Unhappy'}
            </div>
          </div>

          {/* Issues Count */}
          <div className="p-3 bg-white rounded-lg border border-gray-200">
            <div className="text-xs text-gray-600 mb-1">Critical Issues</div>
            <div className="text-2xl font-bold text-red-600">{metrics.criticalIssues}</div>
            <div className="text-xs mt-1 text-gray-600">Requiring action</div>
          </div>

          {/* Feedback Count */}
          <div className="p-3 bg-white rounded-lg border border-gray-200">
            <div className="text-xs text-gray-600 mb-1">Total Feedback</div>
            <div className="text-2xl font-bold">{feedback.length}</div>
            <div className="text-xs mt-1 text-gray-600">Items received</div>
          </div>
        </div>

        {/* Recommendations */}
        <div>
          <h4 className="font-semibold text-sm mb-2">Recommendations</h4>
          <div className="space-y-2">
            {metrics.recommendations.map((rec, idx) => (
              <div key={idx} className="flex gap-2 p-2 bg-white rounded border border-gray-200 text-sm">
                <span className="text-lg">💡</span>
                <span className="text-gray-700">{rec}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Status Integration */}
        {projectStatus && (
          <div className="text-xs text-gray-600 pt-2 border-t border-gray-200">
            <span className="font-medium">Project Status:</span> {projectStatus}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
