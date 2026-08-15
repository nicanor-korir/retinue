/**
 * Knowledge Entry Detail Component
 *
 * Displays full knowledge entry with feedback options and usage tracking.
 */

'use client';

import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Star, Calendar, User, Tag, TrendingUp, Share2, Copy, Check } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Separator } from '@/components/ui/separator';
import { Textarea } from '@/components/ui/textarea';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { useKnowledgeEntry, useKnowledgeFeedback } from '@/hooks/useKnowledge';
import { Skeleton } from '@/components/ui/skeleton';
import ReactMarkdown from 'react-markdown';

interface KnowledgeDetailProps {
  entryId: string;
  userId?: string;
  agentId?: string;
}

export function KnowledgeDetail({ entryId, userId, agentId }: KnowledgeDetailProps) {
  const { data: entry, isLoading } = useKnowledgeEntry(entryId, { userId, agentId });
  const feedbackMutation = useKnowledgeFeedback();

  const [feedbackDialog, setFeedbackDialog] = useState(false);
  const [feedbackType, setFeedbackType] = useState<'helpful' | 'not_helpful' | null>(null);
  const [feedbackComment, setFeedbackComment] = useState('');
  const [copied, setCopied] = useState(false);

  const handleFeedback = async (type: 'helpful' | 'not_helpful', rating?: number) => {
    if (!entry) return;

    await feedbackMutation.mutateAsync({
      entry_id: entry.entry_id,
      feedback_type: type,
      rating,
      comment: feedbackComment || undefined,
      user_id: userId,
      agent_id: agentId,
    });

    setFeedbackDialog(false);
    setFeedbackComment('');
    setFeedbackType(null);
  };

  const handleCopy = () => {
    if (entry?.content) {
      navigator.clipboard.writeText(entry.content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <Skeleton className="h-6 w-3/4" />
          <Skeleton className="h-4 w-1/2" />
        </CardHeader>
        <CardContent className="space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-24 w-full" />
        </CardContent>
      </Card>
    );
  }

  if (!entry) {
    return (
      <Card>
        <CardContent className="py-8 text-center">
          <p className="text-muted-foreground">Knowledge entry not found</p>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-2">
            <div className="flex items-center gap-2 flex-wrap">
              <CardTitle>{entry.title}</CardTitle>
              <Badge variant="outline" className={getTypeColor(entry.entry_type)}>
                {entry.entry_type.replace('_', ' ')}
              </Badge>
              {entry.validation_status && (
                <Badge variant="outline" className={getValidationColor(entry.validation_status)}>
                  {entry.validation_status.replace('_', ' ')}
                </Badge>
              )}
            </div>
            {entry.summary && (
              <CardDescription>{entry.summary}</CardDescription>
            )}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
            >
              {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            </Button>
            <Button variant="outline" size="sm">
              <Share2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* Content */}
        <div className="prose prose-sm dark:prose-invert max-w-none">
          <ReactMarkdown>{entry.content}</ReactMarkdown>
        </div>

        <Separator />

        {/* Metadata Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard
            icon={<TrendingUp className="h-4 w-4" />}
            label="Quality Score"
            value={`${(entry.quality_score * 100).toFixed(0)}%`}
          />
          <MetricCard
            icon={<ThumbsUp className="h-4 w-4" />}
            label="Helpfulness"
            value={`${entry.helpfulness_up} / ${entry.helpfulness_up + entry.helpfulness_down}`}
          />
          <MetricCard
            icon={<Star className="h-4 w-4" />}
            label="Times Used"
            value={entry.use_count.toString()}
          />
          <MetricCard
            icon={<Calendar className="h-4 w-4" />}
            label="Created"
            value={new Date(entry.created_at).toLocaleDateString()}
          />
        </div>

        <Separator />

        {/* Tags */}
        {entry.tags && entry.tags.length > 0 && (
          <div>
            <h3 className="text-sm font-medium mb-2 flex items-center gap-2">
              <Tag className="h-4 w-4" />
              Tags
            </h3>
            <div className="flex flex-wrap gap-2">
              {entry.tags.map((tag: string) => (
                <Badge key={tag} variant="secondary">
                  {tag}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* Problem Context */}
        {entry.problem_context && (
          <div>
            <h3 className="text-sm font-medium mb-2">Problem Context</h3>
            <p className="text-sm text-muted-foreground">{entry.problem_context}</p>
          </div>
        )}

        {/* Applicable Scenarios */}
        {entry.applicable_scenarios && entry.applicable_scenarios.length > 0 && (
          <div>
            <h3 className="text-sm font-medium mb-2">Applicable Scenarios</h3>
            <ul className="list-disc list-inside space-y-1">
              {entry.applicable_scenarios.map((scenario: string, idx: number) => (
                <li key={idx} className="text-sm text-muted-foreground">
                  {scenario}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Prerequisites */}
        {entry.prerequisites && entry.prerequisites.length > 0 && (
          <div>
            <h3 className="text-sm font-medium mb-2">Prerequisites</h3>
            <ul className="list-disc list-inside space-y-1">
              {entry.prerequisites.map((prereq: string, idx: number) => (
                <li key={idx} className="text-sm text-muted-foreground">
                  {prereq}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Limitations */}
        {entry.limitations && entry.limitations.length > 0 && (
          <div>
            <h3 className="text-sm font-medium mb-2">Limitations</h3>
            <ul className="list-disc list-inside space-y-1">
              {entry.limitations.map((limitation: string, idx: number) => (
                <li key={idx} className="text-sm text-muted-foreground">
                  {limitation}
                </li>
              ))}
            </ul>
          </div>
        )}

        <Separator />

        {/* Feedback Actions */}
        <div className="flex items-center justify-between">
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => handleFeedback('helpful')}
              disabled={feedbackMutation.isPending}
            >
              <ThumbsUp className="h-4 w-4 mr-2" />
              Helpful
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setFeedbackType('not_helpful');
                setFeedbackDialog(true);
              }}
              disabled={feedbackMutation.isPending}
            >
              <ThumbsDown className="h-4 w-4 mr-2" />
              Not Helpful
            </Button>
          </div>

          <Dialog open={feedbackDialog} onOpenChange={setFeedbackDialog}>
            <DialogTrigger asChild>
              <Button variant="ghost" size="sm">
                Leave Feedback
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Provide Feedback</DialogTitle>
                <DialogDescription>
                  Help us improve this knowledge entry
                </DialogDescription>
              </DialogHeader>
              <div className="space-y-4">
                <div className="flex gap-2">
                  <Button
                    variant={feedbackType === 'helpful' ? 'default' : 'outline'}
                    onClick={() => setFeedbackType('helpful')}
                    className="flex-1"
                  >
                    <ThumbsUp className="h-4 w-4 mr-2" />
                    Helpful
                  </Button>
                  <Button
                    variant={feedbackType === 'not_helpful' ? 'default' : 'outline'}
                    onClick={() => setFeedbackType('not_helpful')}
                    className="flex-1"
                  >
                    <ThumbsDown className="h-4 w-4 mr-2" />
                    Not Helpful
                  </Button>
                </div>

                <Textarea
                  placeholder="Additional comments (optional)"
                  value={feedbackComment}
                  onChange={(e) => setFeedbackComment(e.target.value)}
                  rows={4}
                />

                <div className="flex justify-end gap-2">
                  <Button
                    variant="outline"
                    onClick={() => setFeedbackDialog(false)}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={() => {
                      if (feedbackType) {
                        handleFeedback(feedbackType);
                      }
                    }}
                    disabled={!feedbackType || feedbackMutation.isPending}
                  >
                    Submit Feedback
                  </Button>
                </div>
              </div>
            </DialogContent>
          </Dialog>
        </div>
      </CardContent>
    </Card>
  );
}

interface MetricCardProps {
  icon: React.ReactNode;
  label: string;
  value: string;
}

function MetricCard({ icon, label, value }: MetricCardProps) {
  return (
    <div className="flex flex-col gap-1">
      <div className="flex items-center gap-1 text-muted-foreground text-xs">
        {icon}
        <span>{label}</span>
      </div>
      <div className="text-lg font-semibold">{value}</div>
    </div>
  );
}

function getTypeColor(type: string): string {
  const colors: Record<string, string> = {
    solution: 'bg-blue-500/10 text-blue-500',
    best_practice: 'bg-green-500/10 text-green-500',
    lesson_learned: 'bg-yellow-500/10 text-yellow-500',
    pattern: 'bg-purple-500/10 text-purple-500',
    standard: 'bg-orange-500/10 text-orange-500',
    preference: 'bg-pink-500/10 text-pink-500',
  };
  return colors[type] || 'bg-gray-500/10 text-gray-500';
}

function getValidationColor(status: string): string {
  const colors: Record<string, string> = {
    organizational_standard: 'bg-emerald-500/10 text-emerald-500',
    human_validated: 'bg-blue-500/10 text-blue-500',
    agent_validated: 'bg-cyan-500/10 text-cyan-500',
    unvalidated: 'bg-gray-500/10 text-gray-500',
  };
  return colors[status] || 'bg-gray-500/10 text-gray-500';
}

export default KnowledgeDetail;
