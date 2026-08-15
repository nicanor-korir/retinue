"use client";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { useTasks } from "@/hooks/useApi";
import { ListTodo, User, Code, RefreshCw, Clock } from "lucide-react";
import { Button } from "@/components/ui/button";
import { formatRelativeTime } from "@/lib/utils";
import { getTaskStatusColor, getTaskStatusIcon } from "@/lib/status-utils";
import { LoadingState } from "@/components/common/LoadingState";
import { EmptyState } from "@/components/common/EmptyState";
import { useRefresh } from "@/hooks/useRefresh";
import Link from "next/link";
import { TaskStatus } from "@/types/api";
import { useState } from "react";

export default function TasksPage() {
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  const { data: tasks, isLoading, refetch } = useTasks({ status: statusFilter });
  const { isRefreshing, handleRefresh } = useRefresh(refetch);

  if (isLoading) {
    return <LoadingState />;
  }

  const tasksByStatus = {
    [TaskStatus.PENDING]: tasks?.filter(t => t.status === TaskStatus.PENDING) || [],
    [TaskStatus.IN_PROGRESS]: tasks?.filter(t => t.status === TaskStatus.IN_PROGRESS) || [],
    [TaskStatus.REVIEW]: tasks?.filter(t => t.status === TaskStatus.REVIEW) || [],
    [TaskStatus.COMPLETED]: tasks?.filter(t => t.status === TaskStatus.COMPLETED) || [],
    [TaskStatus.BLOCKED]: tasks?.filter(t => t.status === TaskStatus.BLOCKED) || [],
  };

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Tasks</h1>
            <p className="text-muted-foreground">
              View and monitor all tasks across projects
            </p>
          </div>
          <Button
            variant="outline"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw className={`mr-2 h-4 w-4 ${isRefreshing ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
        </div>

        {/* Stats */}
        <div className="grid gap-4 md:grid-cols-5">
          {Object.entries(tasksByStatus).map(([status, statusTasks]) => (
            <Card
              key={status}
              className={`cursor-pointer transition-all ${
                statusFilter === status ? "ring-2 ring-primary" : ""
              }`}
              onClick={() => setStatusFilter(statusFilter === status ? undefined : status)}
            >
              <CardHeader className="pb-2">
                <CardTitle className="text-sm font-medium text-muted-foreground capitalize">
                  {status.replace("_", " ")}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="text-2xl font-bold">{statusTasks.length}</div>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Filter indicator */}
        {statusFilter && (
          <div className="flex items-center space-x-2">
            <span className="text-sm text-muted-foreground">Filtering by:</span>
            <Badge variant={getTaskStatusColor(statusFilter as TaskStatus)}>
              {statusFilter}
            </Badge>
            <button
              onClick={() => setStatusFilter(undefined)}
              className="text-sm text-primary hover:underline"
            >
              Clear filter
            </button>
          </div>
        )}

        {/* Tasks List */}
        <div className="space-y-3">
          {tasks && tasks.length > 0 ? (
            tasks.map((task) => (
              <Link key={task.task_id} href={`/tasks/${task.task_id}`}>
                <Card className="hover:shadow-md transition-shadow">
                  <CardContent className="p-4">
                    <div className="flex items-start space-x-4">
                      <div className="mt-0.5">
                        {getTaskStatusIcon(task.status)}
                      </div>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between mb-2">
                          <h4 className="font-medium line-clamp-1">{task.title}</h4>
                          <Badge variant={getTaskStatusColor(task.status)}>
                            {task.status}
                          </Badge>
                        </div>
                        {task.description && (
                          <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
                            {task.description}
                          </p>
                        )}
                        <div className="flex items-center flex-wrap gap-4 text-xs text-muted-foreground">
                          <span className="flex items-center">
                            <User className="mr-1 h-3 w-3" />
                            {task.assigned_to_agent_id}
                          </span>
                          <span className="flex items-center">
                            <Clock className="mr-1 h-3 w-3" />
                            {formatRelativeTime(task.updated_at)}
                          </span>
                          {task.output && Object.keys(task.output).length > 0 && (
                            <span className="flex items-center text-green-600">
                              <Code className="mr-1 h-3 w-3" />
                              Has output
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))
          ) : (
            <EmptyState
              icon={ListTodo}
              title="No tasks found"
              description={
                statusFilter
                  ? `No tasks with status "${statusFilter}"`
                  : "Tasks will appear here once projects are created"
              }
            />
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}
