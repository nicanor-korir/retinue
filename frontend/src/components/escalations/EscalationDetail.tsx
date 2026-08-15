'use client';

import { useState } from 'react';
import { useEscalation, useEscalationTimeline, useEscalationComments } from '@/hooks/useEscalations';
import { getPriorityColor, getStatusColor, getLevelColor, formatDate, formatEscalationType, formatStatus, getAssignedName } from '@/lib/escalationUtils';

interface EscalationDetailProps {
  escalationId: string;
  onClose: () => void;
  onUpdate: () => void;
}

export default function EscalationDetail({ escalationId, onClose, onUpdate }: EscalationDetailProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'timeline' | 'comments' | 'related'>('overview');
  const { escalation, loading } = useEscalation(escalationId);
  const { timeline } = useEscalationTimeline(escalationId);
  const { comments } = useEscalationComments(escalationId);

  if (loading) {
    return (
      <div className="p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-8 bg-muted rounded w-1/3"></div>
          <div className="h-4 bg-muted rounded w-full"></div>
          <div className="h-4 bg-muted rounded w-2/3"></div>
        </div>
      </div>
    );
  }

  if (!escalation) {
    return (
      <div className="p-6 text-center">
        <p className="text-muted-foreground">Escalation not found</p>
      </div>
    );
  }

  const tabs = [
    { id: 'overview' as const, label: 'Overview' },
    { id: 'timeline' as const, label: 'Timeline', count: timeline.length },
    { id: 'comments' as const, label: 'Comments', count: comments.length },
    { id: 'related' as const, label: 'Related' },
  ];

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="border-b p-6">
        <div className="flex items-start justify-between mb-4">
          <div>
            <div className="text-sm text-muted-foreground mb-1">{escalation.escalation_number}</div>
            <h2 className="text-2xl font-bold">{escalation.title}</h2>
          </div>
          <button onClick={onClose} className="text-muted-foreground hover:text-foreground">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex items-center gap-2 mb-4">
          <span className={`px-3 py-1 text-sm font-medium rounded-full border ${getPriorityColor(escalation.priority)}`}>
            {escalation.priority.toUpperCase()}
          </span>
          <span className={`px-3 py-1 text-sm font-medium rounded-full border ${getStatusColor(escalation.status)}`}>
            {formatStatus(escalation.status)}
          </span>
          <span className={`px-3 py-1 text-sm font-medium rounded-full border ${getLevelColor(escalation.level)}`}>
            {escalation.level.toUpperCase()}
          </span>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          <button className="px-4 py-2 text-sm font-medium text-white bg-green-600 dark:bg-green-700 rounded-lg hover:bg-green-700 dark:hover:bg-green-600">
            Resolve
          </button>
          <button className="px-4 py-2 text-sm font-medium text-white bg-orange-600 dark:bg-orange-700 rounded-lg hover:bg-orange-700 dark:hover:bg-orange-600">
            Escalate
          </button>
          <button className="px-4 py-2 text-sm font-medium bg-secondary text-secondary-foreground border rounded-lg hover:bg-secondary/80">
            Reassign
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b">
        <div className="flex px-6">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tab.id
                  ? 'border-primary text-primary'
                  : 'border-transparent text-muted-foreground hover:text-foreground'
              }`}
            >
              {tab.label}
              {tab.count !== undefined && (
                <span className="ml-2 px-2 py-0.5 text-xs bg-muted rounded-full">
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'overview' && (
          <div className="space-y-6">
            <div>
              <h3 className="text-sm font-medium mb-2">Description</h3>
              <p className="whitespace-pre-wrap">{escalation.description}</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-1">Type</h3>
                <p>{formatEscalationType(escalation.escalation_type)}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-1">Assigned To</h3>
                <p>{getAssignedName(escalation)}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-1">Created</h3>
                <p>{formatDate(escalation.created_at)}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-1">Updated</h3>
                <p>{formatDate(escalation.updated_at)}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-1">Impact</h3>
                <p className="capitalize">{escalation.impact_assessment}</p>
              </div>
              <div>
                <h3 className="text-sm font-medium text-muted-foreground mb-1">Urgency</h3>
                <p className="capitalize">{escalation.urgency}</p>
              </div>
            </div>

            {escalation.tags && escalation.tags.length > 0 && (
              <div>
                <h3 className="text-sm font-medium mb-2">Tags</h3>
                <div className="flex flex-wrap gap-2">
                  {escalation.tags.map((tag) => (
                    <span key={tag} className="px-2 py-1 text-xs bg-muted rounded">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {activeTab === 'timeline' && (
          <div className="space-y-4">
            {timeline.map((event) => (
              <div key={event.id} className="flex gap-3">
                <div className="flex-shrink-0 w-2 h-2 mt-2 bg-primary rounded-full"></div>
                <div className="flex-1">
                  <p className="text-sm font-medium">{event.description}</p>
                  <p className="text-xs text-muted-foreground mt-1">{formatDate(event.timestamp)}</p>
                </div>
              </div>
            ))}
          </div>
        )}

        {activeTab === 'comments' && (
          <div className="space-y-4">
            {comments.map((comment) => (
              <div key={comment.id} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium">{comment.author_id}</span>
                  <span className="text-xs text-muted-foreground">{formatDate(comment.created_at)}</span>
                </div>
                <p className="text-sm">{comment.content}</p>
              </div>
            ))}
            {comments.length === 0 && (
              <p className="text-center text-muted-foreground text-sm">No comments yet</p>
            )}
          </div>
        )}

        {activeTab === 'related' && (
          <div>
            <p className="text-center text-muted-foreground text-sm">No related items</p>
          </div>
        )}
      </div>
    </div>
  );
}
