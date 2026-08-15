'use client';

import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Lightbulb, Brain, CheckCircle, AlertCircle, TrendingUp, Code } from 'lucide-react';

interface Learning {
  learning_id: string;
  learning_type: string;
  title: string;
  description: string;
  status: string;
  priority: string;
  confidence_score: number;
  tested: boolean;
  affected_agent_ids: string[];
  system_prompt_update?: string;
  created_at: string;
}

interface LearningDashboardProps {
  systemLearnings?: Learning[];
  agentId?: string;
  isLoading?: boolean;
}

const LEARNING_TYPE_ICONS: Record<string, string> = {
  pattern: '🔄',
  mistake: '❌',
  improvement: '⬆️',
  best_practice: '⭐',
};

const STATUS_COLORS: Record<string, string> = {
  proposed: 'bg-blue-100 text-blue-800',
  approved: 'bg-green-100 text-green-800',
  implemented: 'bg-purple-100 text-purple-800',
  archived: 'bg-gray-100 text-gray-800',
};

const PRIORITY_COLORS: Record<string, string> = {
  low: 'bg-blue-100 text-blue-800',
  medium: 'bg-yellow-100 text-yellow-800',
  high: 'bg-orange-100 text-orange-800',
  critical: 'bg-red-100 text-red-800',
};

