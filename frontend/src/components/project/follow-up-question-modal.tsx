"use client";

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { MessageSquarePlus, Sparkles, Info } from "lucide-react";
import { useAddFollowUpQuestion } from "@/hooks/useApi";
import { Priority } from "@/types/api";

interface FollowUpQuestionModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectName: string;
  projectId: string;
  originalQuestion?: string;
}

export function FollowUpQuestionModal({
  open,
  onOpenChange,
  projectName,
  projectId,
  originalQuestion,
}: FollowUpQuestionModalProps) {
  const addFollowUp = useAddFollowUpQuestion();
  const [followUpText, setFollowUpText] = useState("");
  const [priority, setPriority] = useState<Priority>(Priority.MEDIUM);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const characterCount = followUpText.length;
  const minCharacters = 10;
  const maxCharacters = 5000;
  const isValid = characterCount >= minCharacters && characterCount <= maxCharacters;

  const handleSubmit = async () => {
    if (!isValid) return;

    setIsSubmitting(true);
    setError(null);

    try {
      // Add follow-up question to existing project
      await addFollowUp.mutateAsync({
        id: projectId,
        question: followUpText,
        priority: priority.toLowerCase(),
      });

      // Close modal and reset form
      onOpenChange(false);
      setFollowUpText("");
      setPriority(Priority.MEDIUM);
    } catch (err: any) {
      console.error("Failed to submit follow-up question:", err);
      setError(err.message || "Failed to submit follow-up question. Please try again.");
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      onOpenChange(false);
      setFollowUpText("");
      setPriority(Priority.MEDIUM);
      setError(null);
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <div className="flex items-center gap-2">
            <MessageSquarePlus className="h-6 w-6 text-primary" />
            <DialogTitle className="text-2xl">Ask Follow-up Question</DialogTitle>
          </div>
          <DialogDescription className="text-base pt-2">
            Continue the conversation based on the previous answer. The CEO agent will
            review your question and provide a detailed response or involve the team
            if development work is needed.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Context Info */}
          <div className="p-4 rounded-lg bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900">
            <div className="flex items-start gap-3">
              <Info className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm">
                <p className="font-medium text-blue-900 dark:text-blue-100 mb-1">
                  About Follow-up Questions
                </p>
                <ul className="text-blue-700 dark:text-blue-300 space-y-1 list-disc list-inside">
                  <li>Your question will be sent directly to the CEO agent</li>
                  <li>Context from the original conversation will be included automatically</li>
                  <li>Simple queries get instant answers; development work involves the full team</li>
                  <li>You'll be notified when the CEO responds (~15 minutes)</li>
                </ul>
              </div>
            </div>
          </div>

          {/* Follow-up Question Input */}
          <div className="space-y-2">
            <Label htmlFor="follow-up-text" className="text-base font-semibold">
              Your Follow-up Question *
            </Label>
            <Textarea
              id="follow-up-text"
              placeholder="Ask for clarification, request more details, or expand on the previous answer...&#10;&#10;Examples:&#10;• Can you explain [specific concept] in more detail?&#10;• How would I implement this in [technology]?&#10;• What are the pros and cons of this approach?&#10;• Could you provide code examples for [feature]?"
              value={followUpText}
              onChange={(e) => setFollowUpText(e.target.value)}
              className="min-h-[200px] resize-none text-base"
              disabled={isSubmitting}
            />
            <div className="flex items-center justify-between text-sm">
              <span className={characterCount < minCharacters ? "text-destructive" : "text-muted-foreground"}>
                {characterCount < minCharacters ? (
                  `${minCharacters - characterCount} more characters needed`
                ) : (
                  `${characterCount} / ${maxCharacters} characters`
                )}
              </span>
              {characterCount >= minCharacters && (
                <span className="text-green-600 font-medium flex items-center gap-1">
                  <Sparkles className="h-3 w-3" />
                  Ready to submit
                </span>
              )}
            </div>
          </div>

          {/* Priority Selection */}
          <div className="space-y-2">
            <Label htmlFor="priority" className="text-base font-semibold">
              Priority Level
            </Label>
            <select
              id="priority"
              value={priority}
              onChange={(e) => setPriority(e.target.value as Priority)}
              disabled={isSubmitting}
              className="flex h-10 w-full items-center justify-between rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <option value={Priority.LOW}>Low - No rush</option>
              <option value={Priority.MEDIUM}>Medium - Standard priority</option>
              <option value={Priority.HIGH}>High - Important question</option>
              <option value={Priority.CRITICAL}>Critical - Urgent response needed</option>
            </select>
            <p className="text-xs text-muted-foreground">
              Higher priority questions may receive faster responses from the CEO agent
            </p>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/20">
              <p className="text-sm text-destructive font-medium">{error}</p>
            </div>
          )}
        </div>

        <DialogFooter className="gap-2 sm:gap-0">
          <Button
            variant="outline"
            onClick={handleClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={!isValid || isSubmitting}
            className="gap-2"
          >
            {isSubmitting ? (
              <>
                <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <MessageSquarePlus className="h-4 w-4" />
                Submit Question
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
