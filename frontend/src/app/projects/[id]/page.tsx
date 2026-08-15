"use client";

import { useState, useEffect, useRef } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { useProject, useTasks, useRestartProject, useProjectVersions, useDeleteProject, useProjectActivity, useCancelProject, useApproveProject } from "@/hooks/useApi";
import { ArrowLeft, Calendar, User, Clock, CheckCircle2, Code, RotateCcw, History, Trash2, RefreshCw, Ban, MessageSquare, Check } from "lucide-react";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { ActivityFeed } from "@/components/activity/activity-feed";
import { ProjectOutput } from "@/components/project/project-output";
import { LiveStreamFeed } from "@/components/realtime/live-stream-feed";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { formatRelativeTime, formatDateTime } from "@/lib/utils";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { ProjectStatus, TaskStatus, Priority } from "@/types/api";
import { ExportDialogV2 } from '@/components/export/ExportDialogV2';
import { Download } from 'lucide-react';
import { FeedbackDialog } from '@/components/feedback/feedback-dialog';
import { FeedbackDisplay } from '@/components/feedback/feedback-display';
import { ContextDisplay } from '@/components/feedback/context-display';
import { ProjectHealth } from '@/components/feedback/project-health';
import { useProjectFeedback } from '@/hooks/useFeedback';
import { ProjectChatPanel } from '@/components/project/project-chat-panel';
import { getProjectStatusColor, getProjectStatusIcon, getTaskStatusColor, getTaskStatusIcon } from "@/lib/status-utils";

