"use client";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { useProjects } from "@/hooks/useApi";
import { Plus, FolderKanban, Calendar, User, RefreshCw } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";
import Link from "next/link";
import { ProjectStatus } from "@/types/api";
import { useState } from "react";
import { getProjectStatusColor } from "@/lib/status-utils";

export default function ProjectsPage() {
  const { data: projects, isLoading, refetch } = useProjects();
  const [isRefreshing, setIsRefreshing] = useState(false);

  const handleRefresh = async () => {
    setIsRefreshing(true);
    try {
      await refetch();
    } finally {
      setIsRefreshing(false);
    }
  };

  const projectsByStatus = {
    [ProjectStatus.PLANNING]: projects?.filter(p => p.status === ProjectStatus.PLANNING) || [],
    [ProjectStatus.IN_PROGRESS]: projects?.filter(p => p.status === ProjectStatus.IN_PROGRESS) || [],
    [ProjectStatus.REVIEW]: projects?.filter(p => p.status === ProjectStatus.REVIEW) || [],
    [ProjectStatus.COMPLETED]: projects?.filter(p => p.status === ProjectStatus.COMPLETED) || [],
    [ProjectStatus.ON_HOLD]: projects?.filter(p => p.status === ProjectStatus.ON_HOLD) || [],
    [ProjectStatus.CANCELLED]: projects?.filter(p => p.status === ProjectStatus.CANCELLED) || [],
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

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Projects</h1>
            <p className="text-muted-foreground">
              Manage and monitor all your AI-generated projects
            </p>
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
            <Link href="/projects/create">
              <Button>
                <Plus className="mr-2 h-4 w-4" />
                New Project
              </Button>
            </Link>
          </div>
        </div>

        {/* Stats */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Projects
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{projects?.length || 0}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                In Progress
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{projectsByStatus[ProjectStatus.IN_PROGRESS].length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Completed
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{projectsByStatus[ProjectStatus.COMPLETED].length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Planning
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{projectsByStatus[ProjectStatus.PLANNING].length}</div>
            </CardContent>
          </Card>
        </div>

        {/* Projects Grid */}
        {projects && projects.length > 0 ? (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {projects.map((project) => (
              <Link
                key={project.project_id}
                href={`/projects/${project.project_id}`}
              >
                <Card className="h-full transition-all hover:shadow-lg hover:-translate-y-1">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex items-center gap-2">
                        <FolderKanban className="h-8 w-8 text-primary" />
                        {(project as any).version && (project as any).version > 1 && (
                          <Badge variant="outline" className="font-mono text-xs">
                            v{(project as any).version}
                          </Badge>
                        )}
                      </div>
                      <Badge variant={getProjectStatusColor(project.status)}>
                        {project.status}
                      </Badge>
                    </div>
                    <CardTitle className="mt-4">{project.name}</CardTitle>
                    <CardDescription className="line-clamp-2">
                      {project.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2 text-sm">
                      <div className="flex items-center text-muted-foreground">
                        <User className="mr-2 h-4 w-4" />
                        {project.owner_agent_id}
                      </div>
                      <div className="flex items-center text-muted-foreground">
                        <Calendar className="mr-2 h-4 w-4" />
                        Created {formatRelativeTime(project.created_at)}
                      </div>
                      {project.tasks && (
                        <div className="pt-2 border-t">
                          <div className="text-xs text-muted-foreground">
                            {project.tasks.length} tasks
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        ) : (
          <Card>
            <CardContent className="flex flex-col items-center justify-center py-16">
              <FolderKanban className="h-16 w-16 text-muted-foreground mb-4" />
              <h3 className="text-lg font-semibold mb-2">No projects yet</h3>
              <p className="text-muted-foreground mb-4 text-center">
                Get started by creating your first AI-powered project
              </p>
              <Link href="/projects/create">
                <Button>
                  <Plus className="mr-2 h-4 w-4" />
                  Create Project
                </Button>
              </Link>
            </CardContent>
          </Card>
        )}
      </div>
    </DashboardLayout>
  );
}
