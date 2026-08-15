'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { BookOpen, Copy, MessageSquare, Lightbulb, AlertCircle } from 'lucide-react';
import axios from 'axios';

interface Context {
  context_id: string;
  title: string;
  content: string;
  tags: string[];
  source: string;
  implementation_status: string;
  created_at: string;
}

interface ContextDisplayProps {
  entityType: 'project' | 'task' | 'agent';
  entityId: string;
}

const TAG_COLORS: Record<string, string> = {
  requirements: 'bg-blue-100 text-blue-800',
  architecture: 'bg-purple-100 text-purple-800',
  performance: 'bg-red-100 text-red-800',
  security: 'bg-yellow-100 text-yellow-800',
  testing: 'bg-green-100 text-green-800',
  documentation: 'bg-cyan-100 text-cyan-800',
  design: 'bg-pink-100 text-pink-800',
  action_items: 'bg-orange-100 text-orange-800',
  follow_up: 'bg-indigo-100 text-indigo-800',
  improvement_plan: 'bg-teal-100 text-teal-800',
  blocking: 'bg-red-200 text-red-900',
  critical: 'bg-red-200 text-red-900',
  bug: 'bg-red-100 text-red-800',
  enhancement: 'bg-green-100 text-green-800',
  feature: 'bg-blue-100 text-blue-800',
  technical: 'bg-purple-100 text-purple-800',
  strategy: 'bg-indigo-100 text-indigo-800',
};

const IMPLEMENTATION_STATUS_ICONS: Record<string, JSX.Element> = {
  pending: <AlertCircle className="h-4 w-4 text-yellow-600" />,
  in_progress: <MessageSquare className="h-4 w-4 text-blue-600" />,
  implemented: <Lightbulb className="h-4 w-4 text-green-600" />,
};

export function ContextDisplay({ entityType, entityId }: ContextDisplayProps) {
  const [contexts, setContexts] = useState<Context[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  useEffect(() => {
    fetchContextUpdates();
  }, [entityType, entityId]);

  const fetchContextUpdates = async () => {
    try {
      setIsLoading(true);
      setError(null);

      const endpoint = `/api/v1/${entityType}/${entityId}/context`;
      const response = await axios.get(endpoint);
      setContexts(response.data.contexts || []);
    } catch (err) {
      console.error('Failed to fetch context:', err);
      setError('Failed to load context updates');
    } finally {
      setIsLoading(false);
    }
  };

  const handleCopyToClipboard = (content: string, contextId: string) => {
    navigator.clipboard.writeText(content);
    setCopiedId(contextId);
    setTimeout(() => setCopiedId(null), 2000);
  };

  if (isLoading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            Context & Information
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-gray-500">Loading context updates...</div>
        </CardContent>
      </Card>
    );
  }

  if (contexts.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <BookOpen className="h-5 w-5" />
            Context & Information
          </CardTitle>
          <CardDescription>No context updates yet</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-gray-500 py-4">
            Additional context and information provided through feedback will appear here.
          </div>
        </CardContent>
      </Card>
    );
  }

  // Group contexts by tag for better organization
  const contextsByTag: Record<string, Context[]> = {};
  contexts.forEach((ctx) => {
    ctx.tags.forEach((tag) => {
      if (!contextsByTag[tag]) {
        contextsByTag[tag] = [];
      }
      contextsByTag[tag].push(ctx);
    });
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <BookOpen className="h-5 w-5" />
          Context & Information
        </CardTitle>
        <CardDescription>
          {contexts.length} context update{contexts.length !== 1 ? 's' : ''} available
        </CardDescription>
      </CardHeader>

      <CardContent>
        <div className="space-y-4">
          {/* Tag-based grouping */}
          {Object.entries(contextsByTag).map(([tag, tagContexts]) => (
            <div key={tag} className="border rounded-lg p-4">
              <div className="flex items-center gap-2 mb-3">
                <Badge className={TAG_COLORS[tag] || 'bg-gray-100 text-gray-800'}>
                  {tag.replace(/_/g, ' ')}
                </Badge>
                <span className="text-xs text-gray-600">
                  {tagContexts.length} item{tagContexts.length !== 1 ? 's' : ''}
                </span>
              </div>

              <div className="space-y-2">
                {tagContexts.map((context) => (
                  <div
                    key={context.context_id}
                    className="bg-gray-50 rounded-lg p-3 hover:bg-gray-100 transition-colors"
                  >
                    {/* Header */}
                    <div className="flex items-start justify-between gap-2 mb-2">
                      <div className="flex-1 min-w-0">
                        <button
                          onClick={() =>
                            setExpandedId(expandedId === context.context_id ? null : context.context_id)
                          }
                          className="text-left w-full"
                        >
                          <h4 className="font-medium text-sm leading-tight hover:text-blue-600 transition-colors">
                            {context.title}
                          </h4>
                        </button>

                        {/* Status and metadata */}
                        <div className="flex items-center gap-2 flex-wrap mt-2">
                          <div className="flex items-center gap-1">
                            {IMPLEMENTATION_STATUS_ICONS[context.implementation_status] ||
                              IMPLEMENTATION_STATUS_ICONS.pending}
                            <span className="text-xs text-gray-600 capitalize">
                              {context.implementation_status.replace(/_/g, ' ')}
                            </span>
                          </div>
                          <span className="text-xs text-gray-500">
                            {new Date(context.created_at).toLocaleDateString()}
                          </span>
                          {context.source && (
                            <Badge variant="outline" className="text-xs">
                              {context.source}
                            </Badge>
                          )}
                        </div>
                      </div>

                      {/* Copy button */}
                      <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => handleCopyToClipboard(context.content, context.context_id)}
                        title="Copy to clipboard"
                      >
                        <Copy className="h-4 w-4" />
                      </Button>
                    </div>

                    {/* Content - Preview and Expanded */}
                    <div className="text-sm text-gray-700">
                      {expandedId === context.context_id ? (
                        // Expanded view - full content
                        <div className="max-h-96 overflow-y-auto whitespace-pre-wrap bg-white p-3 rounded border border-gray-200">
                          {context.content}
                        </div>
                      ) : (
                        // Collapsed view - preview
                        <p className="line-clamp-2 cursor-pointer hover:text-gray-900">
                          {context.content}
                        </p>
                      )}
                    </div>

                    {/* Feedback on copy */}
                    {copiedId === context.context_id && (
                      <div className="text-xs text-green-600 mt-2">✓ Copied to clipboard</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}

          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700 flex gap-2">
              <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
              <div>{error}</div>
            </div>
          )}
        </div>

        {/* Info box */}
        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
          <p>
            💡 <strong>How to use:</strong> Review this context information to understand feedback,
            suggestions, and action items provided for this {entityType}. Click to expand and copy
            context to use in your work.
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
