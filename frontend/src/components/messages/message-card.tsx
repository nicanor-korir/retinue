"use client";

import { Message, MessageType, Priority } from "@/types/api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  ArrowRight,
  Eye,
  MoreVertical,
  User,
  Clock,
  AlertCircle,
  CheckCircle2,
  Info,
  Bell,
} from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";
import { useState } from "react";

interface MessageCardProps {
  message: Message;
  onClick: () => void;
  onMarkAsRead?: (messageId: string) => void;
}

function getMessageTypeColor(type: MessageType): string {
  switch (type) {
    case MessageType.APPROVAL:
      return "border-yellow-500/50 bg-yellow-500/5 hover:bg-yellow-500/10";
    case MessageType.ALERT:
      return "border-red-500/50 bg-red-500/5 hover:bg-red-500/10";
    case MessageType.TASK_ASSIGNMENT:
      return "border-blue-500/50 bg-blue-500/5 hover:bg-blue-500/10";
    case MessageType.STATUS_UPDATE:
      return "border-green-500/50 bg-green-500/5 hover:bg-green-500/10";
    default:
      return "border-border hover:bg-accent/50";
  }
}

function getPriorityBadgeVariant(priority: Priority) {
  switch (priority) {
    case Priority.CRITICAL:
      return "destructive";
    case Priority.HIGH:
      return "default";
    case Priority.MEDIUM:
      return "secondary";
    default:
      return "outline";
  }
}

function getMessageTypeIcon(type: MessageType) {
  switch (type) {
    case MessageType.ALERT:
      return <AlertCircle className="h-4 w-4" />;
    case MessageType.APPROVAL:
      return <CheckCircle2 className="h-4 w-4" />;
    case MessageType.STATUS_UPDATE:
      return <Info className="h-4 w-4" />;
    case MessageType.TASK_ASSIGNMENT:
      return <Bell className="h-4 w-4" />;
    default:
      return <Info className="h-4 w-4" />;
  }
}

export function MessageCard({ message, onClick, onMarkAsRead }: MessageCardProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const isLongMessage = message.content.length > 150;
  const displayContent = isExpanded || !isLongMessage 
    ? message.content 
    : message.content.slice(0, 150) + "...";

  const handleCardClick = (e: React.MouseEvent) => {
    // Don't trigger if clicking on buttons or interactive elements
    if ((e.target as HTMLElement).closest('button')) {
      return;
    }
    onClick();
  };

  return (
    <Card
      className={`transition-all duration-200 cursor-pointer border-l-4 ${
        getMessageTypeColor(message.message_type)
      } ${!message.read ? "shadow-md" : "shadow-sm"}`}
      onClick={handleCardClick}
    >
      <CardContent className="p-4">
        <div className="space-y-3">
          {/* Header Row */}
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3 flex-1 min-w-0">
              {/* Agent Avatar/Icon */}
              <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                <User className="h-5 w-5 text-primary" />
              </div>

              {/* From/To Info */}
              <div className="flex items-center gap-2 text-sm min-w-0 flex-1">
                <span className="font-semibold truncate">{message.from_agent_id}</span>
                <ArrowRight className="h-4 w-4 text-muted-foreground flex-shrink-0" />
                <span className="text-muted-foreground truncate">{message.to_agent_id}</span>
              </div>
            </div>

            {/* Badges */}
            <div className="flex items-center gap-2 flex-shrink-0">
              {!message.read && (
                <div className="h-2 w-2 rounded-full bg-blue-500 animate-pulse" />
              )}
              <Badge variant={getPriorityBadgeVariant(message.priority)} className="text-xs">
                {message.priority}
              </Badge>
            </div>
          </div>

          {/* Message Type Badge */}
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {getMessageTypeIcon(message.message_type)}
              <span className="ml-1.5 capitalize">
                {message.message_type.replace("_", " ")}
              </span>
            </Badge>
          </div>

          {/* Message Content */}
          <div className="pl-[52px]">
            <p className="text-sm leading-relaxed text-foreground/90 whitespace-pre-wrap break-words">
              {displayContent}
            </p>
            {isLongMessage && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  setIsExpanded(!isExpanded);
                }}
                className="text-xs text-primary hover:underline mt-1 font-medium"
              >
                {isExpanded ? "Show less" : "Show more"}
              </button>
            )}
          </div>

          {/* Metadata Preview */}
          {message.metadata && Object.keys(message.metadata).length > 0 && (
            <div className="pl-[52px]">
              <div className="text-xs text-muted-foreground">
                {Object.keys(message.metadata).length} metadata field(s)
              </div>
            </div>
          )}

          {/* Footer Row */}
          <div className="flex items-center justify-between pt-2 border-t">
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Clock className="h-3 w-3" />
              <span>{formatRelativeTime(message.created_at)}</span>
            </div>

            <div className="flex items-center gap-2">
              {!message.read && onMarkAsRead && (
                <Button
                  variant="ghost"
                  size="sm"
                  className="h-7 text-xs"
                  onClick={(e) => {
                    e.stopPropagation();
                    onMarkAsRead(message.message_id);
                  }}
                >
                  <Eye className="h-3 w-3 mr-1" />
                  Mark as read
                </Button>
              )}
              <Button
                variant="ghost"
                size="sm"
                className="h-7 px-2"
                onClick={(e) => {
                  e.stopPropagation();
                  onClick();
                }}
              >
                <MoreVertical className="h-4 w-4" />
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
