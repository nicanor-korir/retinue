'use client';

import EscalationDashboard from '@/components/escalations/EscalationDashboard';
import { DashboardLayout } from '@/components/layout/dashboard-layout';

export default function EscalationsPage() {
  return (
    <DashboardLayout>
      <div className="space-y-6">
        <EscalationDashboard />
      </div>
    </DashboardLayout>
  )
}
