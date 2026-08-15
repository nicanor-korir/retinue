'use client';

import { useState } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Checkbox } from '@/components/ui/checkbox';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Slider } from '@/components/ui/slider';
import { MessageSquare, Star, AlertCircle, Loader2 } from 'lucide-react';
import axios from 'axios';
import { feedbackAPI } from '@/lib/api';
import type { ProjectFeedbackRequest, TaskFeedbackRequest, AgentFeedbackRequest } from '@/types/api';
import { FeedbackType, Priority } from '@/types/api';

interface FeedbackDialogProps {
  entityType: 'project' | 'task' | 'agent';
  entityId: string;
  entityName: string;
  projectId?: string; // Required for tasks, optional for projects/agents
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onFeedbackSubmitted?: (feedbackId: string) => void;
}

const FEEDBACK_TYPES: Array<{ id: FeedbackType; label: string; description: string; icon: string }> = [
  { id: FeedbackType.GENERAL, label: 'General Feedback', description: 'General comments or observations', icon: '💬' },
  { id: FeedbackType.QUALITY, label: 'Quality Assessment', description: 'Feedback on overall quality', icon: '⭐' },
  { id: FeedbackType.CORRECTNESS, label: 'Correctness', description: 'Is the output correct?', icon: '✓' },
  { id: FeedbackType.COMPLETENESS, label: 'Completeness', description: 'Is everything done?', icon: '📋' },
  { id: FeedbackType.DIRECTION, label: 'Strategic Direction', description: 'Guidance on direction/approach', icon: '🎯' },
  { id: FeedbackType.IMPLEMENTATION, label: 'Implementation Feedback', description: 'Technical implementation details', icon: '⚙️' },
  { id: FeedbackType.BLOCKING_ISSUE, label: 'Blocking Issue', description: 'Something blocking progress', icon: '🚫' },
  { id: FeedbackType.ENHANCEMENT, label: 'Enhancement Suggestion', description: 'Ideas for improvement', icon: '✨' },
  { id: FeedbackType.BUG_REPORT, label: 'Bug Report', description: 'Found a bug or error', icon: '🐛' },
  { id: FeedbackType.PERFORMANCE, label: 'Performance', description: 'Performance-related feedback', icon: '⚡' },
];

