'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { MessageCircle, Star, AlertCircle, TrendingUp, CheckCircle } from 'lucide-react';
import axios from 'axios';

interface Feedback {
  feedback_id: string;
  title: string;
  description: string;
  type: string;
  status: string;
  priority: string;
  quality_rating?: number;
  satisfaction_rating?: number;
  output_quality?: number;
  correctness?: number;
  completeness?: number;
  implementation_quality?: number;
  decision_quality?: number;
  execution_quality?: number;
  communication_clarity?: number;
  created_at: string;
}

interface FeedbackDisplayProps {
  entityType: 'project' | 'task' | 'agent';
  entityId: string;
}

const PRIORITY_COLORS: Record<string, string> = {
  low: 'bg-blue-100 text-blue-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
};

const STATUS_ICONS: Record<string, JSX.Element> = {
  pending: <MessageCircle className="h-4 w-4" />,
  acknowledged: <CheckCircle className="h-4 w-4" />,
  in_progress: <TrendingUp className="h-4 w-4" />,
  implemented: <CheckCircle className="h-4 w-4 text-green-600" />,
  resolved: <CheckCircle className="h-4 w-4 text-green-600" />,
};

const FEEDBACK_TYPE_ICONS: Record<string, string> = {
  general: '💬',
  quality: '⭐',
  correctness: '✓',
  completeness: '📋',
  direction: '🎯',
  implementation: '⚙️',
  blocking_issue: '🚫',
  enhancement: '✨',
  bug_report: '🐛',
  performance: '⚡',
};

