/**
 * Extraction Candidate Review Component
 *
 * Review and approve/reject automatically extracted knowledge candidates.
 */

'use client';

import React, { useState } from 'react';
import { Check, X, Edit, Sparkles, TrendingUp, Zap } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { useExtractionCandidates, useReviewExtraction, ExtractionCandidate } from '@/hooks/useKnowledge';
import { Progress } from '@/components/ui/progress';

interface ExtractionReviewProps {
  reviewerId: string;
  limit?: number;
  minQuality?: number;
}

export function ExtractionReview({ reviewerId, limit = 20, minQuality = 0.5 }: ExtractionReviewProps) {
  const { data: candidates, isLoading } = useExtractionCandidates({ limit, minQuality });
  const reviewMutation = useReviewExtraction();

  const [selectedCandidate, setSelectedCandidate] = useState<ExtractionCandidate | null>(null);
  const [reviewNotes, setReviewNotes] = useState('');

  const handleReview = async (
    candidate: ExtractionCandidate,
    decision: 'approve' | 'reject'
  ) => {
    await reviewMutation.mutateAsync({
      candidateId: candidate.candidate_id,
      reviewerId,
      decision,
      reviewNotes: reviewNotes || undefined,
    });

    setSelectedCandidate(null);
    setReviewNotes('');
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
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
      </div>
    );
  }

  if (!candidates || candidates.length === 0) {
    return (
      <Card>
        <CardContent className="py-12 text-center">
          <Sparkles className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
          <p className="text-muted-foreground">
            No extraction candidates pending review
          </p>
          <p className="text-sm text-muted-foreground mt-2">
            Knowledge is automatically extracted from conversations and tasks
          </p>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold">Pending Extraction Candidates</h3>
          <p className="text-sm text-muted-foreground">
            {candidates.length} candidates awaiting review
          </p>
        </div>
        <Button
          variant="outline"
          onClick={() => {
            // Batch approve all high-quality candidates
            candidates
              .filter((c) => c.extraction_quality >= 0.8)
              .forEach((c) => handleReview(c, 'approve'));
          }}
          disabled={reviewMutation.isPending}
        >
          <Zap className="h-4 w-4 mr-2" />
          Auto-Approve High Quality
        </Button>
      </div>

      {/* Candidates List */}
      <ScrollArea className="h-[600px]">
        <div className="space-y-3">
          {candidates.map((candidate) => (
            <ExtractionCandidateCard
              key={candidate.candidate_id}
              candidate={candidate}
              onApprove={() => handleReview(candidate, 'approve')}
              onReject={() => handleReview(candidate, 'reject')}
              onView={() => setSelectedCandidate(candidate)}
              isReviewing={reviewMutation.isPending}
            />
          ))}
        </div>
      </ScrollArea>

      {/* Detail Dialog */}
      <Dialog
        open={!!selectedCandidate}
        onOpenChange={(open) => !open && setSelectedCandidate(null)}
      >
        <DialogContent className="max-w-3xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>{selectedCandidate?.title}</DialogTitle>
            <DialogDescription>
              Review and approve this extracted knowledge
            </DialogDescription>
          </DialogHeader>

          {selectedCandidate && (
            <div className="space-y-4">
              {/* Scores */}
              <div className="grid grid-cols-4 gap-4">
                <ScoreCard label="Quality" value={selectedCandidate.extraction_quality} />
                <ScoreCard label="Confidence" value={selectedCandidate.confidence_score} />
                <ScoreCard label="Novelty" value={selectedCandidate.novelty_score} />
                <ScoreCard label="Relevance" value={selectedCandidate.relevance_score} />
              </div>

              {/* Content */}
              <div>
                <h4 className="text-sm font-medium mb-2">Summary</h4>
                <p className="text-sm text-muted-foreground">{selectedCandidate.summary}</p>
              </div>

              {/* Metadata */}
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">{selectedCandidate.extraction_type}</Badge>
                <Badge variant="outline">{selectedCandidate.trigger_type}</Badge>
              </div>

              {/* Review Notes */}
              <div>
                <h4 className="text-sm font-medium mb-2">Review Notes (Optional)</h4>
                <Textarea
                  placeholder="Add notes about this knowledge..."
                  value={reviewNotes}
                  onChange={(e) => setReviewNotes(e.target.value)}
                  rows={3}
                />
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => handleReview(selectedCandidate, 'reject')}
                  disabled={reviewMutation.isPending}
                >
                  <X className="h-4 w-4 mr-2" />
                  Reject
                </Button>
                <Button
                  onClick={() => handleReview(selectedCandidate, 'approve')}
                  disabled={reviewMutation.isPending}
                >
                  <Check className="h-4 w-4 mr-2" />
                  Approve
                </Button>
              </div>
            </div>
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
}

interface ExtractionCandidateCardProps {
  candidate: ExtractionCandidate;
  onApprove: () => void;
  onReject: () => void;
  onView: () => void;
  isReviewing: boolean;
}

function ExtractionCandidateCard({
  candidate,
  onApprove,
  onReject,
  onView,
  isReviewing,
}: ExtractionCandidateCardProps) {
  const getQualityColor = (score: number) => {
    if (score >= 0.8) return 'text-green-500';
    if (score >= 0.6) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <Card className="cursor-pointer hover:shadow-md transition-all" onClick={onView}>
      <CardHeader>
        <div className="flex items-start justify-between gap-4">
          <div className="flex-1 space-y-1">
            <CardTitle className="text-base">{candidate.title}</CardTitle>
            <CardDescription className="line-clamp-2">
              {candidate.summary}
            </CardDescription>
          </div>
          <Badge
            variant="outline"
            className={getQualityColor(candidate.extraction_quality)}
          >
            {(candidate.extraction_quality * 100).toFixed(0)}% quality
          </Badge>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {/* Progress Bars */}
          <div className="space-y-2">
            <div className="flex items-center justify-between text-xs">
              <span className="text-muted-foreground">Confidence</span>
              <span className={getQualityColor(candidate.confidence_score)}>
                {(candidate.confidence_score * 100).toFixed(0)}%
              </span>
            </div>
            <Progress value={candidate.confidence_score * 100} className="h-1" />
          </div>

          <div className="flex items-center gap-2 flex-wrap">
            <Badge variant="secondary" className="text-xs">
              {candidate.extraction_type}
            </Badge>
            <Badge variant="secondary" className="text-xs">
              {candidate.trigger_type}
            </Badge>
            <span className="text-xs text-muted-foreground">
              {new Date(candidate.created_at).toLocaleDateString()}
            </span>
          </div>

          {/* Actions */}
          <div className="flex gap-2 pt-2" onClick={(e) => e.stopPropagation()}>
            <Button
              variant="outline"
              size="sm"
              onClick={onReject}
              disabled={isReviewing}
              className="flex-1"
            >
              <X className="h-4 w-4 mr-2" />
              Reject
            </Button>
            <Button
              size="sm"
              onClick={onApprove}
              disabled={isReviewing}
              className="flex-1"
            >
              <Check className="h-4 w-4 mr-2" />
              Approve
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface ScoreCardProps {
  label: string;
  value: number;
}

function ScoreCard({ label, value }: ScoreCardProps) {
  const getColor = (score: number) => {
    if (score >= 0.8) return 'text-green-500';
    if (score >= 0.6) return 'text-yellow-500';
    return 'text-red-500';
  };

  return (
    <div className="text-center">
      <div className={`text-2xl font-bold ${getColor(value)}`}>
        {(value * 100).toFixed(0)}%
      </div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}

export default ExtractionReview;
