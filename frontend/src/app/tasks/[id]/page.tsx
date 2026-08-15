"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useTask, useProject, useTaskActivity, useCancelTask, useResolveReviewEscalation, useApproveTask } from "@/hooks/useApi";
import { ArrowLeft, Calendar, User, Clock, AlertCircle, FileText, Code, Folder, RefreshCw, Ban, MessageSquare, Check, Circle } from "lucide-react";
import { FeedbackDialog } from '@/components/feedback/feedback-dialog';
import { FeedbackDisplay } from '@/components/feedback/feedback-display';
import { ContextDisplay } from '@/components/feedback/context-display';
import { useTaskFeedback } from '@/hooks/useFeedback';
import { ReviewEscalationPanel } from '@/components/tasks/review-escalation-panel';
import { TaskChatPanel } from '@/components/task/task-chat-panel';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from "@/components/ui/accordion";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ActivityFeed } from "@/components/activity/activity-feed";
import { formatDate, formatRelativeTime } from "@/lib/utils";
import { getTaskStatusColor, getTaskStatusIcon } from "@/lib/status-utils";
import { LoadingState } from "@/components/common/LoadingState";
import { EmptyState } from "@/components/common/EmptyState";
import { ConfirmDialog } from "@/components/common/ConfirmDialog";
import { useRefresh } from "@/hooks/useRefresh";
import Link from "next/link";
import { TaskStatus } from "@/types/api";