export function FeedbackDialog({
  entityType,
  entityId,
  entityName,
  projectId,
  isOpen,
  onOpenChange,
  onFeedbackSubmitted,
}: FeedbackDialogProps) {
  // Basic feedback
  const [feedbackType, setFeedbackType] = useState<FeedbackType>(FeedbackType.GENERAL);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [priority, setPriority] = useState('medium');

  // Ratings (0-5, used differently based on entity type)
  const [ratings, setRatings] = useState<Record<string, number>>({});

  // Additional context
  const [contextTags, setContextTags] = useState<string[]>([]);
  const [additionalDetails, setAdditionalDetails] = useState('');

  // Specific fields based on entity type
  const [suggestedActions, setSuggestedActions] = useState<string[]>(['']);
  const [codeReviewFeedback, setCodeReviewFeedback] = useState('');

  // Submission state
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const selectedType = FEEDBACK_TYPES.find((t) => t.id === feedbackType);

  const handleAddSuggestedAction = () => {
    setSuggestedActions([...suggestedActions, '']);
  };

  const handleUpdateSuggestedAction = (index: number, value: string) => {
    const updated = [...suggestedActions];
    updated[index] = value;
    setSuggestedActions(updated);
  };

  const handleRemoveSuggestedAction = (index: number) => {
    setSuggestedActions(suggestedActions.filter((_, i) => i !== index));
  };

  const handleRatingChange = (ratingType: string, value: number) => {
    setRatings((prev) => ({ ...prev, [ratingType]: value }));
  };

  const toggleContextTag = (tag: string) => {
    setContextTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const handleSubmit = async () => {
    if (!title.trim() || !description.trim()) {
      setError('Please fill in title and description');
      return;
    }

    setIsSubmitting(true);
    setError(null);

    try {
      // Common payload properties
      const basePayload = {
        feedback_type: feedbackType,
        title,
        description,
        priority: priority as Priority,
        context: {
          tags: contextTags,
          additional_details: additionalDetails,
        },
      };

      let feedbackId: string | undefined;

      if (entityType === 'project') {
        const payload: ProjectFeedbackRequest = {
          ...basePayload,
          quality_rating: ratings['quality'] || null,
          satisfaction_rating: ratings['satisfaction'] || null,
          confidence_level: ratings['confidence'] || null,
          suggested_actions: suggestedActions.filter((a) => a.trim()),
        };
        const response = await feedbackAPI.submitProjectFeedback(entityId, payload);
        feedbackId = response.data.feedback_id;
      } else if (entityType === 'task') {
        const payload: TaskFeedbackRequest = {
          ...basePayload,
          output_quality: ratings['output_quality'] || null,
          correctness: ratings['correctness'] || null,
          completeness: ratings['completeness'] || null,
          implementation_quality: ratings['implementation'] || null,
          code_review_feedback: codeReviewFeedback || null,
          suggested_improvements: suggestedActions.filter((a) => a.trim()),
          action_items: suggestedActions.filter((a) => a.trim()),
        };
        const response = await feedbackAPI.submitTaskFeedback(entityId, payload);
        feedbackId = response.data.feedback_id;
      } else if (entityType === 'agent') {
        const payload: AgentFeedbackRequest = {
          ...basePayload,
          decision_quality: ratings['decision'] || null,
          execution_quality: ratings['execution'] || null,
          communication_clarity: ratings['communication'] || null,
          problem_solving: ratings['problem_solving'] || null,
          efficiency: ratings['efficiency'] || null,
          recommended_improvements: suggestedActions.filter((a) => a.trim()),
        };
        const response = await feedbackAPI.submitAgentFeedback(entityId, payload);
        feedbackId = response.data.feedback_id;
      }

      setSuccess(true);
      if (feedbackId) {
        onFeedbackSubmitted?.(feedbackId);
      }

      // Reset form
      setTimeout(() => {
        setTitle('');
        setDescription('');
        setFeedbackType(FeedbackType.GENERAL);
        setPriority('medium');
        setRatings({});
        setContextTags([]);
        setAdditionalDetails('');
        setSuggestedActions(['']);
        setCodeReviewFeedback('');
        setSuccess(false);
        onOpenChange(false);
      }, 1500);
    } catch (err) {
      const message = axios.isAxiosError(err) ? err.response?.data?.detail || err.message : 'Failed to submit feedback';
      setError(message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5" />
            Provide Feedback: {entityName}
          </DialogTitle>
          <DialogDescription>
            Share your thoughts, suggestions, and context to help improve the {entityType}
          </DialogDescription>
        </DialogHeader>

        {success && (
          <div className="p-4 bg-green-50 dark:bg-green-950/30 border-2 border-green-500 rounded-lg text-sm text-green-700 dark:text-green-300 font-medium">
            ✅ Feedback submitted successfully! The system will process it and take appropriate action.
          </div>
        )}

        {error && (
          <div className="p-4 bg-red-50 dark:bg-red-950/30 border-2 border-red-500 rounded-lg text-sm text-red-700 dark:text-red-300 flex gap-2 font-medium">
            <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
            <div>{error}</div>
          </div>
        )}

        <div className="space-y-6">
          {/* Feedback Type Selection */}
          <div className="space-y-3">
            <Label className="text-base font-semibold">What type of feedback is this?</Label>
            <div className="grid grid-cols-2 gap-2 max-h-64 overflow-y-auto">
              {FEEDBACK_TYPES.map((type) => (
                <div
                  key={type.id}
                  onClick={() => setFeedbackType(type.id)}
                  className={`p-3 border-2 rounded-lg cursor-pointer transition-all ${
                    feedbackType === type.id
                      ? 'border-blue-600 bg-blue-600 shadow-md'
                      : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                  }`}
                >
                  <div className="flex items-start gap-2">
                    <span className="text-xl">{type.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className={`font-medium text-sm ${
                        feedbackType === type.id ? 'text-white' : 'text-gray-900'
                      }`}>
                        {type.label}
                      </div>
                      <div className={`text-xs ${
                        feedbackType === type.id ? 'text-blue-100' : 'text-gray-600'
                      }`}>
                        {type.description}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Title and Description */}
          <div className="space-y-3">
            <div>
              <Label htmlFor="feedback-title" className="text-sm font-semibold">
                Feedback Title *
              </Label>
              <Input
                id="feedback-title"
                placeholder="Brief summary of your feedback"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                className="mt-2"
              />
            </div>

            <div>
              <Label htmlFor="feedback-description" className="text-sm font-semibold">
                Detailed Description *
              </Label>
              <Textarea
                id="feedback-description"
                placeholder="Provide detailed context, observations, and suggestions..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="mt-2 h-32"
              />
            </div>
          </div>

          {/* Ratings Section */}
          {entityType === 'project' && (
            <div className="space-y-4 p-4 bg-blue-50 dark:bg-blue-950/30 rounded-lg border border-blue-200 dark:border-blue-800">
              <h4 className="font-semibold text-sm text-blue-900 dark:text-blue-100">Rate the Project (Optional)</h4>

              <div className="space-y-3">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-sm">Overall Quality</Label>
                    <span className="text-sm font-medium">{ratings['quality'] || 0}/5</span>
                  </div>
                  <Slider
                    min={0}
                    max={5}
                    step={1}
                    value={[ratings['quality'] || 0]}
                    onValueChange={(val) => handleRatingChange('quality', val[0])}
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-sm">Satisfaction Level</Label>
                    <span className="text-sm font-medium">{ratings['satisfaction'] || 0}/5</span>
                  </div>
                  <Slider
                    min={0}
                    max={5}
                    step={1}
                    value={[ratings['satisfaction'] || 0]}
                    onValueChange={(val) => handleRatingChange('satisfaction', val[0])}
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-sm">Confidence in Feedback</Label>
                    <span className="text-sm font-medium">{ratings['confidence'] || 0}/5</span>
                  </div>
                  <Slider
                    min={0}
                    max={5}
                    step={1}
                    value={[ratings['confidence'] || 0]}
                    onValueChange={(val) => handleRatingChange('confidence', val[0])}
                  />
                </div>
              </div>
            </div>
          )}

          {entityType === 'task' && (
            <div className="space-y-4 p-4 bg-purple-50 dark:bg-purple-950/30 rounded-lg border border-purple-200 dark:border-purple-800">
              <h4 className="font-semibold text-sm text-purple-900 dark:text-purple-100">Task Quality Assessment (Optional)</h4>

              <div className="space-y-3">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-sm">Output Quality</Label>
                    <span className="text-sm font-medium">{ratings['output_quality'] || 0}/5</span>
                  </div>
                  <Slider
                    min={0}
                    max={5}
                    step={1}
                    value={[ratings['output_quality'] || 0]}
                    onValueChange={(val) => handleRatingChange('output_quality', val[0])}
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-sm">Correctness</Label>
                    <span className="text-sm font-medium">{ratings['correctness'] || 0}/5</span>
                  </div>
                  <Slider
                    min={0}
                    max={5}
                    step={1}
                    value={[ratings['correctness'] || 0]}
                    onValueChange={(val) => handleRatingChange('correctness', val[0])}
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-sm">Completeness</Label>
                    <span className="text-sm font-medium">{ratings['completeness'] || 0}/5</span>
                  </div>
                  <Slider
                    min={0}
                    max={5}
                    step={1}
                    value={[ratings['completeness'] || 0]}
                    onValueChange={(val) => handleRatingChange('completeness', val[0])}
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-sm">Implementation Quality</Label>
                    <span className="text-sm font-medium">{ratings['implementation'] || 0}/5</span>
                  </div>
                  <Slider
                    min={0}
                    max={5}
                    step={1}
                    value={[ratings['implementation'] || 0]}
                    onValueChange={(val) => handleRatingChange('implementation', val[0])}
                  />
                </div>
              </div>

              {feedbackType === 'implementation' && (
                <div className="mt-4 pt-4 border-t">
                  <Label htmlFor="code-review" className="text-sm font-semibold">
                    Code Review Feedback
                  </Label>
                  <Textarea
                    id="code-review"
                    placeholder="Specific comments on code implementation..."
                    value={codeReviewFeedback}
                    onChange={(e) => setCodeReviewFeedback(e.target.value)}
                    className="mt-2 h-24"
                  />
                </div>
              )}
            </div>
          )}

          {entityType === 'agent' && (
            <div className="space-y-4 p-4 bg-orange-50 dark:bg-orange-950/30 rounded-lg border border-orange-200 dark:border-orange-800">
              <h4 className="font-semibold text-sm text-orange-900 dark:text-orange-100">Agent Performance Assessment (Optional)</h4>

              <div className="space-y-3">
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-sm">Decision Quality</Label>
                    <span className="text-sm font-medium">{ratings['decision'] || 0}/5</span>
                  </div>
                  <Slider
                    min={0}
                    max={5}
                    step={1}
                    value={[ratings['decision'] || 0]}
                    onValueChange={(val) => handleRatingChange('decision', val[0])}
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-sm">Execution Quality</Label>
                    <span className="text-sm font-medium">{ratings['execution'] || 0}/5</span>
                  </div>
                  <Slider
                    min={0}
                    max={5}
                    step={1}
                    value={[ratings['execution'] || 0]}
                    onValueChange={(val) => handleRatingChange('execution', val[0])}
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-sm">Communication Clarity</Label>
                    <span className="text-sm font-medium">{ratings['communication'] || 0}/5</span>
                  </div>
                  <Slider
                    min={0}
                    max={5}
                    step={1}
                    value={[ratings['communication'] || 0]}
                    onValueChange={(val) => handleRatingChange('communication', val[0])}
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-sm">Problem Solving</Label>
                    <span className="text-sm font-medium">{ratings['problem_solving'] || 0}/5</span>
                  </div>
                  <Slider
                    min={0}
                    max={5}
                    step={1}
                    value={[ratings['problem_solving'] || 0]}
                    onValueChange={(val) => handleRatingChange('problem_solving', val[0])}
                  />
                </div>

                <div>
                  <div className="flex items-center justify-between mb-2">
                    <Label className="text-sm">Efficiency</Label>
                    <span className="text-sm font-medium">{ratings['efficiency'] || 0}/5</span>
                  </div>
                  <Slider
                    min={0}
                    max={5}
                    step={1}
                    value={[ratings['efficiency'] || 0]}
                    onValueChange={(val) => handleRatingChange('efficiency', val[0])}
                  />
                </div>
              </div>
            </div>
          )}

          {/* Priority */}
          <div className="space-y-2">
            <Label htmlFor="priority" className="text-sm font-semibold">
              Priority Level
            </Label>
            <Select value={priority} onValueChange={setPriority}>
              <SelectTrigger id="priority">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="low">Low</SelectItem>
                <SelectItem value="medium">Medium</SelectItem>
                <SelectItem value="high">High</SelectItem>
                <SelectItem value="critical">Critical</SelectItem>
              </SelectContent>
            </Select>
          </div>

          {/* Context Tags */}
          <div className="space-y-3">
            <Label className="text-sm font-semibold">Context Tags (Optional)</Label>
            <div className="flex flex-wrap gap-2">
              {['requirements', 'architecture', 'performance', 'security', 'testing', 'documentation', 'design'].map(
                (tag) => (
                  <Badge
                    key={tag}
                    variant={contextTags.includes(tag) ? 'default' : 'outline'}
                    className={`cursor-pointer transition-all ${
                      contextTags.includes(tag)
                        ? 'bg-primary text-primary-foreground hover:bg-primary/90'
                        : 'hover:bg-secondary'
                    }`}
                    onClick={() => toggleContextTag(tag)}
                  >
                    {contextTags.includes(tag) && '✓ '}
                    {tag}
                  </Badge>
                )
              )}
            </div>
          </div>

          {/* Suggested Actions/Items */}
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <Label className="text-sm font-semibold">Suggested Actions (Optional)</Label>
              <Button
                size="sm"
                variant="outline"
                onClick={handleAddSuggestedAction}
              >
                + Add Item
              </Button>
            </div>
            <div className="space-y-2">
              {suggestedActions.map((action, index) => (
                <div key={index} className="flex gap-2">
                  <Input
                    placeholder="Enter suggested action or improvement..."
                    value={action}
                    onChange={(e) => handleUpdateSuggestedAction(index, e.target.value)}
                  />
                  {suggestedActions.length > 1 && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => handleRemoveSuggestedAction(index)}
                    >
                      Remove
                    </Button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Additional Details */}
          <div className="space-y-2">
            <Label htmlFor="additional-details" className="text-sm font-semibold">
              Additional Context or Details
            </Label>
            <Textarea
              id="additional-details"
              placeholder="Any other information that would be helpful..."
              value={additionalDetails}
              onChange={(e) => setAdditionalDetails(e.target.value)}
              className="h-20"
            />
          </div>
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-3 pt-6 border-t">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isSubmitting || !title.trim() || !description.trim()}
            className="gap-2"
          >
            {isSubmitting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Submitting...
              </>
            ) : (
              <>
                <MessageSquare className="h-4 w-4" />
                Submit Feedback
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