export function LearningDashboard({ systemLearnings = [], agentId, isLoading }: LearningDashboardProps) {
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [selectedTab, setSelectedTab] = useState('all');

  // Filter learnings based on agent if provided
  const filteredLearnings =
    agentId && selectedTab !== 'all'
      ? systemLearnings.filter(
          (learning) =>
            selectedTab === 'for-agent' ? learning.affected_agent_ids.includes(agentId) : true
        )
      : selectedTab === 'proposed'
      ? systemLearnings.filter((l) => l.status === 'proposed')
      : selectedTab === 'implemented'
      ? systemLearnings.filter((l) => l.status === 'implemented')
      : systemLearnings;

  const stats = {
    total: systemLearnings.length,
    proposed: systemLearnings.filter((l) => l.status === 'proposed').length,
    implemented: systemLearnings.filter((l) => l.status === 'implemented').length,
    highConfidence: systemLearnings.filter((l) => l.confidence_score >= 0.8).length,
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            System Learning
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-gray-500">Loading system learnings...</div>
        </CardContent>
      </Card>
    );
  }

  if (systemLearnings.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-5 w-5" />
            System Learning
          </CardTitle>
          <CardDescription>Track insights and improvements from feedback</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-gray-500 py-8 text-center">
            <Lightbulb className="h-8 w-8 mx-auto mb-2 text-gray-400" />
            <p>No system learnings yet. Insights will appear as feedback is processed.</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Brain className="h-5 w-5" />
              System Learning Dashboard
            </CardTitle>
            <CardDescription>Track patterns, improvements, and best practices</CardDescription>
          </div>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-2 mt-4">
          <div className="p-2 bg-blue-50 rounded-lg">
            <div className="text-xs text-gray-600">Total Learnings</div>
            <div className="text-2xl font-bold text-blue-600">{stats.total}</div>
          </div>
          <div className="p-2 bg-yellow-50 rounded-lg">
            <div className="text-xs text-gray-600">Proposed</div>
            <div className="text-2xl font-bold text-yellow-600">{stats.proposed}</div>
          </div>
          <div className="p-2 bg-green-50 rounded-lg">
            <div className="text-xs text-gray-600">Implemented</div>
            <div className="text-2xl font-bold text-green-600">{stats.implemented}</div>
          </div>
          <div className="p-2 bg-purple-50 rounded-lg">
            <div className="text-xs text-gray-600">High Confidence</div>
            <div className="text-2xl font-bold text-purple-600">{stats.highConfidence}</div>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* Tabs */}
        <Tabs defaultValue="all" value={selectedTab} onValueChange={setSelectedTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3 md:grid-cols-4 mb-4">
            <TabsTrigger value="all">All</TabsTrigger>
            <TabsTrigger value="proposed">Proposed</TabsTrigger>
            <TabsTrigger value="implemented">Implemented</TabsTrigger>
            {agentId && <TabsTrigger value="for-agent">For This Agent</TabsTrigger>}
          </TabsList>

          <TabsContent value={selectedTab} className="space-y-3">
            {filteredLearnings.length === 0 ? (
              <div className="text-center py-8 text-sm text-gray-500">
                No learnings in this category
              </div>
            ) : (
              filteredLearnings.map((learning) => (
                <div
                  key={learning.learning_id}
                  className="border rounded-lg p-4 hover:bg-gray-50 transition-colors"
                >
                  {/* Header */}
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div className="flex-1 min-w-0">
                      <button
                        onClick={() =>
                          setExpandedId(expandedId === learning.learning_id ? null : learning.learning_id)
                        }
                        className="text-left w-full"
                      >
                        <div className="flex items-start gap-2">
                          <span className="text-lg">{LEARNING_TYPE_ICONS[learning.learning_type] || '💭'}</span>
                          <h3 className="font-semibold text-sm leading-tight hover:text-blue-600 transition-colors flex-1">
                            {learning.title}
                          </h3>
                        </div>
                      </button>

                      {/* Meta tags */}
                      <div className="flex items-center gap-2 flex-wrap mt-2">
                        <Badge className={STATUS_COLORS[learning.status]}>
                          {learning.status}
                        </Badge>
                        <Badge className={PRIORITY_COLORS[learning.priority]}>
                          {learning.priority}
                        </Badge>
                        {learning.tested && (
                          <Badge variant="outline" className="bg-green-50">
                            <CheckCircle className="h-3 w-3 mr-1" />
                            Tested
                          </Badge>
                        )}
                      </div>
                    </div>

                    {/* Confidence Score */}
                    <div className="text-right">
                      <div className="text-xs text-gray-600 mb-1">Confidence</div>
                      <div className="text-lg font-bold">
                        {Math.round(learning.confidence_score * 100)}%
                      </div>
                    </div>
                  </div>

                  {/* Confidence Bar */}
                  <div className="mb-3">
                    <Progress
                      value={learning.confidence_score * 100}
                      className="h-2"
                    />
                  </div>

                  {/* Description - Preview */}
                  <p className="text-sm text-gray-700 line-clamp-2 mb-2">
                    {learning.description}
                  </p>

                  {/* Expanded Content */}
                  {expandedId === learning.learning_id && (
                    <div className="mt-3 pt-3 border-t space-y-3">
                      {/* Full Description */}
                      <div>
                        <h4 className="text-xs font-semibold text-gray-600 mb-1">Full Description</h4>
                        <p className="text-sm text-gray-700 whitespace-pre-wrap">
                          {learning.description}
                        </p>
                      </div>

                      {/* System Prompt Update */}
                      {learning.system_prompt_update && (
                        <div>
                          <h4 className="text-xs font-semibold text-gray-600 mb-1 flex items-center gap-2">
                            <Code className="h-3 w-3" />
                            System Prompt Update
                          </h4>
                          <div className="bg-gray-100 p-2 rounded text-xs font-mono text-gray-700 max-h-40 overflow-y-auto">
                            {learning.system_prompt_update}
                          </div>
                        </div>
                      )}

                      {/* Affected Agents */}
                      {learning.affected_agent_ids.length > 0 && (
                        <div>
                          <h4 className="text-xs font-semibold text-gray-600 mb-1">
                            Affects {learning.affected_agent_ids.length} Agent
                            {learning.affected_agent_ids.length !== 1 ? 's' : ''}
                          </h4>
                          <div className="flex flex-wrap gap-1">
                            {learning.affected_agent_ids.map((agentId) => (
                              <Badge key={agentId} variant="secondary">
                                {agentId}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Actions */}
                      <div className="flex gap-2 pt-2 border-t">
                        {learning.status === 'proposed' && (
                          <>
                            <Button size="sm" variant="default">
                              Approve
                            </Button>
                            <Button size="sm" variant="outline">
                              Reject
                            </Button>
                          </>
                        )}
                        {learning.status === 'approved' && (
                          <Button size="sm" variant="default">
                            Implement
                          </Button>
                        )}
                        {learning.status === 'implemented' && (
                          <Button size="sm" variant="outline" disabled>
                            ✓ Implemented
                          </Button>
                        )}
                      </div>
                    </div>
                  )}

                  {/* Timestamp */}
                  <div className="text-xs text-gray-500 mt-2">
                    {new Date(learning.created_at).toLocaleDateString()}
                  </div>
                </div>
              ))
            )}
          </TabsContent>
        </Tabs>

        {/* Info Box */}
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
          <p>
            <strong>💡 How it works:</strong> System learnings are automatically created from feedback
            patterns. They represent insights, best practices, and improvements that can be applied system-wide
            to improve future performance.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
