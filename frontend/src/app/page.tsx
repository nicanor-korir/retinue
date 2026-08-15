"use client";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useDashboard, useProjects, useAgentStatus, useMessages, useEscalations, useNotificationCount } from "@/hooks/useApi";
import { FolderKanban, ListTodo, Users, Clock, CheckCircle2, AlertTriangle, Bell, Activity } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";
import { getProjectStatusColor, getTaskStatusColor } from "@/lib/status-utils";
import Link from "next/link";
import { ProjectStatus, TaskStatus, Availability } from "@/types/api";

function StatCard({
  title,
  value,
  description,
  icon: Icon,
  trend,
}: {
  title: string;
  value: string | number;
  description: string;
  icon: any;
  trend?: string;
}) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p className="text-xs text-muted-foreground">{description}</p>
        {trend && (
          <p className="mt-1 text-xs text-green-600">{trend}</p>
        )}
      </CardContent>
    </Card>
  );
}

export default function DashboardPage() {
  const { data: dashboard, isLoading: dashboardLoading } = useDashboard();
  const { data: projects } = useProjects();
  const { data: agents } = useAgentStatus();
  const { data: messages } = useMessages({ limit: 5 });
  const { data: escalations } = useEscalations({ status: 'open', limit: 100 });
  const { data: unreadNotifications } = useNotificationCount();

  if (dashboardLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </DashboardLayout>
    );
  }

  const activeProjects = projects?.filter(p => p.status === ProjectStatus.IN_PROGRESS) || [];
  const blockedTasks = dashboard?.recent_activity?.tasks?.filter(t => t.status === TaskStatus.BLOCKED) || [];
  const reviewTasks = dashboard?.recent_activity?.tasks?.filter(t => t.status === TaskStatus.REVIEW) || [];
  const failedProjects = projects?.filter(p => p.status === ProjectStatus.FAILED) || [];
  const openEscalations = escalations?.length || 0;
  const availableAgents = agents?.filter(a => a.availability === Availability.AVAILABLE).length || 0;
  const busyAgents = agents?.filter(a => a.availability === Availability.BUSY).length || 0;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Stats Grid */}
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
          <StatCard
            title="Total Projects"
            value={dashboard?.total_projects || 0}
            description={`${dashboard?.active_projects || 0} active`}
            icon={FolderKanban}
          />
          <StatCard
            title="Total Tasks"
            value={dashboard?.total_tasks || 0}
            description={`${dashboard?.in_progress_tasks || 0} in progress`}
            icon={ListTodo}
          />
          <StatCard
            title="Active Agents"
            value={`${dashboard?.active_agents || 0}/${dashboard?.total_agents || 0}`}
            description="Agents online"
            icon={Users}
          />
          <StatCard
            title="Completion Rate"
            value={
              dashboard?.total_tasks
                ? `${Math.round((dashboard.completed_tasks / dashboard.total_tasks) * 100)}%`
                : "0%"
            }
            description={`${dashboard?.completed_tasks || 0} tasks completed`}
            icon={CheckCircle2}
          />
        </div>

        <div className="grid gap-6 md:grid-cols-2">
          {/* Recent Projects */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Projects</CardTitle>
              <CardDescription>Latest project activity</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {dashboard?.recent_activity?.projects?.slice(0, 5).map((project) => (
                <Link
                  key={project.project_id}
                  href={`/projects/${project.project_id}`}
                  className="block space-y-2 rounded-lg border p-3 transition-colors hover:bg-accent"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{project.name}</span>
                    <Badge variant={getProjectStatusColor(project.status)}>
                      {project.status}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-1">
                    {project.description}
                  </p>
                  <div className="flex items-center text-xs text-muted-foreground">
                    <Clock className="mr-1 h-3 w-3" />
                    {formatRelativeTime(project.created_at)}
                  </div>
                </Link>
              )) || (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No projects yet. Create your first project!
                </p>
              )}
            </CardContent>
          </Card>

          {/* System Health */}
          <Card>
            <CardHeader>
              <CardTitle>System Health</CardTitle>
              <CardDescription>Key metrics and alerts</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Agent Capacity */}
              <div className="rounded-lg border p-3">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    <span className="text-sm font-medium">Agent Capacity</span>
                  </div>
                  <Badge variant={availableAgents > 0 ? "success" : "warning"}>
                    {availableAgents}/{agents?.length || 0}
                  </Badge>
                </div>
                <div className="text-xs text-muted-foreground">
                  {availableAgents} available, {busyAgents} busy
                </div>
              </div>

              {/* Open Escalations */}
              {openEscalations > 0 && (
                <Link href="/escalations" className="block">
                  <div className="rounded-lg border p-3 transition-colors hover:bg-accent">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <AlertTriangle className="h-4 w-4 text-orange-500" />
                        <span className="text-sm font-medium">Open Escalations</span>
                      </div>
                      <Badge variant="destructive">{openEscalations}</Badge>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Require attention
                    </div>
                  </div>
                </Link>
              )}

              {/* Blocked Tasks */}
              {blockedTasks.length > 0 && (
                <Link href="/tasks?status=BLOCKED" className="block">
                  <div className="rounded-lg border p-3 transition-colors hover:bg-accent">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <AlertTriangle className="h-4 w-4 text-red-500" />
                        <span className="text-sm font-medium">Blocked Tasks</span>
                      </div>
                      <Badge variant="destructive">{blockedTasks.length}</Badge>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Need resolution
                    </div>
                  </div>
                </Link>
              )}

              {/* Tasks in Review */}
              {reviewTasks.length > 0 && (
                <Link href="/tasks?status=REVIEW" className="block">
                  <div className="rounded-lg border p-3 transition-colors hover:bg-accent">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <Activity className="h-4 w-4 text-blue-500" />
                        <span className="text-sm font-medium">Tasks in Review</span>
                      </div>
                      <Badge variant="info">{reviewTasks.length}</Badge>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Awaiting approval
                    </div>
                  </div>
                </Link>
              )}

              {/* Unread Notifications */}
              {(unreadNotifications || 0) > 0 && (
                <Link href="/notifications" className="block">
                  <div className="rounded-lg border p-3 transition-colors hover:bg-accent">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center space-x-2">
                        <Bell className="h-4 w-4 text-purple-500" />
                        <span className="text-sm font-medium">Notifications</span>
                      </div>
                      <Badge variant="secondary">{unreadNotifications}</Badge>
                    </div>
                    <div className="text-xs text-muted-foreground">
                      Unread messages
                    </div>
                  </div>
                </Link>
              )}

              {/* All Good State */}
              {openEscalations === 0 && blockedTasks.length === 0 && reviewTasks.length === 0 && (unreadNotifications || 0) === 0 && (
                <div className="rounded-lg border border-green-200 bg-green-50 p-4 text-center">
                  <CheckCircle2 className="h-8 w-8 text-green-600 mx-auto mb-2" />
                  <p className="text-sm font-medium text-green-900">All systems running smoothly</p>
                  <p className="text-xs text-green-700 mt-1">No critical issues detected</p>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Recent Tasks */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Tasks</CardTitle>
              <CardDescription>Latest task updates</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {dashboard?.recent_activity?.tasks?.slice(0, 5).map((task) => (
                <Link
                  key={task.task_id}
                  href={`/tasks/${task.task_id}`}
                  className="block rounded-lg border p-3 transition-colors hover:bg-accent"
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium line-clamp-1">{task.title}</span>
                    <Badge variant={getTaskStatusColor(task.status)} className="text-xs">
                      {task.status}
                    </Badge>
                  </div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{task.assigned_to_agent_id}</span>
                    <span>{formatRelativeTime(task.updated_at)}</span>
                  </div>
                </Link>
              )) || (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No tasks yet
                </p>
              )}
            </CardContent>
          </Card>

          {/* Recent Messages */}
          <Card>
            <CardHeader>
              <CardTitle>Recent Messages</CardTitle>
              <CardDescription>Agent communications</CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              {messages?.map((message) => (
                <div
                  key={message.message_id}
                  className="rounded-lg border p-3"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center space-x-2">
                      <span className="text-sm font-medium">{message.from_agent_id}</span>
                      <span className="text-xs text-muted-foreground">→</span>
                      <span className="text-sm text-muted-foreground">{message.to_agent_id}</span>
                    </div>
                    <Badge variant={message.priority === "high" || message.priority === "critical" ? "destructive" : "secondary"} className="text-xs">
                      {message.message_type}
                    </Badge>
                  </div>
                  <p className="text-sm text-muted-foreground line-clamp-2">
                    {message.content}
                  </p>
                  <p className="text-xs text-muted-foreground mt-2">
                    {formatRelativeTime(message.created_at)}
                  </p>
                </div>
              )) || (
                <p className="text-sm text-muted-foreground text-center py-8">
                  No messages yet
                </p>
              )}
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
