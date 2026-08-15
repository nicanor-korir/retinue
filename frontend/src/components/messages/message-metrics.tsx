"use client";

import { Message, MessageType, Priority } from "@/types/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  MessageSquare,
  AlertCircle,
  CheckCircle2,
  Clock,
  TrendingUp,
  Users,
  Bell,
  Info,
} from "lucide-react";
import { useMemo } from "react";

interface MessageMetricsProps {
  messages: Message[];
}

export function MessageMetrics({ messages }: MessageMetricsProps) {
  const metrics = useMemo(() => {
    const total = messages.length;
    const unread = messages.filter((m) => !m.read).length;
    const critical = messages.filter((m) => m.priority === Priority.CRITICAL).length;
    const requiresAction = messages.filter(
      (m) => m.message_type === MessageType.APPROVAL || m.message_type === MessageType.ALERT
    ).length;

    // Type distribution
    const byType = {
      [MessageType.INFO]: messages.filter((m) => m.message_type === MessageType.INFO).length,
      [MessageType.TASK_ASSIGNMENT]: messages.filter(
        (m) => m.message_type === MessageType.TASK_ASSIGNMENT
      ).length,
      [MessageType.APPROVAL]: messages.filter((m) => m.message_type === MessageType.APPROVAL)
        .length,
      [MessageType.ALERT]: messages.filter((m) => m.message_type === MessageType.ALERT).length,
      [MessageType.STATUS_UPDATE]: messages.filter(
        (m) => m.message_type === MessageType.STATUS_UPDATE
      ).length,
    };

    // Priority distribution
    const byPriority = {
      [Priority.CRITICAL]: messages.filter((m) => m.priority === Priority.CRITICAL).length,
      [Priority.HIGH]: messages.filter((m) => m.priority === Priority.HIGH).length,
      [Priority.MEDIUM]: messages.filter((m) => m.priority === Priority.MEDIUM).length,
      [Priority.LOW]: messages.filter((m) => m.priority === Priority.LOW).length,
    };

    // Agent stats
    const uniqueAgents = new Set([
      ...messages.map((m) => m.from_agent_id),
      ...messages.map((m) => m.to_agent_id),
    ]);

    // Calculate today's messages
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const todayMessages = messages.filter(
      (m) => new Date(m.created_at) >= today
    ).length;

    // Calculate response rate (read messages)
    const readRate = total > 0 ? Math.round(((total - unread) / total) * 100) : 0;

    return {
      total,
      unread,
      critical,
      requiresAction,
      byType,
      byPriority,
      uniqueAgents: uniqueAgents.size,
      todayMessages,
      readRate,
    };
  }, [messages]);

  const statCards = [
    {
      title: "Total Messages",
      value: metrics.total,
      icon: MessageSquare,
      color: "text-blue-600",
      bgColor: "bg-blue-500/10",
      description: `${metrics.todayMessages} today`,
    },
    {
      title: "Unread",
      value: metrics.unread,
      icon: Bell,
      color: "text-yellow-600",
      bgColor: "bg-yellow-500/10",
      description: `${metrics.readRate}% read rate`,
    },
    {
      title: "Critical Priority",
      value: metrics.critical,
      icon: AlertCircle,
      color: "text-red-600",
      bgColor: "bg-red-500/10",
      description: "Requires immediate attention",
    },
    {
      title: "Requires Action",
      value: metrics.requiresAction,
      icon: CheckCircle2,
      color: "text-orange-600",
      bgColor: "bg-orange-500/10",
      description: "Approvals & alerts",
    },
    {
      title: "Active Agents",
      value: metrics.uniqueAgents,
      icon: Users,
      color: "text-purple-600",
      bgColor: "bg-purple-500/10",
      description: "Communicating agents",
    },
  ];

  return (
    <div className="space-y-6">
      {/* Main Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-5">
        {statCards.map((stat) => (
          <Card key={stat.title} className="relative overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.title}
              </CardTitle>
              <div className={`${stat.bgColor} p-2 rounded-lg`}>
                <stat.icon className={`h-4 w-4 ${stat.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-muted-foreground mt-1">{stat.description}</p>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Distribution Charts */}
      <div className="grid gap-4 md:grid-cols-2">
        {/* By Type */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <Info className="h-4 w-4" />
              By Message Type
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(metrics.byType).map(([type, count]) => {
              const percentage = metrics.total > 0 ? (count / metrics.total) * 100 : 0;
              return (
                <div key={type} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="capitalize">{type.replace("_", " ")}</span>
                    <span className="font-medium">{count}</span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div
                      className="bg-primary h-2 rounded-full transition-all duration-300"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>

        {/* By Priority */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold flex items-center gap-2">
              <TrendingUp className="h-4 w-4" />
              By Priority Level
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {Object.entries(metrics.byPriority).map(([priority, count]) => {
              const percentage = metrics.total > 0 ? (count / metrics.total) * 100 : 0;
              let barColor = "bg-primary";
              if (priority === Priority.CRITICAL) barColor = "bg-red-500";
              else if (priority === Priority.HIGH) barColor = "bg-orange-500";
              else if (priority === Priority.MEDIUM) barColor = "bg-blue-500";
              else barColor = "bg-gray-400";

              return (
                <div key={priority} className="space-y-1">
                  <div className="flex items-center justify-between text-sm">
                    <span className="capitalize">{priority}</span>
                    <span className="font-medium">{count}</span>
                  </div>
                  <div className="w-full bg-secondary rounded-full h-2">
                    <div
                      className={`${barColor} h-2 rounded-full transition-all duration-300`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