export default function TaskDetailPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const { data: task, isLoading: taskLoading, refetch: refetchTask } = useTask(id);
  const { data: project, refetch: refetchProject } = useProject(task?.project_id || "");
  const { data: activities, isLoading: activitiesLoading } = useTaskActivity(id, 50);
  const cancelTask = useCancelTask();
  const resolveReview = useResolveReviewEscalation();
  const approveTask = useApproveTask();
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [cancelReason, setCancelReason] = useState("");
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const { feedback, fetchFeedback } = useTaskFeedback(id, task?.project_id);
  const [chatOpen, setChatOpen] = useState(false);

  const { isRefreshing, handleRefresh } = useRefresh([
    refetchTask,
    () => task?.project_id ? refetchProject() : Promise.resolve(),
    fetchFeedback
  ]);

  useEffect(() => {
    fetchFeedback();
  }, [id, task?.project_id, fetchFeedback]);

  const handleCancel = async () => {
    if (!cancelReason.trim()) {
      return;
    }
    setIsCancelling(true);
    try {
      await cancelTask.mutateAsync({ id, reason: cancelReason });
      setShowCancelDialog(false);
      setCancelReason("");
      // Refresh task data to show updated status
      await refetchTask();
    } catch (error) {
      console.error("Failed to cancel task:", error);
    } finally {
      setIsCancelling(false);
    }
  };

  const handleResolveReview = async (
    taskId: string,
    resolutionNotes: string,
    clearDirection: string,
    resolvedByAgentId: string
  ) => {
    try {
      await resolveReview.mutateAsync({
        id: taskId,
        resolutionNotes,
        clearDirection,
        resolvedByAgentId,
      });
      // Refresh task data to show updated status
      await refetchTask();
    } catch (error) {
      console.error("Failed to resolve review:", error);
      throw error;
    }
  };

  const handleApprove = async () => {
    setIsApproving(true);
    try {
      await approveTask.mutateAsync(id);
      setShowApproveDialog(false);
      // Refresh task data to show updated status
      await refetchTask();
    } catch (error) {
      console.error("Failed to approve task:", error);
    } finally {
      setIsApproving(false);
    }
  };

  if (taskLoading) {
    return <LoadingState />;
  }

  if (!task) {
    return (
      <DashboardLayout>
        <EmptyState
          icon={AlertCircle}
          title="Task not found"
          description="The task you're looking for doesn't exist or has been deleted."
          action={
            <Link href="/tasks">
              <Button>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Tasks
              </Button>
            </Link>
          }
        />
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <div className="flex items-center gap-4 mb-4">
            <Link href="/tasks">
              <Button variant="ghost">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Tasks
              </Button>
            </Link>
            {project && (
              <Link href={`/projects/${project.project_id}`}>
                <Button variant="ghost">
                  <Folder className="mr-2 h-4 w-4" />
                  View Project
                </Button>
              </Link>
            )}
          </div>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center space-x-3 mb-2">
                {getTaskStatusIcon(task.status)}
                <h1 className="text-3xl font-bold tracking-tight">{task.title}</h1>
              </div>
              <div className="flex items-center gap-2 mb-3">
                <Badge variant={getTaskStatusColor(task.status)}>
                  {task.status}
                </Badge>
                {task.version && task.version > 1 && (
                  <Badge variant="outline">v{task.version}</Badge>
                )}
              </div>
              {task.description && (
                <p className="text-muted-foreground max-w-3xl">
                  {task.description}
                </p>
              )}
            </div>
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={handleRefresh}
                disabled={isRefreshing}
              >
                <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                Refresh
              </Button>
              <Button
                variant="outline"
                className="gap-2"
                onClick={() => setChatOpen(prev => !prev)}
              >
                <MessageSquare className="h-4 w-4" />
                Task Chat
              </Button>
              <Button
                variant="outline"
                className="gap-2"
                onClick={() => setFeedbackOpen(true)}
              >
                <MessageSquare className="h-4 w-4" />
                Feedback
              </Button>
              {task.status === TaskStatus.REVIEW && (
                <Button
                  onClick={() => setShowApproveDialog(true)}
                  className="gap-2 bg-green-600 hover:bg-green-700"
                >
                  <Check className="h-4 w-4" />
                  Approve
                </Button>
              )}
              {(task.status === TaskStatus.IN_PROGRESS ||
                task.status === TaskStatus.PENDING ||
                task.status === TaskStatus.REVIEW ||
                task.status === TaskStatus.BLOCKED) && (
                <Button
                  variant="outline"
                  className="border-orange-500 text-orange-600 hover:bg-orange-50"
                  onClick={() => setShowCancelDialog(true)}
                >
                  <Ban className="mr-2 h-4 w-4" />
                  Cancel Task
                </Button>
              )}
            </div>
          </div>
        </div>

        {/* Task Info Cards */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Assigned To
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center">
                <User className="mr-2 h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">{task.assigned_to_agent_id}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Created
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center">
                <Calendar className="mr-2 h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">{formatDate(task.created_at)}</span>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Last Updated
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center">
                <Clock className="mr-2 h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">{formatRelativeTime(task.updated_at)}</span>
              </div>
            </CardContent>
          </Card>

          {task.estimated_hours && (
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground">
                  Estimated Hours
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex items-center">
                  <Clock className="mr-2 h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">{task.estimated_hours}h</span>
                </div>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Review Escalation Panel - Show if task is in review and timeout exceeded */}
        {task.status === TaskStatus.REVIEW && task.review_started_at && (
          <ReviewEscalationPanel
            taskId={id}
            reviewStartedAt={task.review_started_at}
            assignedToAgent={task.assigned_to_agent_id}
            onResolve={handleResolveReview}
            isLoading={resolveReview.isPending}
          />
        )}

        {/* Task Chat - Always visible */}
        <Card>
          <Accordion
            type="single"
            collapsible
            value={chatOpen ? "chat" : undefined}
            onValueChange={(value) => setChatOpen(value === "chat")}
          >
            <AccordionItem value="chat" className="border-0">
              <AccordionTrigger className="px-6 py-4 hover:no-underline hover:bg-accent/50">
                <div className="flex items-center gap-3 text-left">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <MessageSquare className="h-5 w-5" />
                      <span>Task Chat</span>
                    </CardTitle>
                    <CardDescription className="text-xs mt-1">
                      Chat with the assigned agent about this task
                    </CardDescription>
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent className="px-6 pb-4">
                <TaskChatPanel taskId={id} taskTitle={task.title} />
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </Card>

        {/* Live Activity Feed - Show only if task is in progress */}
        {(task.status === TaskStatus.IN_PROGRESS || task.status === TaskStatus.REVIEW || task.status === TaskStatus.BLOCKED) && (
          <ActivityFeed
            activities={activities || []}
            isLoading={activitiesLoading}
            title="Task Activity"
            description="Real-time updates on work being done for this task"
          />
        )}

        {/* Project Context */}
        {project && (
          <Card>
            <CardHeader>
              <CardTitle>Project Context</CardTitle>
              <CardDescription>This task is part of a larger project</CardDescription>
            </CardHeader>
            <CardContent>
              <Link
                href={`/projects/${project.project_id}`}
                className="block p-4 border rounded-lg hover:bg-accent transition-colors"
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h4 className="font-semibold">{project.name}</h4>
                      <Badge variant={getTaskStatusColor(project.status as any)}>
                        {project.status}
                      </Badge>
                    </div>
                    <p className="text-sm text-muted-foreground line-clamp-2">
                      {project.description}
                    </p>
                  </div>
                  <Folder className="h-5 w-5 text-muted-foreground ml-4" />
                </div>
              </Link>
            </CardContent>
          </Card>
        )}

        {/* Task Output / Deliverables */}
        {task.output && Object.keys(task.output).length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Task Output</CardTitle>
              <CardDescription>
                Results and deliverables from this task
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Analysis */}
              {task.output.analysis && (
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h5 className="font-medium text-sm mb-2 text-primary flex items-center">
                    <FileText className="mr-2 h-4 w-4" />
                    Analysis
                  </h5>
                  <div className="text-sm whitespace-pre-wrap">{task.output.analysis}</div>
                </div>
              )}

              {/* Decision */}
              {task.output.decision && (
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h5 className="font-medium text-sm mb-2 text-primary">Decision</h5>
                  <Badge variant={task.output.decision === 'approved' ? 'success' : 'destructive'} className="text-sm">
                    {task.output.decision.toUpperCase()}
                  </Badge>
                </div>
              )}

              {/* Generated Content/Code */}
              {task.output.content && (
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h5 className="font-medium text-sm mb-2 text-primary flex items-center">
                    <Code className="mr-2 h-4 w-4" />
                    Generated Content
                  </h5>
                  <pre className="text-sm bg-background p-3 rounded overflow-x-auto border max-h-96">
                    {typeof task.output.content === 'string'
                      ? task.output.content
                      : JSON.stringify(task.output.content, null, 2)}
                  </pre>
                </div>
              )}

              {/* Implementation */}
              {task.output.implementation && (
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h5 className="font-medium text-sm mb-2 text-primary flex items-center">
                    <Code className="mr-2 h-4 w-4" />
                    Implementation
                  </h5>
                  <pre className="text-sm bg-background p-3 rounded overflow-x-auto border max-h-96">
                    {typeof task.output.implementation === 'string'
                      ? task.output.implementation
                      : JSON.stringify(task.output.implementation, null, 2)}
                  </pre>
                </div>
              )}

              {/* Files/Artifacts */}
              {task.output.files && Array.isArray(task.output.files) && (
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h5 className="font-medium text-sm mb-2 text-primary">Files Created</h5>
                  <ul className="space-y-2">
                    {task.output.files.map((file: any, idx: number) => (
                      <li key={idx} className="flex items-center text-sm">
                        <Code className="mr-2 h-4 w-4 text-muted-foreground" />
                        <span className="font-mono">{file.path || file.name || file}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}

              {/* Language & Framework Info */}
              {(task.output.language || task.output.framework) && (
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h5 className="font-medium text-sm mb-2 text-primary">Technical Details</h5>
                  <div className="flex gap-2">
                    {task.output.language && (
                      <Badge variant="outline">{task.output.language}</Badge>
                    )}
                    {task.output.framework && (
                      <Badge variant="outline">{task.output.framework}</Badge>
                    )}
                    {task.output.task_type && (
                      <Badge variant="secondary">{task.output.task_type}</Badge>
                    )}
                  </div>
                </div>
              )}

              {/* Status Info */}
              {task.output.status && (
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h5 className="font-medium text-sm mb-2 text-primary">Status</h5>
                  <Badge variant="outline">{task.output.status}</Badge>
                </div>
              )}

              {/* Error Info */}
              {task.output.error && (
                <div className="bg-destructive/10 border border-destructive/20 p-4 rounded-lg">
                  <h5 className="font-medium text-sm mb-2 text-destructive">Error</h5>
                  <p className="text-sm text-destructive">{task.output.error}</p>
                </div>
              )}

              {/* Raw Output (fallback) */}
              {!task.output.analysis &&
               !task.output.decision &&
               !task.output.content &&
               !task.output.implementation &&
               !task.output.files &&
               !task.output.error && (
                <div className="bg-secondary/50 p-4 rounded-lg">
                  <h5 className="font-medium text-sm mb-2 text-primary">Output</h5>
                  <pre className="text-sm bg-background p-3 rounded overflow-x-auto border max-h-96">
                    {JSON.stringify(task.output, null, 2)}
                  </pre>
                </div>
              )}
            </CardContent>
          </Card>
        )}

        {/* Blocking Reason (if task is blocked) */}
        {task.status === TaskStatus.BLOCKED && task.blocking_reason && (
          <Card className="border-destructive">
            <CardHeader>
              <CardTitle className="text-destructive">Task Blocked</CardTitle>
              <CardDescription>This task is currently blocked</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-start gap-3">
                <AlertCircle className="h-5 w-5 text-destructive mt-0.5" />
                <div>
                  <p className="font-medium mb-1">Blocking Reason:</p>
                  <p className="text-sm text-muted-foreground">{task.blocking_reason}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Dependencies */}
        {task.dependencies && task.dependencies.length > 0 && (
          <Card>
            <CardHeader>
              <CardTitle>Dependencies</CardTitle>
              <CardDescription>Tasks that must be completed first</CardDescription>
            </CardHeader>
            <CardContent>
              <ul className="space-y-2">
                {task.dependencies.map((dep: string, idx: number) => (
                  <li key={idx} className="text-sm flex items-center">
                    <Circle className="mr-2 h-3 w-3 text-muted-foreground" />
                    {dep}
                  </li>
                ))}
              </ul>
            </CardContent>
          </Card>
        )}

        {/* Feedback Components Section */}
        <div className="space-y-6">
          {/* Feedback Dialog */}
          <FeedbackDialog
            entityType="task"
            entityId={id}
            entityName={task.title}
            isOpen={feedbackOpen}
            onOpenChange={setFeedbackOpen}
            onFeedbackSubmitted={() => {
              fetchFeedback();
            }}
          />

          {/* Feedback Display */}
          <FeedbackDisplay
            entityType="task"
            entityId={id}
          />

          {/* Context Updates */}
          <ContextDisplay
            entityType="task"
            entityId={id}
          />
        </div>
      </div>

      {/* Cancel Task Dialog */}
      <ConfirmDialog
        open={showCancelDialog}
        onOpenChange={(open) => {
          setShowCancelDialog(open);
          if (!open) setCancelReason("");
        }}
        title="Cancel Task"
        description="Cancel this task. The agent will stop working on it immediately."
        confirmText="Cancel Task"
        onConfirm={handleCancel}
        isLoading={isCancelling}
        variant="warning"
      >
        <div className="space-y-4">
          <div className="bg-orange-50 border border-orange-200 p-4 rounded-lg">
            <h4 className="font-semibold mb-2 text-orange-700">Note</h4>
            <ul className="text-sm space-y-1 list-disc list-inside text-muted-foreground">
              <li>Task status will be set to CANCELLED</li>
              <li>The assigned agent will stop working on this task</li>
              <li>The cancellation reason will be recorded</li>
            </ul>
          </div>
          <div className="space-y-2">
            <Label htmlFor="cancel-reason">Cancellation Reason *</Label>
            <Input
              id="cancel-reason"
              placeholder="e.g., Taking too long, Wrong approach, No longer needed..."
              value={cancelReason}
              onChange={(e) => setCancelReason(e.target.value)}
              disabled={isCancelling}
            />
          </div>
        </div>
      </ConfirmDialog>

      {/* Approve Task Dialog */}
      <ConfirmDialog
        open={showApproveDialog}
        onOpenChange={setShowApproveDialog}
        title="Approve Task"
        description="Approve this task and move it to COMPLETED status."
        confirmText="Approve Task"
        onConfirm={handleApprove}
        isLoading={isApproving}
        variant="success"
      >
        <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
          <h4 className="font-semibold mb-2 text-green-700">Approval Details</h4>
          <ul className="text-sm space-y-1 list-disc list-inside text-muted-foreground">
            <li>Task status will be set to COMPLETED</li>
            <li>The task output will be finalized and available for use</li>
            <li>This action is permanent and cannot be undone</li>
          </ul>
        </div>
      </ConfirmDialog>
    </DashboardLayout>
  );
}
