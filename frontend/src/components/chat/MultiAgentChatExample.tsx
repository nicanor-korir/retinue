/**
 * Multi-Agent Chat Integration Example
 *
 * Complete example showing how to integrate all multi-agent components.
 * Use this as a reference for adding multi-agent features to existing chat components.
 */

'use client';

import React, { useState, useEffect } from 'react';
import { MessageSquare, Users, Sparkles, X } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';
import { useMultiAgentChat } from '@/hooks/useMultiAgent';
import { AgentSuggestionsPanel } from './AgentSuggestionsPanel';
import { ParticipantList, ParticipantCount } from './ParticipantList';
import { AgentPresenceIndicator } from './AgentPresenceIndicator';

export interface MultiAgentChatExampleProps {
  conversationId: string;
  userId: string;
  projectId?: string;
  className?: string;
}

/**
 * Complete multi-agent chat interface example
 */
export function MultiAgentChatExample({
  conversationId,
  userId,
  projectId,
  className,
}: MultiAgentChatExampleProps) {
  const [showSuggestionsPanel, setShowSuggestionsPanel] = useState(true);
  const [showParticipants, setShowParticipants] = useState(false);

  const {
    suggestions,
    suggestionsLoading,
    participants,
    participantsLoading,
    pendingInvitations,
    inviteAgent,
    dismissSuggestion,
    isInviting,
  } = useMultiAgentChat(conversationId, userId);

  // Auto-show suggestions if available
  useEffect(() => {
    if (suggestions.length > 0) {
      setShowSuggestionsPanel(true);
    }
  }, [suggestions.length]);

  const activeParticipants = participants.filter(
    p => p.presence?.status === 'active' ||
         p.presence?.status === 'thinking' ||
         p.presence?.status === 'typing'
  );

  const handleInviteAgent = async (agentId: string) => {
    try {
      await inviteAgent(agentId, 'User invited via AI suggestion');
      // Optionally close suggestions after inviting
      setShowSuggestionsPanel(false);
    } catch (error) {
      console.error('Failed to invite agent:', error);
    }
  };

  return (
    <div className={className}>
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Multi-Agent Chat</CardTitle>

            <div className="flex items-center gap-2">
              {/* Participant count with sheet trigger */}
              <Sheet open={showParticipants} onOpenChange={setShowParticipants}>
                <SheetTrigger asChild>
                  <div>
                    <ParticipantCount
                      count={participants.length}
                      activeCount={activeParticipants.length}
                      onClick={() => setShowParticipants(true)}
                    />
                  </div>
                </SheetTrigger>
                <SheetContent>
                  <SheetHeader>
                    <SheetTitle>Participants</SheetTitle>
                    <SheetDescription>
                      All agents in this conversation
                    </SheetDescription>
                  </SheetHeader>
                  <div className="mt-6">
                    <ParticipantList
                      participants={participants}
                      onInviteMore={() => setShowSuggestionsPanel(true)}
                      currentUserId={userId}
                    />
                  </div>
                </SheetContent>
              </Sheet>

              {/* Suggestions indicator */}
              {suggestions.length > 0 && !showSuggestionsPanel && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setShowSuggestionsPanel(true)}
                  className="h-8"
                >
                  <Sparkles className="h-4 w-4 mr-1" />
                  {suggestions.length} Suggestions
                </Button>
              )}
            </div>
          </div>

          {/* Pending invitations indicator */}
          {pendingInvitations.length > 0 && (
            <div className="mt-2">
              <Badge variant="secondary" className="text-xs">
                {pendingInvitations.length} pending invitation(s)
              </Badge>
            </div>
          )}
        </CardHeader>

        <Separator />

        <CardContent className="p-0">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-0">
            {/* Main chat area */}
            <div className="lg:col-span-2 border-r">
              <div className="p-4 space-y-4">
                {/* Agent suggestions panel */}
                {showSuggestionsPanel && suggestions.length > 0 && (
                  <AgentSuggestionsPanel
                    suggestions={suggestions}
                    onInvite={handleInviteAgent}
                    onDismiss={dismissSuggestion}
                    onClose={() => setShowSuggestionsPanel(false)}
                    isInviting={isInviting}
                  />
                )}

                {/* Chat messages would go here */}
                <div className="min-h-[400px] bg-muted/20 rounded-lg p-4 flex items-center justify-center">
                  <div className="text-center text-muted-foreground">
                    <MessageSquare className="h-12 w-12 mx-auto mb-2 opacity-50" />
                    <p className="text-sm">Chat messages appear here</p>
                    <p className="text-xs mt-1">
                      Integrate with your existing ChatWidget component
                    </p>
                  </div>
                </div>

                {/* Message input would go here */}
                <div className="h-12 bg-muted/20 rounded-lg flex items-center justify-center text-xs text-muted-foreground">
                  Message input area
                </div>
              </div>
            </div>

            {/* Sidebar - Participants and info */}
            <div className="hidden lg:block p-4 space-y-4">
              <ParticipantList
                participants={participants}
                onInviteMore={() => setShowSuggestionsPanel(true)}
                currentUserId={userId}
                compact={false}
              />

              {/* Suggestions in sidebar (alternative placement) */}
              {!showSuggestionsPanel && suggestions.length > 0 && (
                <div className="text-center">
                  <Button
                    variant="outline"
                    onClick={() => setShowSuggestionsPanel(true)}
                    className="w-full"
                  >
                    <Sparkles className="h-4 w-4 mr-2" />
                    View {suggestions.length} AI Suggestions
                  </Button>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}

/**
 * Minimal integration example for adding to existing chat
 */
export function MinimalMultiAgentIntegration({
  conversationId,
  userId,
}: {
  conversationId: string;
  userId: string;
}) {
  const {
    suggestions,
    participants,
    inviteAgent,
    dismissSuggestion,
  } = useMultiAgentChat(conversationId, userId);

  const activeCount = participants.filter(
    p => p.presence?.status === 'active' ||
         p.presence?.status === 'thinking' ||
         p.presence?.status === 'typing'
  ).length;

  return (
    <div className="space-y-2">
      {/* Add to chat header */}
      <div className="flex items-center gap-2">
        <ParticipantCount count={participants.length} activeCount={activeCount} />
      </div>

      {/* Add to chat content area */}
      {suggestions.length > 0 && (
        <AgentSuggestionsPanel
          suggestions={suggestions.slice(0, 2)} // Show top 2
          onInvite={(agentId) => inviteAgent(agentId)}
          onDismiss={dismissSuggestion}
        />
      )}
    </div>
  );
}

/**
 * Integration with existing ChatWidget
 *
 * Usage example:
 * ```tsx
 * import { ChatWidget } from '@/components/chat/ChatWidget';
 * import { useMultiAgentChat } from '@/hooks/useMultiAgent';
 *
 * function MyChat() {
 *   const conversationId = "uuid";
 *   const userId = "user_1";
 *
 *   const {
 *     suggestions,
 *     participants,
 *     inviteAgent,
 *   } = useMultiAgentChat(conversationId, userId);
 *
 *   return (
 *     <div>
 *       <ChatWidget conversationId={conversationId} />
 *
 *       // Add multi-agent features
 *       {suggestions.length > 0 && (
 *         <AgentSuggestionsPanel
 *           suggestions={suggestions}
 *           onInvite={inviteAgent}
 *         />
 *       )}
 *
 *       <ParticipantList participants={participants} />
 *     </div>
 *   );
 * }
 * ```
 */

export default MultiAgentChatExample;
