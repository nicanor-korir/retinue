"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { AlertCircle, Clock, Send, X } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";

interface ReviewEscalationPanelProps {
  taskId: string;
  reviewStartedAt: string;
  assignedToAgent: string;
  onResolve: (taskId: string, notes: string, direction: string, resolvedByAgentId: string) => Promise<void>;
  isLoading?: boolean;
}

export function ReviewEscalationPanel({
  taskId,
  reviewStartedAt,
  assignedToAgent,
  onResolve,
  isLoading = false,
}: ReviewEscalationPanelProps) {
  const [showResolveDialog, setShowResolveDialog] = useState(false);
  const [resolutionNotes, setResolutionNotes] = useState("");
  const [clearDirection, setClearDirection] = useState("");
  const [resolvedByAgentId, setResolvedByAgentId] = useState("ceo_001");
  const [isSubmitting, setIsSubmitting] = useState(false);

  const reviewDuration = new Date(reviewStartedAt);
  const now = new Date();
  const minutesInReview = Math.round((now.getTime() - reviewDuration.getTime()) / 60000);
  const isTimeoutExceeded = minutesInReview > 5;

  const handleResolveSubmit = async () => {
    if (!resolutionNotes.trim() || !clearDirection.trim()) {
      return;
    }

    setIsSubmitting(true);
    try {
      await onResolve(taskId, resolutionNotes, clearDirection, resolvedByAgentId);
      setShowResolveDialog(false);
      setResolutionNotes("");
      setClearDirection("");
    } finally {
      setIsSubmitting(false);
    }
  };

  if (!isTimeoutExceeded) {
    return null;
  }

  return (
    <>
      <Card className="border-yellow-500 bg-yellow-50 dark:bg-yellow-950">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex items-start gap-3">
              <AlertCircle className="h-5 w-5 text-yellow-600 dark:text-yellow-400 mt-0.5" />
              <div>
                <CardTitle className="text-yellow-900 dark:text-yellow-100">
                  Review Timeout Escalation
                </CardTitle>
                <CardDescription className="text-yellow-800 dark:text-yellow-200">
                  This task has been in review status for more than 5 minutes
                </CardDescription>
              </div>
            </div>
            <Badge variant="destructive" className="ml-2">
              ESCALATED
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <Label className="text-sm font-medium text-yellow-900 dark:text-yellow-100">
                Time in Review
              </Label>
              <div className="flex items-center gap-2 mt-1">
                <Clock className="h-4 w-4 text-yellow-600 dark:text-yellow-400" />
                <span className="text-sm font-semibold text-yellow-900 dark:text-yellow-100">
                  {minutesInReview} minutes
                </span>
              </div>
            </div>

            <div>
              <Label className="text-sm font-medium text-yellow-900 dark:text-yellow-100">
                Started Review
              </Label>
              <p className="text-sm text-yellow-800 dark:text-yellow-200 mt-1">
                {formatRelativeTime(reviewStartedAt)}
              </p>
            </div>
          </div>

          <div>
            <Label className="text-sm font-medium text-yellow-900 dark:text-yellow-100">
              Assigned To
            </Label>
            <p className="text-sm text-yellow-800 dark:text-yellow-200 mt-1">
              {assignedToAgent}
            </p>
          </div>

          <div className="bg-yellow-100 dark:bg-yellow-900 p-3 rounded-md">
            <p className="text-sm text-yellow-900 dark:text-yellow-100">
              This task requires immediate manager attention to provide clear direction on what needs to be done next.
              Use the button below to provide feedback and next steps.
            </p>
          </div>

          <Button
            onClick={() => setShowResolveDialog(true)}
            className="w-full bg-yellow-600 hover:bg-yellow-700 text-white"
            disabled={isLoading}
          >
            <Send className="mr-2 h-4 w-4" />
            Provide Clear Direction
          </Button>
        </CardContent>
      </Card>

      <Dialog open={showResolveDialog} onOpenChange={setShowResolveDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Resolve Review Escalation</DialogTitle>
            <DialogDescription>
              Provide feedback on what was reviewed and clear direction on what the assigned agent needs to do next.
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <Label htmlFor="manager-id" className="text-sm font-medium">
                Manager/Approver ID
              </Label>
              <div className="text-sm text-muted-foreground mt-1 p-2 bg-secondary rounded">
                <select
                  value={resolvedByAgentId}
                  onChange={(e) => setResolvedByAgentId(e.target.value)}
                  className="w-full bg-transparent"
                >
                  <option value="ceo_001">CEO (ceo_001)</option>
                  <option value="cto_001">CTO (cto_001)</option>
                  <option value="pm_001">Project Manager (pm_001)</option>
                  <option value="hr_001">HR (hr_001)</option>
                </select>
              </div>
            </div>

            <div>
              <Label htmlFor="resolution-notes" className="text-sm font-medium">
                Review Feedback *
              </Label>
              <p className="text-xs text-muted-foreground mb-2">
                What feedback do you have about the work that was reviewed?
              </p>
              <Textarea
                id="resolution-notes"
                placeholder="e.g., The implementation looks good overall. The error handling could be more comprehensive. Please add try-catch blocks for database operations."
                value={resolutionNotes}
                onChange={(e) => setResolutionNotes(e.target.value)}
                className="min-h-[100px]"
              />
            </div>

            <div>
              <Label htmlFor="clear-direction" className="text-sm font-medium">
                Clear Direction on What Needs to Be Done *
              </Label>
              <p className="text-xs text-muted-foreground mb-2">
                Provide specific, actionable next steps for the agent to complete the task.
              </p>
              <Textarea
                id="clear-direction"
                placeholder="e.g., Please make the following changes: 1. Add try-catch blocks to all database queries in the user service, 2. Add unit tests for the error handling logic, 3. Update the API documentation with the new error response format."
                value={clearDirection}
                onChange={(e) => setClearDirection(e.target.value)}
                className="min-h-[120px]"
              />
            </div>

            <div className="bg-blue-50 dark:bg-blue-950 p-3 rounded-md">
              <p className="text-sm text-blue-900 dark:text-blue-100">
                <strong>Note:</strong> After you provide this feedback, the task will be returned to IN_PROGRESS status
                and the agent will receive a message with your feedback and clear direction.
              </p>
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => {
                setShowResolveDialog(false);
                setResolutionNotes("");
                setClearDirection("");
              }}
              disabled={isSubmitting}
            >
              Cancel
            </Button>
            <Button
              onClick={handleResolveSubmit}
              disabled={
                isSubmitting ||
                !resolutionNotes.trim() ||
                !clearDirection.trim()
              }
              className="bg-blue-600 hover:bg-blue-700"
            >
              {isSubmitting ? "Submitting..." : "Submit & Return to In Progress"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
