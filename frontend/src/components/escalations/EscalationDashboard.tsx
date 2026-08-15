'use client';

import { useState } from 'react';
import { EscalationStatus, EscalationFilters } from '@/types/escalation';
import { useEscalations, useEscalationStats } from '@/hooks/useEscalations';
import { Button } from '@/components/ui/button';
import EscalationStats from './EscalationStats';
import EscalationList from './EscalationList';
import EscalationDetail from './EscalationDetail';
import EscalationFiltersPanel from './EscalationFilters';
import CreateEscalationModal from './CreateEscalationModal';

export default function EscalationDashboard() {
  const [selectedEscalationId, setSelectedEscalationId] = useState<string | null>(null);
  // const [showCreateModal, setShowCreateModal] = useState(false);
  const [filters, setFilters] = useState<EscalationFilters>({
    status: [EscalationStatus.OPEN, EscalationStatus.IN_PROGRESS, EscalationStatus.PENDING_HUMAN],
    order_by: 'created_at',
    order_desc: true,
    per_page: 50,
  });

  const { stats, loading: statsLoading } = useEscalationStats();
  const { escalations, total, loading, error, refetch } = useEscalations(filters);

  const handleFilterChange = (newFilters: Partial<EscalationFilters>) => {
    setFilters(prev => ({ ...prev, ...newFilters }));
  };

  const handleEscalationSelect = (escalationId: string) => {
    setSelectedEscalationId(escalationId);
  };

  // const handleEscalationCreated = () => {
  //   setShowCreateModal(false);
  //   refetch();
  // };

  const handleEscalationUpdated = () => {
    refetch();
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Escalations</h1>
          <p className="text-muted-foreground mt-1">
            Manage and resolve escalations across the organization
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => refetch()}
            className="gap-2"
          >
            <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
            </svg>
            Refresh
          </Button>
          {/* <Button
            size="sm"
            onClick={() => setShowCreateModal(true)}
          >
            + New Escalation
          </Button> */}
        </div>
      </div>

      {/* Statistics */}
      <EscalationStats stats={stats} loading={statsLoading} />

      {/* Filters */}
      <EscalationFiltersPanel
        filters={filters}
        onFilterChange={handleFilterChange}
        totalResults={total}
      />

      {/* Results Count */}
      {escalations.length > 0 && (
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          <span>
            Showing {escalations.length} of {total} escalations
          </span>
        </div>
      )}

      {/* Escalation List */}
      <div className="space-y-3">
        <EscalationList
          escalations={escalations}
          loading={loading}
          error={error}
          selectedId={selectedEscalationId}
          onSelect={handleEscalationSelect}
          onRefresh={refetch}
        />
      </div>

      {/* Escalation Detail Panel */}
      {selectedEscalationId && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40"
            onClick={() => setSelectedEscalationId(null)}
          />
          {/* Panel */}
          <div className="fixed inset-y-0 right-0 w-full max-w-2xl bg-card border-l shadow-2xl z-50 overflow-y-auto">
            <EscalationDetail
              escalationId={selectedEscalationId}
              onClose={() => setSelectedEscalationId(null)}
              onUpdate={handleEscalationUpdated}
            />
          </div>
        </>
      )}

      {/* Create Modal */}
      {/* {showCreateModal && (
        <CreateEscalationModal
          onClose={() => setShowCreateModal(false)}
          onCreated={handleEscalationCreated}
        />
      )} */}
    </div>
  );
}