export default function ProjectDetailPage({ params }: { params: { id: string } }) {
  const { id } = params;
  const router = useRouter();

  // Ensure id is a valid string, not undefined
  const validId = id && typeof id === "string" && id !== "undefined" ? id : undefined;

  const { data: project, isLoading, refetch: refetchProject } = useProject(validId || "");
  const { data: tasks, refetch: refetchTasks } = useTasks(validId ? { project_id: validId } : undefined);
  const { data: versions, refetch: refetchVersions } = useProjectVersions(validId || "");
  const { data: activities, isLoading: activitiesLoading } = useProjectActivity(validId || "", 50);
  const restartProject = useRestartProject();
  const deleteProject = useDeleteProject();
  const cancelProject = useCancelProject();
  const approveProject = useApproveProject();

  const [showRestartDialog, setShowRestartDialog] = useState(false);
  const [showVersionsDialog, setShowVersionsDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const [showCancelDialog, setShowCancelDialog] = useState(false);
  const [showApproveDialog, setShowApproveDialog] = useState(false);
  const [isRestarting, setIsRestarting] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [isApproving, setIsApproving] = useState(false);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [cancelReason, setCancelReason] = useState("");

  const [exportOpen, setExportOpen] = useState(false);
  const [feedbackOpen, setFeedbackOpen] = useState(false);
  const { feedback, fetchFeedback } = useProjectFeedback(id);
  const [chatOpen, setChatOpen] = useState(false);
  const [feedbackSectionOpen, setFeedbackSectionOpen] = useState(false);
  const chatSectionRef = useRef<HTMLDivElement>(null);
  const feedbackSectionRef = useRef<HTMLDivElement>(null);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await Promise.all([
        refetchProject(),
        refetchTasks(),
        refetchVersions(),
        fetchFeedback()
      ]);
    } finally {
      setIsRefreshing(false);
    }
  };

  const handleOpenTeamChat = () => {
    setChatOpen(true);
    // Scroll to chat section after a brief delay to allow accordion to open
    setTimeout(() => {
      chatSectionRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }, 100);
  };

  const handleOpenFeedback = () => {
    setFeedbackOpen(true);
    setFeedbackSectionOpen(true);
    // Scroll to feedback section after a brief delay to allow accordion to open
    setTimeout(() => {
      feedbackSectionRef.current?.scrollIntoView({
        behavior: 'smooth',
        block: 'start'
      });
    }, 100);
  };

  useEffect(() => {
    fetchFeedback();
  }, [id, fetchFeedback]);

  const handleRestart = async () => {
    if (!project) return;
    
    setIsRestarting(true);
    try {
      const result = await restartProject.mutateAsync({ 
        id,
        data: {
          name: project.name,
          description: project.description,
          priority: (project.metadata?.priority as Priority) || Priority.MEDIUM,
        }
      });
      setShowRestartDialog(false);
      // Navigate to the new version
      router.push(`/projects/${result.project_id}`);
    } catch (error) {
      console.error("Failed to restart project:", error);
    } finally {
      setIsRestarting(false);
    }
  };

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await deleteProject.mutateAsync(id);
      setShowDeleteDialog(false);
      // Navigate back to projects page immediately
      router.push("/projects");
    } catch (error) {
      console.error("Failed to delete project:", error);
      setIsDeleting(false);
    }
    // Don't set isDeleting to false here - let navigation happen
  };

  const handleCancel = async () => {
    if (!cancelReason.trim()) {
      return;
    }
    setIsCancelling(true);
    try {
      await cancelProject.mutateAsync({ id, reason: cancelReason });
      setShowCancelDialog(false);
      setCancelReason("");
      // Refresh project data to show updated status
      await refetchProject();
    } catch (error) {
      console.error("Failed to cancel project:", error);
    } finally {
      setIsCancelling(false);
    }
  };

  const handleApprove = async () => {
    setIsApproving(true);
    try {
      await approveProject.mutateAsync(id);
      setShowApproveDialog(false);
      // Refresh project data to show updated status
      await refetchProject();
    } catch (error) {
      console.error("Failed to approve project:", error);
    } finally {
      setIsApproving(false);
    }
  };

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </DashboardLayout>
    );
  }

  if (!project) {
    return (
      <DashboardLayout>
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-16">
            <h3 className="text-lg font-semibold mb-2">Project not found</h3>
            <Link href="/projects">
              <Button>
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Projects
              </Button>
            </Link>
          </CardContent>
        </Card>
      </DashboardLayout>
    );
  }

  const completedTasks = tasks?.filter(t => t.status === TaskStatus.COMPLETED).length || 0;
  const totalTasks = tasks?.length || 0;
  const progress = totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          {/* Top row: Back button and action buttons */}
          <div className="flex items-center justify-between mb-4">
            <Link href="/projects">
              <Button variant="ghost">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Back to Projects
              </Button>
            </Link>
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
                onClick={handleOpenTeamChat}
              >
                <MessageSquare className="h-4 w-4" />
                Team Chat
              </Button>
              <Button
                variant="outline"
                className="gap-2"
                onClick={handleOpenFeedback}
              >
                <MessageSquare className="h-4 w-4" />
                Feedback
              </Button>
              {project.status === ProjectStatus.REVIEW && (
                <Button
                  onClick={() => setShowApproveDialog(true)}
                  className="gap-2 bg-green-600 hover:bg-green-700"
                >
                  <Check className="h-4 w-4" />
                  Approve
                </Button>
              )}
              {/* Export available for any project with tasks */}
              <Button onClick={() => setExportOpen(true)} variant="outline" className="gap-2">
                <Download className="h-4 w-4" /> Export
              </Button>
              {versions && versions.length > 1 && (
                <Button variant="outline" onClick={() => setShowVersionsDialog(true)}>
                  <History className="mr-2 h-4 w-4" />
                  Version
                </Button>
              )}
              <Button variant="outline" onClick={() => setShowRestartDialog(true)}>
                <RotateCcw className="mr-2 h-4 w-4" />
                Restart
              </Button>
              {(project.status === ProjectStatus.IN_PROGRESS ||
                project.status === ProjectStatus.PLANNING ||
                project.status === ProjectStatus.REVIEW) && (
                <Button
                  variant="outline"
                  className="border-orange-500 text-orange-600 hover:bg-orange-50"
                  onClick={() => setShowCancelDialog(true)}
                >
                  <Ban className="mr-2 h-4 w-4" />
                  Cancel
                </Button>
              )}
              <Button variant="destructive" onClick={() => setShowDeleteDialog(true)}>
                <Trash2 className="mr-2 h-4 w-4" />
                Delete
              </Button>
            </div>
          </div>
          
          {/* Project title and info */}
          <div>
            <div className="flex items-center space-x-3 mb-2">
              {getProjectStatusIcon(project.status)}
              <h1 className="text-3xl font-bold tracking-tight">{project.name}</h1>
              <Badge variant={getProjectStatusColor(project.status)}>
                {project.status}
              </Badge>
              {versions && versions.length > 1 && (
                <Badge variant="outline">v{versions[versions.length - 1].version}</Badge>
              )}
            </div>
            <p className="text-muted-foreground max-w-3xl">
              {project.description}
            </p>
          </div>
        </div>

        {/* Completion Notice - Show for projects with all tasks complete but project not marked complete yet */}
        {project.status !== ProjectStatus.COMPLETED &&
         project.status !== ProjectStatus.CANCELLED &&
         project.status !== ProjectStatus.FAILED &&
         totalTasks > 0 &&
         completedTasks === totalTasks && (
          <Card className="border-2 border-green-500 bg-green-50 dark:bg-green-950/30">
            <CardContent className="pt-6">
              <div className="flex items-start gap-4">
                <CheckCircle2 className="h-8 w-8 text-green-600 flex-shrink-0" />
                <div className="flex-1">
                  <h3 className="text-lg font-semibold text-green-900 dark:text-green-100 mb-2">
                    All Tasks Completed!
                  </h3>
                  <p className="text-sm text-green-700 dark:text-green-300 mb-3">
                    All {totalTasks} tasks have been completed. The PM agent will automatically mark this project as complete in the next check cycle
                  </p>
                  <p className="text-xs text-green-600 dark:text-green-400">
                    The system verifies that no agents are still working and no pending approvals remain before finalizing the project.
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Project Info */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Owner
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center">
                <User className="mr-2 h-4 w-4 text-muted-foreground" />
                <span className="text-sm font-medium">{project.owner_agent_id}</span>
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
                <span className="text-sm font-medium">{formatDateTime(project.created_at)}</span>
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
                <span className="text-sm font-medium">{formatDateTime(project.updated_at)}</span>
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Progress
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="font-medium">{Math.round(progress)}%</span>
                  <span className="text-muted-foreground">{completedTasks}/{totalTasks} tasks</span>
                </div>
                <div className="w-full bg-secondary rounded-full h-2">
                  <div
                    className="bg-primary rounded-full h-2 transition-all"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Project Output - Show if any completed tasks have output */}
        {tasks && tasks.length > 0 && (() => {
          // Find completed tasks with output, prioritize CEO tasks
          const completedTasksWithOutput = tasks.filter(
            t => (t.status === TaskStatus.COMPLETED) && t.output && Object.keys(t.output).length > 0
          );
          
          if (completedTasksWithOutput.length === 0) return null;
          
          // Prioritize CEO tasks
          const ceoTask = completedTasksWithOutput.find(t => (t as any).assigned_to === 'ceo_001' || t.assigned_to_agent_id === 'ceo_001');
          const taskToDisplay = ceoTask || completedTasksWithOutput[0];
          
          return (
            <ProjectOutput
              output={taskToDisplay.output}
              projectName={project.name}
              projectId={id}
              projectStatus={project.status}
              onContinue={() => {
                router.push('/projects?action=new');
              }}
              onExpand={() => {
                setShowRestartDialog(true);
              }}
            />
          );
        })()}

        {/* Team Chat - Always visible */}
        <Card ref={chatSectionRef}>
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
                      <span>Team Chat</span>
                    </CardTitle>
                    <CardDescription className="text-xs mt-1">
                      Chat with all project agents in real-time
                    </CardDescription>
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent className="px-6 pb-4">
                <ProjectChatPanel projectId={id} projectName={project.name} />
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </Card>

        {/* Project Activity - Collapsible Tabbed view */}
        {(project.status === ProjectStatus.IN_PROGRESS || project.status === ProjectStatus.PLANNING || project.status === ProjectStatus.REVIEW) && (
          <Card>
            <Accordion type="single" collapsible defaultValue="activity">
              <AccordionItem value="activity" className="border-0">
                <AccordionTrigger className="px-6 py-4 hover:no-underline hover:bg-accent/50">
                  <div className="flex items-center gap-3 text-left">
                    <div>
                      <CardTitle>Project Activity</CardTitle>
                      <CardDescription className="text-xs mt-1">
                        Real-time updates and agent activities
                      </CardDescription>
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-6 pb-4">
                  <Tabs defaultValue="live-stream" className="w-full">
                    <TabsList className="grid w-full grid-cols-2 max-w-md">
                      <TabsTrigger value="live-stream">🔴 Live Stream</TabsTrigger>
                      <TabsTrigger value="activity-log">Activity Log</TabsTrigger>
                    </TabsList>

                    <TabsContent value="live-stream" className="mt-6">
                      <LiveStreamFeed projectId={id} />
                    </TabsContent>

                    <TabsContent value="activity-log" className="mt-6">
                      <ActivityFeed
                        activities={activities || []}
                        isLoading={activitiesLoading}
                        title="Activity Log"
                        description="Historical updates and agent activities"
                      />
                    </TabsContent>
                  </Tabs>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </Card>
        )}

        {/* Tasks - Collapsible */}
        <Card>
          <Accordion type="single" collapsible defaultValue="tasks">
            <AccordionItem value="tasks" className="border-0">
              <AccordionTrigger className="px-6 py-4 hover:no-underline hover:bg-accent/50">
                <div className="flex items-center gap-3 text-left">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <span>Tasks</span>
                      <Badge variant="outline" className="ml-1">
                        {totalTasks}
                      </Badge>
                    </CardTitle>
                    <CardDescription className="text-xs mt-1">
                      {completedTasks} of {totalTasks} completed
                    </CardDescription>
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent className="px-6 pb-4">
                {tasks && tasks.length > 0 ? (
                  <div className="space-y-3">
                    {tasks.map((task) => (
                      <Link
                        key={task.task_id}
                        href={`/tasks/${task.task_id}`}
                        className="block"
                      >
                        <div className="flex items-start space-x-4 p-4 border rounded-lg hover:bg-accent transition-colors">
                          <div className="mt-0.5">
                            {getTaskStatusIcon(task.status)}
                          </div>
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center justify-between mb-1">
                              <h4 className="font-medium line-clamp-1">{task.title}</h4>
                              <Badge variant={getTaskStatusColor(task.status)} className="ml-2">
                                {task.status}
                              </Badge>
                            </div>
                            {task.description && (
                              <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
                                {task.description}
                              </p>
                            )}
                            <div className="flex items-center text-xs text-muted-foreground space-x-4">
                              <span>{task.assigned_to_agent_id}</span>
                              <span>•</span>
                              <span>Updated {formatRelativeTime(task.updated_at)}</span>
                              {task.output && Object.keys(task.output).length > 0 && (
                                <>
                                  <span>•</span>
                                  <span className="flex items-center">
                                    <Code className="mr-1 h-3 w-3" />
                                    Has output
                                  </span>
                                </>
                              )}
                            </div>
                          </div>
                        </div>
                      </Link>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <p className="text-muted-foreground">
                      No tasks yet. The PM agent will create tasks soon.
                    </p>
                  </div>
                )}
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </Card>

        {/* Deliverables & Outputs - Collapsible */}
        {tasks && tasks.filter(t => t.output && Object.keys(t.output).length > 0).length > 0 && (
          <Card>
            <Accordion type="single" collapsible>
              <AccordionItem value="deliverables" className="border-0">
                <AccordionTrigger className="px-6 py-4 hover:no-underline hover:bg-accent/50">
                  <div className="flex items-center gap-3 text-left">
                    <div>
                      <CardTitle className="flex items-center gap-2">
                        <span>Deliverables & Outputs</span>
                        <Badge variant="secondary" className="ml-1">
                          {tasks.filter(t => t.output && Object.keys(t.output).length > 0).length}
                        </Badge>
                      </CardTitle>
                      <CardDescription className="text-xs mt-1">
                        Generated content, artifacts, and results from completed tasks
                      </CardDescription>
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-6 pb-4">
                  <div className="space-y-6">
                    {tasks
                      .filter(t => t.output && Object.keys(t.output).length > 0)
                      .map((task) => (
                        <div key={task.task_id} className="border-l-4 border-primary pl-4">
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex-1">
                              <h4 className="font-semibold text-lg">{task.title}</h4>
                              <p className="text-sm text-muted-foreground">
                                By {task.assigned_to_agent_id} • {formatRelativeTime(task.updated_at)}
                              </p>
                            </div>
                            <Badge variant={getTaskStatusColor(task.status)} className="ml-2">
                              {task.status}
                            </Badge>
                          </div>

                          {/* Output Content */}
                          <div className="space-y-4">
                            {/* Decision/Analysis (for CEO/executive tasks) */}
                            {task.output.analysis && (
                              <div className="bg-secondary/50 p-4 rounded-lg">
                                <h5 className="font-medium text-sm mb-2 text-primary">Analysis</h5>
                                <div className="text-sm whitespace-pre-wrap line-clamp-3">{task.output.analysis}</div>
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
                                <h5 className="font-medium text-sm mb-2 text-primary">Generated Content</h5>
                                <pre className="text-sm bg-background p-3 rounded overflow-x-auto border max-h-48">
                                  {typeof task.output.content === 'string'
                                    ? task.output.content
                                    : JSON.stringify(task.output.content, null, 2)}
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

                            {/* Raw Output (for other data) */}
                            {!task.output.analysis && !task.output.decision && !task.output.content && !task.output.files && (
                              <div className="bg-secondary/50 p-4 rounded-lg">
                                <h5 className="font-medium text-sm mb-2 text-primary">Output</h5>
                                <pre className="text-sm bg-background p-3 rounded overflow-x-auto border max-h-48">
                                  {JSON.stringify(task.output, null, 2)}
                                </pre>
                              </div>
                            )}
                          </div>
                        </div>
                      ))}
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </Card>
        )}

        {/* Feedback Components Section - Collapsible */}
        <Card ref={feedbackSectionRef}>
          <Accordion
            type="single"
            collapsible
            value={feedbackSectionOpen ? "feedback" : undefined}
            onValueChange={(value) => setFeedbackSectionOpen(value === "feedback")}
          >
            <AccordionItem value="feedback" className="border-0">
              <AccordionTrigger className="px-6 py-4 hover:no-underline hover:bg-accent/50">
                <div className="flex items-center gap-3 text-left">
                  <div>
                    <CardTitle className="flex items-center gap-2">
                      <span>Feedback & Insights</span>
                      {feedback.length > 0 && (
                        <Badge variant="secondary" className="ml-1">
                          {feedback.length}
                        </Badge>
                      )}
                    </CardTitle>
                    <CardDescription className="text-xs mt-1">
                      Project feedback, health status, and context updates
                    </CardDescription>
                  </div>
                </div>
              </AccordionTrigger>
              <AccordionContent className="px-6 pb-4 space-y-6">
                {/* Feedback Dialog */}
                <FeedbackDialog
                  entityType="project"
                  entityId={id}
                  entityName={project.name}
                  isOpen={feedbackOpen}
                  onOpenChange={setFeedbackOpen}
                  onFeedbackSubmitted={() => {
                    fetchFeedback();
                  }}
                />

                {/* Project Health Dashboard */}
                {feedback.length > 0 && (
                  <ProjectHealth
                    feedback={feedback}
                    projectStatus={project.status}
                  />
                )}

                {/* Feedback Display */}
                <FeedbackDisplay
                  entityType="project"
                  entityId={id}
                />

                {/* Context Updates */}
                <ContextDisplay
                  entityType="project"
                  entityId={id}
                />
              </AccordionContent>
            </AccordionItem>
          </Accordion>
        </Card>

        {/* Metadata - Collapsible */}
        {project.metadata && Object.keys(project.metadata).length > 0 && (
          <Card>
            <Accordion type="single" collapsible>
              <AccordionItem value="metadata" className="border-0">
                <AccordionTrigger className="px-6 py-4 hover:no-underline hover:bg-accent/50">
                  <div className="flex items-center gap-3 text-left">
                    <div>
                      <CardTitle>Additional Information</CardTitle>
                    </div>
                  </div>
                </AccordionTrigger>
                <AccordionContent className="px-6 pb-4">
                  <pre className="text-sm bg-secondary p-4 rounded-lg overflow-x-auto max-h-64">
                    {JSON.stringify(project.metadata, null, 2)}
                  </pre>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </Card>
        )}
      </div>

      {/* Restart Dialog */}
      <Dialog open={showRestartDialog} onOpenChange={setShowRestartDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Restart Project</DialogTitle>
            <DialogDescription>
              This will create a new version of the project with the same requirements.
              The CEO and agents will re-evaluate and implement from scratch, potentially
              with improvements based on learnings.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="bg-secondary/50 p-4 rounded-lg">
              <h4 className="font-semibold mb-2">What happens when you restart:</h4>
              <ul className="text-sm space-y-1 list-disc list-inside text-muted-foreground">
                <li>A new version (v{((project as any).version || 1) + 1}) will be created</li>
                <li>The original project and its outputs remain unchanged</li>
                <li>CEO will re-evaluate the requirements</li>
                <li>Agents may produce different/improved outputs</li>
                <li>You can compare versions side-by-side</li>
              </ul>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowRestartDialog(false)} disabled={isRestarting}>
              Cancel
            </Button>
            <Button onClick={handleRestart} disabled={isRestarting}>
              {isRestarting ? "Restarting..." : "Restart Project"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Version History Dialog */}
      <Dialog open={showVersionsDialog} onOpenChange={setShowVersionsDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Version History</DialogTitle>
            <DialogDescription>
              All versions of this project
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {versions?.map((version: any) => (
              <div
                key={version.project_id}
                className={`p-4 border rounded-lg ${
                  version.is_current ? 'border-primary bg-primary/5' : ''
                }`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant={version.is_current ? 'default' : 'outline'}>
                        v{version.version}
                      </Badge>
                      {version.is_current && (
                        <Badge variant="secondary">Current</Badge>
                      )}
                      <Badge variant={getProjectStatusColor(version.status)}>
                        {version.status}
                      </Badge>
                    </div>
                    <h4 className="font-medium">{version.name}</h4>
                    <p className="text-xs text-muted-foreground mt-1">
                      Created {formatRelativeTime(version.created_at)}
                    </p>
                  </div>
                  {!version.is_current && (
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => {
                        router.push(`/projects/${version.project_id}`);
                        setShowVersionsDialog(false);
                      }}
                    >
                      View
                    </Button>
                  )}
                </div>
              </div>
            ))}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowVersionsDialog(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Cancel Project Dialog */}
      <Dialog open={showCancelDialog} onOpenChange={setShowCancelDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Cancel Project</DialogTitle>
            <DialogDescription>
              Cancel this in-progress project. All non-completed tasks will also be cancelled.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="bg-orange-50 border border-orange-200 p-4 rounded-lg">
              <h4 className="font-semibold mb-2 text-orange-700">Note</h4>
              <ul className="text-sm space-y-1 list-disc list-inside text-muted-foreground">
                <li>Project status will be set to CANCELLED</li>
                <li>All non-completed tasks will be cancelled automatically</li>
                <li>Agents will stop working on this project</li>
                <li>You'll need to provide a reason for cancellation</li>
              </ul>
            </div>
            <div className="space-y-2">
              <Label htmlFor="cancel-reason">Cancellation Reason *</Label>
              <Input
                id="cancel-reason"
                placeholder="e.g., Requirements changed, Taking too long, No longer needed..."
                value={cancelReason}
                onChange={(e) => setCancelReason(e.target.value)}
                disabled={isCancelling}
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => {
              setShowCancelDialog(false);
              setCancelReason("");
            }} disabled={isCancelling}>
              Close
            </Button>
            <Button
              variant="default"
              className="bg-orange-600 hover:bg-orange-700"
              onClick={handleCancel}
              disabled={isCancelling || !cancelReason.trim()}
            >
              {isCancelling ? "Cancelling..." : "Cancel Project"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Confirmation Dialog */}
      <Dialog open={showDeleteDialog} onOpenChange={setShowDeleteDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Delete Project</DialogTitle>
            <DialogDescription>
              Are you sure you want to delete this project? This action will mark the project and all its tasks as deleted.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="bg-destructive/10 border border-destructive/20 p-4 rounded-lg">
              <h4 className="font-semibold mb-2 text-destructive">Warning</h4>
              <ul className="text-sm space-y-1 list-disc list-inside text-muted-foreground">
                <li>This will soft delete the project (not permanently removed)</li>
                <li>All associated tasks will also be marked as deleted</li>
                <li>The project will no longer appear in your project list</li>
                <li>Data administrators can restore deleted projects if needed</li>
              </ul>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDeleteDialog(false)} disabled={isDeleting}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={handleDelete} disabled={isDeleting}>
              {isDeleting ? "Deleting..." : "Delete Project"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Approve Project Dialog */}
      <Dialog open={showApproveDialog} onOpenChange={setShowApproveDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Approve Project</DialogTitle>
            <DialogDescription>
              Approve this project and move it to COMPLETED status.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
              <h4 className="font-semibold mb-2 text-green-700">Approval Details</h4>
              <ul className="text-sm space-y-1 list-disc list-inside text-muted-foreground">
                <li>Project status will be set to COMPLETED</li>
                <li>All project deliverables will be available for export and deployment</li>
                <li>This action is permanent and cannot be undone</li>
              </ul>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowApproveDialog(false)} disabled={isApproving}>
              Cancel
            </Button>
            <Button
              onClick={handleApprove}
              disabled={isApproving}
              className="bg-green-600 hover:bg-green-700"
            >
              {isApproving ? "Approving..." : "Approve Project"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* New simplified export dialog - auto-downloads when complete */}
      <ExportDialogV2
        projectId={params.id}
        projectName={project?.name || "Project"}
        isOpen={exportOpen}
        onClose={() => setExportOpen(false)}
      />
    </DashboardLayout>
  );
}
