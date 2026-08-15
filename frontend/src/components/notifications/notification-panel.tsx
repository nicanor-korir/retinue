"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  Bell,
  CheckCheck,
  Trash2,
  AlertCircle,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Users,
  MessageSquare
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from "@/components/ui/badge";
import {
  useNotifications,
  useMarkNotificationRead,
  useMarkAllNotificationsRead,
  useDeleteNotification,
} from "@/hooks/useApi";
import { Notification, NotificationType } from "@/types/api";
import { formatRelativeTime } from "@/lib/utils";
import { cn } from "@/lib/utils";

interface NotificationPanelProps {
  onClose: () => void;
}

function getNotificationIcon(type: NotificationType) {
  switch (type) {
    case NotificationType.CEO_FEEDBACK:
      return <MessageSquare className="h-4 w-4 text-blue-500" />;
    case NotificationType.PROJECT_COMPLETED:
      return <CheckCircle className="h-4 w-4 text-green-500" />;
    case NotificationType.PROJECT_FAILED:
      return <XCircle className="h-4 w-4 text-red-500" />;
    case NotificationType.TASK_BLOCKED:
      return <AlertTriangle className="h-4 w-4 text-yellow-500" />;
    case NotificationType.HUMAN_INTERVENTION_REQUIRED:
      return <Users className="h-4 w-4 text-purple-500" />;
    case NotificationType.ESCALATION:
      return <AlertCircle className="h-4 w-4 text-orange-500" />;
    default:
      return <Bell className="h-4 w-4 text-gray-500" />;
  }
}

function getNotificationColor(type: NotificationType): string {
  switch (type) {
    case NotificationType.CEO_FEEDBACK:
      return "bg-blue-50 hover:bg-blue-100 border-blue-200";
    case NotificationType.PROJECT_COMPLETED:
      return "bg-green-50 hover:bg-green-100 border-green-200";
    case NotificationType.PROJECT_FAILED:
      return "bg-red-50 hover:bg-red-100 border-red-200";
    case NotificationType.TASK_BLOCKED:
      return "bg-yellow-50 hover:bg-yellow-100 border-yellow-200";
    case NotificationType.HUMAN_INTERVENTION_REQUIRED:
      return "bg-purple-50 hover:bg-purple-100 border-purple-200";
    case NotificationType.ESCALATION:
      return "bg-orange-50 hover:bg-orange-100 border-orange-200";
    default:
      return "bg-gray-50 hover:bg-gray-100 border-gray-200";
  }
}

function NotificationItem({
  notification,
  onMarkRead,
  onDelete,
  onNavigate
}: {
  notification: Notification;
  onMarkRead: (id: string) => void;
  onDelete: (id: string) => void;
  onNavigate: (notification: Notification) => void;
}) {
  const colorClass = getNotificationColor(notification.type as NotificationType);

  return (
    <div
      className={cn(
        "p-4 border-b transition-colors cursor-pointer",
        !notification.read ? colorClass : "hover:bg-gray-50",
        !notification.read && "border-l-4"
      )}
      onClick={() => onNavigate(notification)}
    >
      <div className="flex items-start gap-3">
        <div className="mt-1">
          {getNotificationIcon(notification.type as NotificationType)}
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-start justify-between gap-2 mb-1">
            <h4 className={cn(
              "text-sm font-medium line-clamp-1",
              !notification.read && "font-semibold"
            )}>
              {notification.title}
            </h4>
            {!notification.read && (
              <div className="h-2 w-2 bg-blue-600 rounded-full flex-shrink-0 mt-1" />
            )}
          </div>
          <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
            {notification.message}
          </p>
          <div className="flex items-center justify-between">
            <span className="text-xs text-muted-foreground">
              {formatRelativeTime(notification.created_at)}
              {notification.agent_name && ` • ${notification.agent_name}`}
            </span>
            <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
              {!notification.read && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 px-2"
                  onClick={() => onMarkRead(notification.notification_id)}
                >
                  <CheckCheck className="h-3 w-3" />
                </Button>
              )}
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2 text-red-600 hover:text-red-700 hover:bg-red-50"
                onClick={() => onDelete(notification.notification_id)}
              >
                <Trash2 className="h-3 w-3" />
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function NotificationPanel({ onClose }: NotificationPanelProps) {
  const router = useRouter();
  const [activeTab, setActiveTab] = useState("all");

  const { data: allNotifications, isLoading: isLoadingAll } = useNotifications(false);
  const { data: unreadNotifications, isLoading: isLoadingUnread } = useNotifications(true);

  const markRead = useMarkNotificationRead();
  const markAllRead = useMarkAllNotificationsRead();
  const deleteNotification = useDeleteNotification();

  const handleMarkRead = (id: string) => {
    markRead.mutate(id);
  };

  const handleMarkAllRead = () => {
    markAllRead.mutate();
  };

  const handleDelete = (id: string) => {
    deleteNotification.mutate(id);
  };

  const handleNavigate = (notification: Notification) => {
    // Mark as read
    if (!notification.read) {
      markRead.mutate(notification.notification_id);
    }

    // Navigate based on related entity
    if (notification.related_entity_type === "project" && notification.related_entity_id) {
      router.push(`/projects/${notification.related_entity_id}`);
      onClose();
    } else if (notification.related_entity_type === "task" && notification.related_entity_id) {
      router.push(`/tasks/${notification.related_entity_id}`);
      onClose();
    } else if (notification.related_entity_type === "agent" && notification.agent_id) {
      router.push(`/agents/${notification.agent_id}`);
      onClose();
    }
  };

  const notifications = activeTab === "unread" ? unreadNotifications : allNotifications;
  const isLoading = activeTab === "unread" ? isLoadingUnread : isLoadingAll;

  return (
    <div className="flex flex-col h-[500px]">
      {/* Header */}
      <div className="p-4 border-b">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-lg font-semibold">Notifications</h3>
          {unreadNotifications && unreadNotifications.length > 0 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={handleMarkAllRead}
              disabled={markAllRead.isPending}
            >
              <CheckCheck className="h-4 w-4 mr-1" />
              Mark all read
            </Button>
          )}
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="all">
              All
              {allNotifications && (
                <Badge variant="secondary" className="ml-2">
                  {allNotifications.length}
                </Badge>
              )}
            </TabsTrigger>
            <TabsTrigger value="unread">
              Unread
              {unreadNotifications && unreadNotifications.length > 0 && (
                <Badge variant="destructive" className="ml-2">
                  {unreadNotifications.length}
                </Badge>
              )}
            </TabsTrigger>
          </TabsList>
        </Tabs>
      </div>

      {/* Notifications List */}
      <ScrollArea className="flex-1">
        {isLoading ? (
          <div className="flex items-center justify-center h-32">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          </div>
        ) : notifications && notifications.length > 0 ? (
          <div>
            {notifications.map((notification) => (
              <NotificationItem
                key={notification.notification_id}
                notification={notification}
                onMarkRead={handleMarkRead}
                onDelete={handleDelete}
                onNavigate={handleNavigate}
              />
            ))}
          </div>
        ) : (
          <div className="flex flex-col items-center justify-center h-32 text-center p-4">
            <Bell className="h-12 w-12 text-muted-foreground mb-2 opacity-50" />
            <p className="text-sm text-muted-foreground">
              {activeTab === "unread"
                ? "No unread notifications"
                : "No notifications yet"}
            </p>
          </div>
        )}
      </ScrollArea>
    </div>
  );
}
