/**
 * Knowledge Base Dashboard Page
 *
 * Main page for the intelligent knowledge base system with:
 * - Real-time search
 * - Extraction candidate review
 * - Analytics and insights
 * - WebSocket integration for live updates
 */

'use client';

import React, { useState, useCallback } from 'react';
import { Brain, Search, FileCheck, TrendingUp, Users, Bell } from 'lucide-react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { KnowledgeSearch } from '@/components/knowledge/knowledge-search';
import { KnowledgeDetail } from '@/components/knowledge/knowledge-detail';
import { ExtractionReview } from '@/components/knowledge/extraction-review';
import { KnowledgeAnalytics } from '@/components/knowledge/knowledge-analytics';
import { useWebSocket } from '@/hooks/useWebSocket';
import { useExtractionCandidates, KnowledgeEntry } from '@/hooks/useKnowledge';

export default function KnowledgePage() {
  const [selectedEntry, setSelectedEntry] = useState<KnowledgeEntry | null>(null);
  const [activeTab, setActiveTab] = useState('search');

  // Get extraction candidates count for badge
  const { data: candidates } = useExtractionCandidates({ limit: 100 });

  // WebSocket for real-time updates
  const { lastMessage } = useWebSocket({
    onMessage: handleWebSocketMessage,
  });

  function handleWebSocketMessage(message: any) {
    // Handle real-time knowledge updates
    if (message.type === 'knowledge_extracted') {
      // Show notification for new extraction
      console.log('New knowledge extracted:', message.data);
    } else if (message.type === 'knowledge_approved') {
      console.log('Knowledge approved:', message.data);
    }
  }

  const handleSelectEntry = useCallback((entry: KnowledgeEntry) => {
    setSelectedEntry(entry);
  }, []);

  // Mock user ID (in production, get from auth context)
  const userId = 'current-user-id';

  return (
    <div className="container mx-auto py-8 px-4 max-w-7xl">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <Brain className="h-8 w-8 text-primary" />
          <h1 className="text-3xl font-bold">Intelligent Knowledge Base</h1>
        </div>
        <p className="text-muted-foreground">
          AI-powered organizational knowledge management with automatic extraction and smart search
        </p>
      </div>

      {/* Main Content */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="grid w-full grid-cols-4 max-w-2xl">
          <TabsTrigger value="search" className="flex items-center gap-2">
            <Search className="h-4 w-4" />
            Search
          </TabsTrigger>
          <TabsTrigger value="review" className="flex items-center gap-2">
            <FileCheck className="h-4 w-4" />
            Review
            {candidates && candidates.length > 0 && (
              <Badge variant="secondary" className="ml-1">
                {candidates.length}
              </Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="analytics" className="flex items-center gap-2">
            <TrendingUp className="h-4 w-4" />
            Analytics
          </TabsTrigger>
          <TabsTrigger value="predictions" className="flex items-center gap-2">
            <Users className="h-4 w-4" />
            Predictions
          </TabsTrigger>
        </TabsList>

        {/* Search Tab */}
        <TabsContent value="search" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div>
              <KnowledgeSearch
                userId={userId}
                onSelectEntry={handleSelectEntry}
              />
            </div>
            <div>
              {selectedEntry ? (
                <KnowledgeDetail
                  entryId={selectedEntry.entry_id}
                  userId={userId}
                />
              ) : (
                <Card className="h-full flex items-center justify-center">
                  <CardContent className="text-center py-12">
                    <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <p className="text-muted-foreground">
                      Select a knowledge entry to view details
                    </p>
                  </CardContent>
                </Card>
              )}
            </div>
          </div>
        </TabsContent>

        {/* Review Tab */}
        <TabsContent value="review">
          <ExtractionReview reviewerId={userId} />
        </TabsContent>

        {/* Analytics Tab */}
        <TabsContent value="analytics">
          <KnowledgeAnalytics />
        </TabsContent>

        {/* Predictions Tab */}
        <TabsContent value="predictions">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Users className="h-5 w-5" />
                Agent Involvement Predictions
              </CardTitle>
              <CardDescription>
                AI predictions are context-aware and appear during conversations
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center py-8">
                <Users className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                <p className="text-muted-foreground mb-2">
                  Agent predictions appear when you're in a conversation or project
                </p>
                <p className="text-sm text-muted-foreground">
                  The AI analyzes conversation context to suggest which agents should be involved
                </p>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Real-time Notification */}
      {lastMessage && lastMessage.type === 'knowledge_extracted' && (
        <div className="fixed bottom-4 right-4 animate-in slide-in-from-bottom">
          <Card className="shadow-lg border-primary">
            <CardContent className="p-4 flex items-center gap-3">
              <Bell className="h-5 w-5 text-primary" />
              <div>
                <p className="text-sm font-medium">New Knowledge Extracted</p>
                <p className="text-xs text-muted-foreground">
                  Ready for review in the Review tab
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}
