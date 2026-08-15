"use client";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { CheckCircle2, Clock, TrendingUp, Award } from "lucide-react";

export function ActivityStats() {
  return (
    <div className="space-y-6">
      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-6">Activity Overview</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[
            { label: "Tasks Completed", value: "47", icon: CheckCircle2, trend: "+12%" },
            { label: "Hours Logged", value: "156", icon: Clock, trend: "+8%" },
            { label: "Productivity", value: "98%", icon: TrendingUp, trend: "+5%" },
            { label: "Achievements", value: "23", icon: Award, trend: "+3" },
          ].map((stat, index) => {
            const Icon = stat.icon;
            return (
              <div key={index} className="p-4 border rounded-lg">
                <div className="flex items-center justify-between mb-2">
                  <Icon className="h-5 w-5 text-primary" />
                  <Badge variant="secondary">{stat.trend}</Badge>
                </div>
                <div className="text-2xl font-bold">{stat.value}</div>
                <div className="text-sm text-muted-foreground">{stat.label}</div>
              </div>
            );
          })}
        </div>
      </Card>

      <Card className="p-6">
        <h2 className="text-xl font-semibold mb-6">Recent Activity</h2>
        <div className="space-y-4">
          {[
            { action: "Completed task", detail: "Implement user authentication", time: "2 hours ago" },
            { action: "Joined project", detail: "Deviant Development", time: "5 hours ago" },
            { action: "Updated profile", detail: "Changed availability status", time: "1 day ago" },
            { action: "Commented on task", detail: "Database optimization", time: "2 days ago" },
          ].map((activity, index) => (
            <div key={index} className="flex items-start gap-3 p-3 border rounded-lg">
              <div className="h-2 w-2 rounded-full bg-primary mt-2"></div>
              <div className="flex-1">
                <div className="font-medium">{activity.action}</div>
                <div className="text-sm text-muted-foreground">{activity.detail}</div>
              </div>
              <div className="text-xs text-muted-foreground">{activity.time}</div>
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}
