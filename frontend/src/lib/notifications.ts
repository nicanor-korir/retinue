/**
 * Browser Notifications Utility
 * Handles Web Notification API interactions and shows various notification types
 */

interface NotificationOptions {
  title: string;
  body: string;
  tag?: string;
  icon?: string;
  badge?: string;
  data?: Record<string, any>;
  requireInteraction?: boolean;
}

class BrowserNotificationsManager {
  /**
   * Check if the browser supports Web Notifications API
   */
  isSupported(): boolean {
    return typeof window !== "undefined" && "Notification" in window;
  }

  /**
   * Get current notification permission status
   */
  getPermissionStatus(): NotificationPermission {
    if (!this.isSupported()) {
      return "denied";
    }
    return Notification.permission;
  }

  /**
   * Request permission to show notifications
   */
  async requestPermission(): Promise<NotificationPermission> {
    if (!this.isSupported()) {
      return "denied";
    }

    const permission = await Notification.requestPermission();
    return permission;
  }

  /**
   * Show a generic notification
   */
  show(options: NotificationOptions): void {
    if (!this.isSupported() || this.getPermissionStatus() !== "granted") {
      return;
    }

    try {
      new Notification(options.title, {
        body: options.body,
        tag: options.tag || "default",
        icon: options.icon || "/icon-192x192.png",
        badge: options.badge || "/badge-72x72.png",
        data: options.data || {},
        requireInteraction: options.requireInteraction || false,
      });
    } catch (error) {
      console.error("Failed to show notification:", error);
    }
  }

  /**
   * Notify about human intervention required
   */
  notifyHumanInterventionRequired(title: string, message: string, entityId: string): void {
    this.show({
      title: title || "Human Intervention Required",
      body: message,
      tag: `intervention-${entityId}`,
      icon: "/icon-192x192.png",
      data: {
        type: "human_intervention_required",
        entityId,
        url: `/tasks/${entityId}`,
      },
      requireInteraction: true,
    });
  }

  /**
   * Notify about CEO feedback
   */
  notifyCEOFeedback(title: string, message: string, entityId: string): void {
    this.show({
      title: title || "CEO Feedback",
      body: message,
      tag: `feedback-${entityId}`,
      icon: "/icon-192x192.png",
      data: {
        type: "ceo_feedback",
        entityId,
        url: `/projects/${entityId}`,
      },
      requireInteraction: true,
    });
  }

  /**
   * Notify about project completion
   */
  notifyProjectCompleted(title: string, projectId: string): void {
    this.show({
      title: title || "Project Completed",
      body: "Congratulations! Your project has been completed successfully.",
      tag: `project-completed-${projectId}`,
      icon: "/icon-192x192.png",
      data: {
        type: "project_completed",
        projectId,
        url: `/projects/${projectId}`,
      },
    });
  }

  /**
   * Notify about project failure
   */
  notifyProjectFailed(title: string, message: string, projectId: string): void {
    this.show({
      title: title || "Project Failed",
      body: message,
      tag: `project-failed-${projectId}`,
      icon: "/icon-192x192.png",
      data: {
        type: "project_failed",
        projectId,
        url: `/projects/${projectId}`,
      },
      requireInteraction: true,
    });
  }

  /**
   * Notify about task updates
   */
  notifyTaskUpdate(
    title: string,
    message: string,
    taskId: string,
    priority?: string
  ): void {
    const isHighPriority = priority === "high" || priority === "critical";
    this.show({
      title: title || "Task Update",
      body: message,
      tag: `task-${taskId}`,
      icon: "/icon-192x192.png",
      data: {
        type: "task_update",
        taskId,
        priority,
        url: `/tasks/${taskId}`,
      },
      requireInteraction: isHighPriority,
    });
  }

  /**
   * Notify about escalation
   */
  notifyEscalation(title: string, message: string, entityId: string): void {
    this.show({
      title: title || "Escalation Alert",
      body: message,
      tag: `escalation-${entityId}`,
      icon: "/icon-192x192.png",
      data: {
        type: "escalation",
        entityId,
        url: `/escalations`,
      },
      requireInteraction: true,
    });
  }
}

/**
 * Global instance of the notifications manager
 */
export const browserNotifications = new BrowserNotificationsManager();

/**
 * Determine if a browser notification should be shown
 * Returns true if the user is on a different tab or window is not in focus
 */
export function shouldShowBrowserNotification(): boolean {
  if (typeof document === "undefined") {
    return false;
  }

  // Check if document is hidden (user is on another tab)
  return document.hidden === true;
}
