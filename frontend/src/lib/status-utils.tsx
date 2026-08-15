import { CheckCircle2, Circle, AlertCircle, Clock, XCircle, Pause } from "lucide-react";
import { ProjectStatus, TaskStatus } from "@/types/api";

type BadgeVariant = "default" | "secondary" | "destructive" | "outline" | "success" | "warning" | "info";

/**
 * Get badge variant color for task status
 */
export function getTaskStatusColor(status: TaskStatus): BadgeVariant {
  switch (status) {
    case TaskStatus.COMPLETED:
      return "success";
    case TaskStatus.IN_PROGRESS:
      return "info";
    case TaskStatus.REVIEW:
      return "warning";
    case TaskStatus.BLOCKED:
      return "destructive";
    case TaskStatus.FAILED:
      return "destructive";
    case TaskStatus.CANCELLED:
      return "secondary";
    default:
      return "secondary";
  }
}

/**
 * Get icon component for task status
 */
export function getTaskStatusIcon(status: TaskStatus) {
  switch (status) {
    case TaskStatus.COMPLETED:
      return <CheckCircle2 className="h-5 w-5 text-green-500" />;
    case TaskStatus.IN_PROGRESS:
      return <Circle className="h-5 w-5 text-blue-500 animate-pulse" />;
    case TaskStatus.REVIEW:
      return <Clock className="h-5 w-5 text-yellow-500" />;
    case TaskStatus.BLOCKED:
      return <AlertCircle className="h-5 w-5 text-orange-500" />;
    case TaskStatus.FAILED:
      return <XCircle className="h-5 w-5 text-red-500" />;
    case TaskStatus.CANCELLED:
      return <XCircle className="h-5 w-5 text-gray-500" />;
    case TaskStatus.PENDING:
      return <Circle className="h-5 w-5 text-gray-400" />;
    default:
      return <Circle className="h-5 w-5 text-gray-400" />;
  }
}

/**
 * Get badge variant color for project status
 */
export function getProjectStatusColor(status: ProjectStatus): BadgeVariant {
  switch (status) {
    case ProjectStatus.COMPLETED:
      return "success";
    case ProjectStatus.IN_PROGRESS:
      return "info";
    case ProjectStatus.PLANNING:
      return "warning";
    case ProjectStatus.ON_HOLD:
      return "secondary";
    case ProjectStatus.CANCELLED:
      return "destructive";
    case ProjectStatus.FAILED:
      return "destructive";
    case ProjectStatus.REVIEW:
      return "info";
    default:
      return "default";
  }
}

/**
 * Get icon component for project status
 */
export function getProjectStatusIcon(status: ProjectStatus) {
  switch (status) {
    case ProjectStatus.COMPLETED:
      return <CheckCircle2 className="h-6 w-6 text-green-500" />;
    case ProjectStatus.IN_PROGRESS:
      return <Circle className="h-6 w-6 text-blue-500 animate-pulse" />;
    case ProjectStatus.REVIEW:
      return <Clock className="h-6 w-6 text-blue-500" />;
    case ProjectStatus.PLANNING:
      return <Circle className="h-6 w-6 text-yellow-500" />;
    case ProjectStatus.ON_HOLD:
      return <Pause className="h-6 w-6 text-gray-500" />;
    case ProjectStatus.CANCELLED:
      return <XCircle className="h-6 w-6 text-gray-500" />;
    case ProjectStatus.FAILED:
      return <AlertCircle className="h-6 w-6 text-red-500" />;
    default:
      return <Circle className="h-6 w-6 text-gray-400" />;
  }
}