export function FeedbackDisplay({ entityType, entityId }: FeedbackDisplayProps) {
  const [feedbacks, setFeedbacks] = useState<Feedback[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchFeedback();
  }, [entityType, entityId]);

  const fetchFeedback = async () => {
    try {
      setIsLoading(true);
      setError(null);

      let endpoint = '';
      if (entityType === 'project') {
        endpoint = `/api/v1/projects/${entityId}/feedback`;
      } else if (entityType === 'task') {
        endpoint = `/api/v1/tasks/${entityId}/feedback`;
      } else if (entityType === 'agent') {
        endpoint = `/api/v1/agents/${entityId}/feedback`;
      }

      const response = await axios.get(endpoint);
      setFeedbacks(response.data.feedback || []);
    } catch (err) {
      console.error('Failed to fetch feedback:', err);
      setError('Failed to load feedback');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="h-5 w-5" />
            Feedback ({feedbacks.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-gray-500">Loading feedback...</div>
        </CardContent>
      </Card>
    );
  }

  if (feedbacks.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageCircle className="h-5 w-5" />
            Feedback
          </CardTitle>
          <CardDescription>No feedback yet</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-gray-500 py-4">
            No feedback has been provided. Start by sharing your thoughts and suggestions!
          </div>
        </CardContent>
      </Card>
    );
  }

  // Calculate summary statistics
  const summaryStats = {
    total: feedbacks.length,
    avgQuality:
      entityType === 'project'
        ? (
            feedbacks.reduce((sum, f) => sum + (f.quality_rating || 0), 0) / feedbacks.filter((f) => f.quality_rating).length
          ).toFixed(1)
        : undefined,
    blockers: feedbacks.filter((f) => f.type === 'blocking_issue').length,
    enhancements: feedbacks.filter((f) => f.type === 'enhancement').length,
    criticalCount: feedbacks.filter((f) => f.priority === 'critical').length,
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <MessageCircle className="h-5 w-5" />
          Feedback Summary
        </CardTitle>
        <CardDescription>
          {summaryStats.total} feedback item{summaryStats.total !== 1 ? 's' : ''} received
        </CardDescription>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-4">
          {summaryStats.avgQuality && (
            <div className="p-2 bg-blue-50 rounded-lg">
              <div className="text-xs text-gray-600">Avg Quality</div>
              <div className="text-lg font-semibold">{summaryStats.avgQuality}/5</div>
            </div>
          )}
          {summaryStats.blockers > 0 && (
            <div className="p-2 bg-red-50 rounded-lg">
              <div className="text-xs text-gray-600">Blockers</div>
              <div className="text-lg font-semibold text-red-600">{summaryStats.blockers}</div>
            </div>
          )}
          {summaryStats.enhancements > 0 && (
            <div className="p-2 bg-green-50 rounded-lg">
              <div className="text-xs text-gray-600">Enhancements</div>
              <div className="text-lg font-semibold text-green-600">{summaryStats.enhancements}</div>
            </div>
          )}
          {summaryStats.criticalCount > 0 && (
            <div className="p-2 bg-orange-50 rounded-lg">
              <div className="text-xs text-gray-600">Critical</div>
              <div className="text-lg font-semibold text-orange-600">{summaryStats.criticalCount}</div>
            </div>
          )}
        </div>
      </CardHeader>

      <CardContent>
        <div className="space-y-3 max-h-96 overflow-y-auto">
          {feedbacks.map((feedback) => (
            <div key={feedback.feedback_id} className="p-3 border rounded-lg hover:bg-gray-50 transition-colors">
              {/* Header */}
              <div className="flex items-start justify-between gap-2 mb-2">
                <div className="flex items-start gap-2 flex-1 min-w-0">
                  <span className="text-lg">{FEEDBACK_TYPE_ICONS[feedback.type] || '💬'}</span>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-medium text-sm leading-tight">{feedback.title}</h4>
                    <div className="flex items-center gap-2 flex-wrap mt-1">
                      <Badge variant="secondary" className="text-xs">
                        {feedback.type.replace(/_/g, ' ')}
                      </Badge>
                      <Badge className={`text-xs ${PRIORITY_COLORS[feedback.priority]}`}>
                        {feedback.priority}
                      </Badge>
                      <div className="flex items-center gap-1 text-xs text-gray-600">
                        {STATUS_ICONS[feedback.status] || <MessageCircle className="h-3 w-3" />}
                        <span>{feedback.status}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Description */}
              <p className="text-sm text-gray-700 mb-2 line-clamp-2">{feedback.description}</p>

              {/* Ratings if available */}
              {(feedback.quality_rating ||
                feedback.satisfaction_rating ||
                feedback.output_quality ||
                feedback.correctness ||
                feedback.completeness ||
                feedback.implementation_quality ||
                feedback.decision_quality ||
                feedback.execution_quality ||
                feedback.communication_clarity) && (
                <div className="mt-2 pt-2 border-t">
                  <div className="flex flex-wrap gap-2">
                    {feedback.quality_rating && (
                      <div className="text-xs bg-blue-50 px-2 py-1 rounded">
                        Quality: <span className="font-semibold">{feedback.quality_rating}/5</span>
                      </div>
                    )}
                    {feedback.satisfaction_rating && (
                      <div className="text-xs bg-purple-50 px-2 py-1 rounded">
                        Satisfaction: <span className="font-semibold">{feedback.satisfaction_rating}/5</span>
                      </div>
                    )}
                    {feedback.output_quality && (
                      <div className="text-xs bg-blue-50 px-2 py-1 rounded">
                        Output: <span className="font-semibold">{feedback.output_quality}/5</span>
                      </div>
                    )}
                    {feedback.correctness && (
                      <div className="text-xs bg-green-50 px-2 py-1 rounded">
                        Correct: <span className="font-semibold">{feedback.correctness}/5</span>
                      </div>
                    )}
                    {feedback.completeness && (
                      <div className="text-xs bg-yellow-50 px-2 py-1 rounded">
                        Complete: <span className="font-semibold">{feedback.completeness}/5</span>
                      </div>
                    )}
                    {feedback.decision_quality && (
                      <div className="text-xs bg-orange-50 px-2 py-1 rounded">
                        Decisions: <span className="font-semibold">{feedback.decision_quality}/5</span>
                      </div>
                    )}
                    {feedback.execution_quality && (
                      <div className="text-xs bg-cyan-50 px-2 py-1 rounded">
                        Execution: <span className="font-semibold">{feedback.execution_quality}/5</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Timestamp */}
              <div className="text-xs text-gray-500 mt-2">
                {new Date(feedback.created_at).toLocaleDateString()} {new Date(feedback.created_at).toLocaleTimeString()}
              </div>
            </div>
          ))}
        </div>

        {error && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex gap-2 mt-4">
            <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
            <div>{error}</div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
