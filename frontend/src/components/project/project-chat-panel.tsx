"use client";

import { useState, useEffect } from "react";
import { ChatWidget } from "@/components/chat/ChatWidget";
import { useCreateOrGetProjectDiscussion } from "@/hooks/useApi";
import { ConversationType } from "@/types/conversation";
import { Loader2, MessageSquare, AlertCircle } from "lucide-react";

interface ProjectChatPanelProps {
  projectId: string;
  projectName?: string;
}

export function ProjectChatPanel({ projectId, projectName }: ProjectChatPanelProps) {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const createOrGetDiscussion = useCreateOrGetProjectDiscussion();

  useEffect(() => {
    // Load or create project discussion
    const initializeChat = async () => {
      try {
        setError(null);
        const conversation = await createOrGetDiscussion.mutateAsync({
          projectId,
          userId: "user_1",
        });
        setConversationId(conversation.conversation_id);
      } catch (err: any) {
        console.error("Failed to initialize project chat:", err);
        setError(err?.message || "Failed to load project chat");
      }
    };

    initializeChat();
  }, [projectId]);

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
        <p className="text-sm text-muted-foreground">Loading project team chat...</p>
      </div>
    );
  }

  return (
    <div className="h-[600px]">
      <ChatWidget
        conversationId={conversationId}
        conversationType={ConversationType.PROJECT_DISCUSSION}
        projectId={projectId}
        title={`${projectName ? `${projectName} - ` : ""}Team Chat`}
        showHistory={false}
        autoFocus={true}
      />
    </div>
  );
}
