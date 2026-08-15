"use client";

import { useEffect, useState, useCallback } from "react";
import { browserNotifications, shouldShowBrowserNotification } from "@/lib/notifications";
import { useNotifications } from "@/hooks/useApi";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Bell, X } from "lucide-react";
import { Priority, type Notification } from "@/types/api";

/**
 * NotificationProvider Component
 * Manages browser notification permissions and displays notifications
 * when user is on another tab or app
 */
export function NotificationProvider({ children }: { children: React.ReactNode }) {
  const [permissionStatus, setPermissionStatus] = useState<NotificationPermission>("default");
  const [showPermissionPrompt, setShowPermissionPrompt] = useState(false);
  const [hasRequestedPermission, setHasRequestedPermission] = useState(false);
  const [lastNotificationId, setLastNotificationId] = useState<string | null>(null);

  // Fetch unread notifications
  const { data: notifications } = useNotifications(true);

  // Check if we've already requested permission (stored in localStorage)
  useEffect(() => {
    if (typeof window !== "undefined") {
      const requested = localStorage.getItem("notification-permission-requested");
      setHasRequestedPermission(requested === "true");

      // Get current permission status
      if (browserNotifications.isSupported()) {
        setPermissionStatus(browserNotifications.getPermissionStatus());
      }
    }
  }, []);

  // Show permission prompt after 3 seconds if not yet requested
  useEffect(() => {
    if (
      !hasRequestedPermission &&
      permissionStatus === "default" &&
      browserNotifications.isSupported()
    ) {
      const timer = setTimeout(() => {
        setShowPermissionPrompt(true);
      }, 3000); // Show prompt after 3 seconds

      return () => clearTimeout(timer);
    }
  }, [hasRequestedPermission, permissionStatus]);

  // Handle request permission
  const handleRequestPermission = useCallback(async () => {
    const status = await browserNotifications.requestPermission();
    setPermissionStatus(status);
    setShowPermissionPrompt(false);
    setHasRequestedPermission(true);
    localStorage.setItem("notification-permission-requested", "true");
  }, []);

  // Handle dismiss permission prompt
  const handleDismissPrompt = useCallback(() => {
    setShowPermissionPrompt(false);
    setHasRequestedPermission(true);
    localStorage.setItem("notification-permission-requested", "true");
  }, []);

  // Monitor notifications and show browser notifications
  useEffect(() => {
    if (!notifications || notifications.length === 0) return;
    if (permissionStatus !== "granted") return;

    // Get the most recent notification
    const latestNotification = notifications[0];

    // Skip if we've already shown this notification
    if (latestNotification.notification_id === lastNotificationId) return;

    // Only show browser notification if user is on another tab/app
    if (shouldShowBrowserNotification()) {
      showBrowserNotification(latestNotification);
    }

    // Update last notification ID
    setLastNotificationId(latestNotification.notification_id);
  }, [notifications, permissionStatus, lastNotificationId]);

  // Show appropriate browser notification based on type
  const showBrowserNotification = useCallback((notification: Notification) => {
    const { type, title, message, related_entity_id, priority } = notification;

    switch (type) {
      case "human_intervention_required":
        browserNotifications.notifyHumanInterventionRequired(
          title,
          message,
          related_entity_id || ""
        );
        break;

      case "ceo_feedback":
        browserNotifications.notifyCEOFeedback(
          title,
          message,
          related_entity_id || ""
        );
        break;

      case "project_completed":
        browserNotifications.notifyProjectCompleted(
          title,
          related_entity_id || ""
        );
        break;

      case "project_failed":
        browserNotifications.notifyProjectFailed(
          title,
          message,
          related_entity_id || ""
        );
        break;

      case "task_blocked":
        browserNotifications.notifyTaskUpdate(
          title,
          message,
          related_entity_id || "",
          priority?.toLowerCase()
        );
        break;

      case "escalation":
        browserNotifications.notifyEscalation(
          title,
          message,
          related_entity_id || ""
        );
        break;

      case "general":
      default:
        browserNotifications.show({
          title,
          body: message,
          tag: `notification-${notification.notification_id}`,
          data: {
            url: "/",
            type: type,
            notificationId: notification.notification_id,
          },
          requireInteraction: priority === Priority.HIGH || priority === Priority.CRITICAL,
        });
        break;
    }
  }, []);

  return (
    <>
      {children}

      {/* Permission Request Prompt */}
      {showPermissionPrompt && permissionStatus === "default" && (
        <div className="fixed bottom-4 right-4 z-50 animate-in slide-in-from-bottom-5">
          <Card className="w-[400px] shadow-lg border-2 border-primary/20">
            <CardHeader className="pb-3">
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <Bell className="h-5 w-5 text-primary" />
                  <CardTitle className="text-lg">Enable Notifications</CardTitle>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-6 w-6 -mr-2 -mt-2"
                  onClick={handleDismissPrompt}
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>
              <CardDescription className="text-sm">
                Stay updated with project progress, agent activities, and important alerts
                even when you're on another tab or app.
              </CardDescription>
            </CardHeader>
            <CardContent className="flex gap-2">
              <Button
                onClick={handleRequestPermission}
                className="flex-1"
                size="sm"
              >
                Enable Notifications
              </Button>
              <Button
                variant="outline"
                onClick={handleDismissPrompt}
                className="flex-1"
                size="sm"
              >
                Maybe Later
              </Button>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Permission Denied Info (optional) */}
      {permissionStatus === "denied" && hasRequestedPermission && (
        <div className="fixed bottom-4 right-4 z-50">
          {/* Could add a small info banner here if needed */}
        </div>
      )}
    </>
  );
}
