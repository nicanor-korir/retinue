"use client";

import { useState, useEffect } from "react";
import { ChatWidget } from "@/components/chat/ChatWidget";
import { useCreateOrGetTaskDiscussion } from "@/hooks/useApi";
import { ConversationType } from "@/types/conversation";
import { Loader2, MessageSquare, AlertCircle } from "lucide-react";

interface TaskChatPanelProps {
  taskId: string;
  taskTitle?: string;
}

export function TaskChatPanel({ taskId, taskTitle }: TaskChatPanelProps) {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const createOrGetDiscussion = useCreateOrGetTaskDiscussion();

  useEffect(() => {
    // Load or create task discussion
    const initializeChat = async () => {
      try {
        setError(null);
        const conversation = await createOrGetDiscussion.mutateAsync({
          taskId,
          userId: "user_1",
        });
        setConversationId(conversation.conversation_id);
      } catch (err: any) {
        console.error("Failed to initialize task chat:", err);
        setError(err?.message || "Failed to load task chat");
      }
    };

    initializeChat();
  }, [taskId]);

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-[600px] bg-card rounded-lg border border-destructive/20">
        <AlertCircle className="h-12 w-12 text-destructive mb-4" />
        <h3 className="text-lg font-semibold mb-2">Failed to Load Chat</h3>
        <p className="text-sm text-muted-foreground mb-4 text-center max-w-md">
          {error}
        </p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
        >
          Retry
        </button>
      </div>
    );
  }

  if (!conversationId) {
    return (
      <div className="flex flex-col items-center justify-center h-[600px] bg-card rounded-lg border">
        <Loader2 className="h-8 w-8 animate-spin text-primary mb-4" />
        <p className="text-sm text-muted-foreground">Loading task chat...</p>
      </div>
    );
  }

  return (
    <div className="h-[600px]">
      <ChatWidget
        conversationId={conversationId}
        conversationType={ConversationType.PROJECT_DISCUSSION}
        title={`${taskTitle ? `${taskTitle} - ` : ""}Task Chat`}
        showHistory={false}
      />
    </div>
  );
}
