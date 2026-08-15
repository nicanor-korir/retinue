'use client';

import { useState } from 'react';
import { useEscalationMutations } from '@/hooks/useEscalations';
import { EscalationType, EscalationPriority, ImpactLevel, UrgencyLevel, CreateEscalationRequest } from '@/types/escalation';

interface CreateEscalationModalProps {
  onClose: () => void;
  onCreated: () => void;
}

export default function CreateEscalationModal({ onClose, onCreated }: CreateEscalationModalProps) {
  const { createEscalation, loading, error } = useEscalationMutations();
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    escalation_type: EscalationType.TECHNICAL_DECISION,
    priority: EscalationPriority.MEDIUM,
    impact: ImpactLevel.MEDIUM,
    urgency: UrgencyLevel.MEDIUM,
    department: '',
    tags: '',
  });

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    try {
      const request: CreateEscalationRequest = {
        title: formData.title,
        description: formData.description,
        escalation_type: formData.escalation_type,
        priority: formData.priority,
        impact: formData.impact,
        urgency: formData.urgency,
        created_by_type: 'user',
        created_by_id: 'current_user', // TODO: Get from auth context
        department: formData.department || undefined,
        tags: formData.tags ? formData.tags.split(',').map(t => t.trim()) : undefined,
      };

      await createEscalation(request);
      onCreated();
    } catch (err) {
      // Error is handled in the hook
      console.error('Failed to create escalation:', err);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="bg-card rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto border shadow-lg">
        <div className="sticky top-0 bg-card border-b px-6 py-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold">Create Escalation</h2>
            <button
              onClick={onClose}
              className="text-muted-foreground hover:text-foreground"
              disabled={loading}
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-4">
          {error && (
            <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-4 text-sm text-destructive">
              {error}
            </div>
          )}

          {/* Title */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Title <span className="text-destructive">*</span>
            </label>
            <input
              type="text"
              required
              value={formData.title}
              onChange={(e) => setFormData({ ...formData, title: e.target.value })}
              className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Brief summary of the issue"
            />
          </div>

          {/* Description */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Description <span className="text-destructive">*</span>
            </label>
            <textarea
              required
              value={formData.description}
              onChange={(e) => setFormData({ ...formData, description: e.target.value })}
              rows={4}
              className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Detailed description of the escalation"
            />
          </div>

          {/* Type */}
          <div>
            <label className="block text-sm font-medium mb-1">
              Escalation Type <span className="text-destructive">*</span>
            </label>
            <select
              value={formData.escalation_type}
              onChange={(e) => setFormData({ ...formData, escalation_type: e.target.value as EscalationType })}
              className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {Object.values(EscalationType).map((type) => (
                <option key={type} value={type}>
                  {type.split('_').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                </option>
              ))}
            </select>
          </div>

          {/* Priority, Impact, Urgency */}
          <div className="grid grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">Priority</label>
              <select
                value={formData.priority}
                onChange={(e) => setFormData({ ...formData, priority: e.target.value as EscalationPriority })}
                className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {Object.values(EscalationPriority).map((priority) => (
                  <option key={priority} value={priority} className="capitalize">
                    {priority}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Impact</label>
              <select
                value={formData.impact}
                onChange={(e) => setFormData({ ...formData, impact: e.target.value as ImpactLevel })}
                className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {Object.values(ImpactLevel).map((impact) => (
                  <option key={impact} value={impact} className="capitalize">
                    {impact}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium mb-1">Urgency</label>
              <select
                value={formData.urgency}
                onChange={(e) => setFormData({ ...formData, urgency: e.target.value as UrgencyLevel })}
                className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              >
                {Object.values(UrgencyLevel).map((urgency) => (
                  <option key={urgency} value={urgency} className="capitalize">
                    {urgency}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Department */}
          <div>
            <label className="block text-sm font-medium mb-1">Department (Optional)</label>
            <input
              type="text"
              value={formData.department}
              onChange={(e) => setFormData({ ...formData, department: e.target.value })}
              className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="e.g., Engineering, Finance"
            />
          </div>

          {/* Tags */}
          <div>
            <label className="block text-sm font-medium mb-1">Tags (Optional)</label>
            <input
              type="text"
              value={formData.tags}
              onChange={(e) => setFormData({ ...formData, tags: e.target.value })}
              className="w-full px-3 py-2 bg-background border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary"
              placeholder="Comma-separated tags"
            />
            <p className="text-xs text-muted-foreground mt-1">Separate tags with commas</p>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 text-sm font-medium bg-secondary text-secondary-foreground border rounded-lg hover:bg-secondary/80 disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="px-4 py-2 text-sm font-medium text-primary-foreground bg-primary rounded-lg hover:bg-primary/90 disabled:opacity-50"
            >
              {loading ? 'Creating...' : 'Create Escalation'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
