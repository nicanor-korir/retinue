"use client";

import { Message } from "@/types/api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Textarea } from "@/components/ui/textarea";
import {
  X,
  Clock,
  User,
  AlertCircle,
  CheckCircle2,
  Link as LinkIcon,
  Tag,
  MessageSquare,
  Send,
  Archive,
  MoreVertical,
} from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";
import { MessageType, Priority } from "@/types/api";
import { useState } from "react";

interface MessageDetailPanelProps {
  message: Message;
  onClose: () => void;
  onMarkAsRead?: (messageId: string) => void;
  onMarkAsResolved?: (messageId: string) => void;
  onReply?: (messageId: string, content: string) => void;
}

function getMessageTypeColor(type: MessageType) {
  switch (type) {
    case MessageType.APPROVAL:
      return "bg-yellow-500/10 text-yellow-700 dark:text-yellow-400 border-yellow-500/20";
    case MessageType.ALERT:
      return "bg-red-500/10 text-red-700 dark:text-red-400 border-red-500/20";
    case MessageType.TASK_ASSIGNMENT:
      return "bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20";
    case MessageType.STATUS_UPDATE:
      return "bg-green-500/10 text-green-700 dark:text-green-400 border-green-500/20";
    default:
      return "bg-gray-500/10 text-gray-700 dark:text-gray-400 border-gray-500/20";
  }
}

function getPriorityColor(priority: Priority) {
  switch (priority) {
    case Priority.CRITICAL:
      return "bg-red-500/10 text-red-700 dark:text-red-400 border-red-500/20";
    case Priority.HIGH:
      return "bg-orange-500/10 text-orange-700 dark:text-orange-400 border-orange-500/20";
    case Priority.MEDIUM:
      return "bg-blue-500/10 text-blue-700 dark:text-blue-400 border-blue-500/20";
    default:
      return "bg-gray-500/10 text-gray-700 dark:text-gray-400 border-gray-500/20";
  }
}

function getMessageTypeIcon(type: MessageType) {
  switch (type) {
    case MessageType.ALERT:
      return <AlertCircle className="h-5 w-5" />;
    case MessageType.APPROVAL:
      return <CheckCircle2 className="h-5 w-5" />;
    case MessageType.TASK_ASSIGNMENT:
      return <LinkIcon className="h-5 w-5" />;
    default:
      return <MessageSquare className="h-5 w-5" />;
  }
}

export function MessageDetailPanel({
  message,
  onClose,
  onMarkAsRead,
  onMarkAsResolved,
  onReply,
}: MessageDetailPanelProps) {
  const [replyContent, setReplyContent] = useState("");
  const [isReplying, setIsReplying] = useState(false);

  const handleReply = () => {
    if (replyContent.trim() && onReply) {
      onReply(message.message_id, replyContent);
      setReplyContent("");
      setIsReplying(false);
    }
  };

  return (
    <div className="fixed inset-y-0 right-0 w-full md:w-[600px] bg-background border-l shadow-2xl z-50 overflow-y-auto">
      <div className="sticky top-0 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-b z-10">
        <div className="flex items-center justify-between p-4">
          <h2 className="text-lg font-semibold">Message Details</h2>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <X className="h-5 w-5" />
          </Button>
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Status Bar */}
        <div className="flex items-center gap-2 flex-wrap">
          <Badge className={`${getMessageTypeColor(message.message_type)} border`}>
            {getMessageTypeIcon(message.message_type)}
            <span className="ml-1.5">{message.message_type}</span>
          </Badge>
          <Badge className={`${getPriorityColor(message.priority)} border`}>
            {message.priority}
          </Badge>
          {!message.read && (
            <Badge variant="outline" className="bg-blue-500/10 border-blue-500/20">
              Unread
            </Badge>
          )}
        </div>

        {/* Participants */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <User className="h-4 w-4" />
              Participants
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">From</div>
                <div className="text-sm text-muted-foreground mt-0.5">
                  {message.from_agent_id}
                </div>
              </div>
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                <User className="h-4 w-4 text-primary" />
              </div>
            </div>
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm font-medium">To</div>
                <div className="text-sm text-muted-foreground mt-0.5">
                  {message.to_agent_id}
                </div>
              </div>
              <div className="h-8 w-8 rounded-full bg-primary/10 flex items-center justify-center">
                <User className="h-4 w-4 text-primary" />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Message Content */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <MessageSquare className="h-4 w-4" />
              Message Content
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <p className="text-sm leading-relaxed whitespace-pre-wrap">
                {message.content}
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Timestamp */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium flex items-center gap-2">
              <Clock className="h-4 w-4" />
              Timeline
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Sent</span>
              <span className="font-medium">{formatRelativeTime(message.created_at)}</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-muted-foreground">Status</span>
              <span className="font-medium">
                {message.read ? "Read" : "Unread"}
              </span>
            </div>
          </CardContent>
        </Card>

        {/* Metadata */}
        {message.metadata && Object.keys(message.metadata).length > 0 && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Tag className="h-4 w-4" />
                Metadata
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {Object.entries(message.metadata).map(([key, value]) => (
                  <div key={key} className="flex items-start gap-2">
                    <span className="text-xs font-medium text-muted-foreground min-w-[100px]">
                      {key}:
                    </span>
                    <span className="text-xs flex-1 break-words">
                      {typeof value === "object"
                        ? JSON.stringify(value, null, 2)
                        : String(value)}
                    </span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        )}

        {/* Quick Actions */}
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-medium">Quick Actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {!message.read && onMarkAsRead && (
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => onMarkAsRead(message.message_id)}
              >
                <CheckCircle2 className="h-4 w-4 mr-2" />
                Mark as Read
              </Button>
            )}
            {onMarkAsResolved && (
              <Button
                variant="outline"
                className="w-full justify-start"
                onClick={() => onMarkAsResolved(message.message_id)}
              >
                <Archive className="h-4 w-4 mr-2" />
                Mark as Resolved
              </Button>
            )}
            <Button
              variant="outline"
              className="w-full justify-start"
              onClick={() => setIsReplying(!isReplying)}
            >
              <Send className="h-4 w-4 mr-2" />
              Reply to Message
            </Button>
          </CardContent>
        </Card>

        {/* Reply Section */}
        {isReplying && (
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium">Reply</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Textarea
                placeholder="Type your reply..."
                value={replyContent}
                onChange={(e) => setReplyContent(e.target.value)}
                rows={4}
                className="resize-none"
              />
              <div className="flex gap-2">
                <Button
                  size="sm"
                  onClick={handleReply}
                  disabled={!replyContent.trim()}
                >
                  <Send className="h-4 w-4 mr-2" />
                  Send Reply
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    setIsReplying(false);
                    setReplyContent("");
                  }}
                >
                  Cancel
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
