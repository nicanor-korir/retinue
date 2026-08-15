/**
 * UserActivityProfile - Displays user activity patterns and preferences
 * Phase 2: Frontend Integration
 */

import React, { useState } from "react";
import {
  User,
  Activity,
  TrendingUp,
  Clock,
  FolderKanban,
  Users,
  MessageSquare,
  Calendar,
  BarChart3,
  RefreshCw,
  Loader2,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import { useUserActivityProfile } from "@/hooks/useContextIntelligence";
import { cn } from "@/lib/utils";

interface UserActivityProfileProps {
  userId: string;
  days?: number;
  className?: string;
  showHeader?: boolean;
  collapsible?: boolean;
}

export function UserActivityProfile({
  userId,
  days = 30,
  className,
  showHeader = true,
  collapsible = true,
}: UserActivityProfileProps) {
  const { profile, loading, error, refetch } = useUserActivityProfile(userId, days);
  const [collapsed, setCollapsed] = useState(false);

  if (error) {
    return (
      <div className={cn("p-4 border rounded-lg bg-red-50 border-red-200", className)}>
        <p className="text-sm text-red-600">Failed to load user activity profile</p>
      </div>
    );
  }

  if (loading && !profile) {
    return (
      <div className={cn("p-4 border rounded-lg bg-gray-50", className)}>
        <div className="flex items-center gap-2">
          <Loader2 className="w-4 h-4 animate-spin text-gray-400" />
          <span className="text-sm text-gray-600">Loading activity profile...</span>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className={cn("p-4 border rounded-lg bg-gray-50", className)}>
        <p className="text-sm text-gray-500">No activity data available</p>
      </div>
    );
  }

  return (
    <div className={cn("border rounded-lg bg-white shadow-sm", className)}>
      {/* Header */}
      {showHeader && (
        <div className="p-3 border-b bg-gradient-to-r from-purple-50 to-pink-50 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <User className="w-5 h-5 text-purple-600" />
            <h3 className="font-semibold text-gray-900">Activity Profile</h3>
            <span className="text-xs text-gray-500">Last {days} days</span>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={() => refetch()}
              className="p-1 hover:bg-white rounded transition-colors"
              title="Refresh profile"
            >
              <RefreshCw className={cn("w-4 h-4 text-gray-600", loading && "animate-spin")} />
            </button>

            {collapsible && (
              <button
                onClick={() => setCollapsed(!collapsed)}
                className="p-1 hover:bg-white rounded transition-colors"
              >
                {collapsed ? (
                  <ChevronDown className="w-4 h-4 text-gray-600" />
                ) : (
                  <ChevronUp className="w-4 h-4 text-gray-600" />
                )}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Content */}
      {!collapsed && (
        <div className="p-4 space-y-4">
          {/* Active Projects */}
          {profile.active_projects.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <FolderKanban className="w-4 h-4 text-blue-500" />
                <span className="text-sm font-medium text-gray-700">Active Projects</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {profile.active_projects.map((projectId) => (
                  <span
                    key={projectId}
                    className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-blue-50 text-blue-700 border border-blue-200"
                  >
                    {formatEntityId(projectId)}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Frequent Agents */}
          {profile.frequent_agents.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <Users className="w-4 h-4 text-purple-500" />
                <span className="text-sm font-medium text-gray-700">Frequent Agents</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {profile.frequent_agents.map((agentId) => (
                  <span
                    key={agentId}
                    className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-purple-50 text-purple-700 border border-purple-200"
                  >
                    {agentId}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Common Topics */}
          {profile.common_topics.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp className="w-4 h-4 text-green-500" />
                <span className="text-sm font-medium text-gray-700">Common Topics</span>
              </div>
              <div className="flex flex-wrap gap-2">
                {profile.common_topics.map((topic, idx) => (
                  <span
                    key={idx}
                    className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-green-50 text-green-700 border border-green-200"
                  >
                    {topic}
                  </span>
                ))}
              </div>
            </div>
          )}

          {/* Activity Summary */}
          {Object.keys(profile.activity_summary).length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <BarChart3 className="w-4 h-4 text-orange-500" />
                <span className="text-sm font-medium text-gray-700">Activity Summary</span>
              </div>
              <div className="space-y-1">
                {Object.entries(profile.activity_summary).map(([activity, count]) => (
                  <div key={activity} className="flex items-center justify-between text-xs">
                    <span className="text-gray-600">{formatActivityType(activity)}</span>
                    <span className="font-medium text-gray-900">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* User Preferences */}
          {profile.preferences && (
            <div className="pt-3 border-t">
              <div className="flex items-center gap-2 mb-2">
                <Activity className="w-4 h-4 text-cyan-500" />
                <span className="text-sm font-medium text-gray-700">Preferences</span>
              </div>
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-gray-600">Response Format</span>
                  <span className="font-medium text-gray-900 capitalize">
                    {profile.preferences.response_format}
                  </span>
                </div>
                {profile.preferences.preferred_agents.length > 0 && (
                  <div className="text-xs">
                    <span className="text-gray-600">Preferred Agents: </span>
                    <span className="font-medium text-gray-900">
                      {profile.preferences.preferred_agents.join(", ")}
                    </span>
                  </div>
                )}
                {profile.preferences.topics_of_interest.length > 0 && (
                  <div className="text-xs">
                    <span className="text-gray-600">Interests: </span>
                    <span className="font-medium text-gray-900">
                      {profile.preferences.topics_of_interest.join(", ")}
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Format entity ID for display
 */
function formatEntityId(id: string): string {
  // If it's a UUID, show shortened version
  if (id.length > 20 && id.includes("-")) {
    return id.substring(0, 8);
  }
  return id;
}

/**
 * Format activity type for display
 */
function formatActivityType(activity: string): string {
  return activity
    .split("_")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

/**
 * Compact version of user activity profile
 */
export function CompactUserActivityProfile({
  userId,
  days = 30,
  className,
}: {
  userId: string;
  days?: number;
  className?: string;
}) {
  const { profile, loading, error } = useUserActivityProfile(userId, days);

  if (loading || error || !profile) {
    return null;
  }

  const totalActivity = Object.values(profile.activity_summary).reduce(
    (sum, count) => sum + count,
    0
  );

  return (
    <div className={cn("flex items-center gap-2 text-xs text-gray-500", className)}>
      <Activity className="w-3 h-3" />
      <span>{totalActivity} activities</span>
      {profile.active_projects.length > 0 && (
        <>
          <span>•</span>
          <FolderKanban className="w-3 h-3" />
          <span>{profile.active_projects.length} projects</span>
        </>
      )}
    </div>
  );
}
