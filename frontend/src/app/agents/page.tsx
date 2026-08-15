"use client";

import { useEffect, useState, useMemo } from "react";
import Link from "next/link";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useAgentStatus } from "@/hooks/useApi";
import { useGlobalEventStream } from "@/hooks/useWebSocket";
import { Users, Activity, Clock, CheckCircle2, ArrowRight, Search } from "lucide-react";
import { Availability } from "@/types/api";

function getAvailabilityColor(availability: Availability) {
  switch (availability) {
    case Availability.AVAILABLE:
      return "success";
    case Availability.BUSY:
      return "warning";
    case Availability.OFFLINE:
      return "secondary";
    default:
      return "default";
  }
}

export default function AgentsPage() {
  const { data: agents, isLoading } = useAgentStatus();
  const { agentActivities } = useGlobalEventStream(true);
  const [agentStatuses, setAgentStatuses] = useState<Record<string, Availability>>({});
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedDepartment, setSelectedDepartment] = useState<string | null>(null);

  // Update agent statuses based on real-time activities
  useEffect(() => {
    const statuses: Record<string, Availability> = {};

    // Check which agents have active activities
    agentActivities.forEach((activity, agentId) => {
      if (activity.is_active) {
        statuses[agentId] = Availability.BUSY;
      }
    });

    setAgentStatuses(statuses);
  }, [agentActivities]);

  // Merge static agent data with real-time status
  const agentsWithRealTimeStatus = agents?.map(agent => ({
    ...agent,
    availability: agentStatuses[agent.agent_id] || agent.availability,
  })) || [];

  // Get unique departments (from all agents' departments arrays)
  const departments = useMemo(() => {
    const depts = new Set<string>();
    agentsWithRealTimeStatus.forEach(agent => {
      // Support both multi-department and legacy single department
      const agentDepts = agent.departments || [agent.department || "General"];
      agentDepts.forEach(dept => depts.add(dept));
    });
    return Array.from(depts).sort();
  }, [agentsWithRealTimeStatus]);

  // Filter agents
  const filteredAgents = useMemo(() => {
    return agentsWithRealTimeStatus.filter((agent) => {
      // Department filter - check if agent belongs to selected department
      if (selectedDepartment) {
        const agentDepts = agent.departments || [agent.department || "General"];
        if (!agentDepts.includes(selectedDepartment)) {
          return false;
        }
      }

      // Search filter
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const agentDepts = agent.departments || [agent.department];
        const deptString = agentDepts.join(" ");

        return (
          agent.name?.toLowerCase().includes(query) ||
          agent.role?.toLowerCase().includes(query) ||
          agent.agent_id?.toLowerCase().includes(query) ||
          deptString.toLowerCase().includes(query)
        );
      }

      return true;
    });
  }, [agentsWithRealTimeStatus, searchQuery, selectedDepartment]);

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </DashboardLayout>
    );
  }

  const availableAgents = filteredAgents.filter(a => a.availability === Availability.AVAILABLE);
  const busyAgents = filteredAgents.filter(a => a.availability === Availability.BUSY);
  const totalTasks = agents?.reduce((sum, a) => sum + (a.tasks_completed || 0), 0) || 0;
  const totalAgents = agentsWithRealTimeStatus.length;

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Agents</h1>
          <p className="text-muted-foreground">
            Monitor the status and performance of all AI agents
          </p>
        </div>

        {/* Stats */}
        <div className="grid gap-4 md:grid-cols-4">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Agents
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{totalAgents}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Available
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{availableAgents.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Busy
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-yellow-600">{busyAgents.length}</div>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Departments
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{departments.length}</div>
            </CardContent>
          </Card>
        </div>

        {/* Search and Filter */}
        <div className="space-y-4">
          <div className="flex gap-3">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search agents by name, role, or department..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="pl-10"
              />
            </div>
          </div>

          {departments.length > 1 && (
            <div className="flex flex-wrap gap-2">
              <Button
                variant={selectedDepartment === null ? "default" : "outline"}
                size="sm"
                onClick={() => setSelectedDepartment(null)}
                className="rounded-full"
              >
                All Departments
              </Button>
              {departments.map((dept) => (
                <Button
                  key={dept}
                  variant={selectedDepartment === dept ? "default" : "outline"}
                  size="sm"
                  onClick={() => setSelectedDepartment(dept)}
                  className="rounded-full capitalize"
                >
                  {dept}
                </Button>
              ))}
            </div>
          )}
        </div>

        {/* Agents Grid */}
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {filteredAgents?.map((agent) => {
            const role = agent.role || "Unknown Role";
            const description = agent.description || `Specialized agent working on ${agent.department || 'projects'}`;

            return (
              <Link key={agent.agent_id} href={`/agents/${agent.agent_id}`}>
                <Card className="overflow-hidden hover:shadow-lg transition-shadow cursor-pointer group">
                  <CardHeader className="pb-3">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-3">
                        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/10 group-hover:bg-primary/20 transition-colors">
                          <Users className="h-6 w-6 text-primary" />
                        </div>
                        <div>
                          <CardTitle className="text-lg group-hover:text-primary transition-colors">
                            {agent.name || agent.agent_id}
                          </CardTitle>
                          <CardDescription className="text-xs">{role}</CardDescription>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className={`h-3 w-3 rounded-full ${
                          agent.availability === Availability.AVAILABLE ? 'bg-green-500' :
                          agent.availability === Availability.BUSY ? 'bg-yellow-500 animate-pulse' :
                          'bg-gray-500'
                        }`} />
                        <ArrowRight className="h-4 w-4 opacity-0 group-hover:opacity-100 transition-opacity" />
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-muted-foreground">
                      {description}
                    </p>

                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Status</span>
                        <Badge variant={getAvailabilityColor(agent.availability)}>
                          {agent.availability}
                        </Badge>
                      </div>

                      <div className="flex items-center justify-between text-sm">
                        <span className="text-muted-foreground">Tasks Completed</span>
                        <span className="font-medium flex items-center">
                          <CheckCircle2 className="mr-1 h-4 w-4 text-green-500" />
                          {agent.tasks_completed}
                        </span>
                      </div>

                      {agent.current_task_id && (
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-muted-foreground">Current Task</span>
                          <span className="font-medium flex items-center">
                            <Activity className="mr-1 h-4 w-4 text-blue-500 animate-pulse" />
                            Working
                          </span>
                        </div>
                      )}

                      {/* <div className="pt-2 border-t">
                        <div className="flex items-center text-xs text-muted-foreground">
                          <Clock className="mr-1 h-3 w-3" />
                          Last active {formatRelativeTime(agent.last_active)}
                        </div>
                        <div className="flex items-center text-xs text-muted-foreground mt-1">
                          <Activity className="mr-1 h-3 w-3" />
                          Last check {formatRelativeTime(agent.last_check)}
                        </div>
                      </div> */}
                    </div>
                  </CardContent>
                </Card>
              </Link>
            );
          })}
        </div>
      </div>
    </DashboardLayout>
  );
}
