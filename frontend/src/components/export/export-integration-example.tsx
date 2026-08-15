'use client';

/**
 * Example integration of Export components in a project page.
 *
 * This file demonstrates how to integrate the ExportDialog and ExportProgress
 * components in your project or task detail page.
 *
 * Usage:
 * 1. Import the components and hook
 * 2. Add state for dialog visibility
 * 3. Add the export button
 * 4. Render both the dialog and progress modal
 */

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Download } from 'lucide-react';
import { ExportDialog } from './export-dialog';
import { ExportProgress } from './export-progress';
import { useExport } from '@/hooks/useExport';

interface ExportIntegrationExampleProps {
  projectId: string;
  projectName: string;
}

/**
 * This component shows how to integrate export functionality into a project page.
 *
 * It handles:
 * - Opening/closing the export dialog
 * - Starting an export job
 * - Tracking and displaying export progress
 * - Cleanup when dialogs are closed
 */
export function ExportIntegrationExample({
  projectId,
  projectName,
}: ExportIntegrationExampleProps) {
  const [isExportDialogOpen, setIsExportDialogOpen] = useState(false);
  const [isProgressDialogOpen, setIsProgressDialogOpen] = useState(false);
  const [currentJobId, setCurrentJobId] = useState<string | null>(null);

  const handleExportStart = (jobId: string) => {
    setCurrentJobId(jobId);
    setIsExportDialogOpen(false);
    setIsProgressDialogOpen(true);
  };

  return (
    <>
      {/* Export Button - place this in your project toolbar/header */}
      <Button
        variant="outline"
        size="sm"
        className="gap-2"
        onClick={() => setIsExportDialogOpen(true)}
      >
        <Download className="h-4 w-4" />
        Export Project
      </Button>

      {/* Export Dialog - user selects export type and format */}
      <ExportDialog
        projectId={projectId}
        projectName={projectName}
        isOpen={isExportDialogOpen}
        onOpenChange={setIsExportDialogOpen}
        onExportStart={handleExportStart}
      />

      {/* Export Progress - shows progress and allows download */}
      <ExportProgress
        jobId={currentJobId}
        isOpen={isProgressDialogOpen}
        onOpenChange={setIsProgressDialogOpen}
      />
    </>
  );
}

/**
 * Usage in a project page:
 *
 * ```tsx
 * import { ExportIntegrationExample } from '@/components/export/export-integration-example';
 *
 * export default function ProjectPage({ params }: { params: { id: string } }) {
 *   return (
 *     <div>
 *       <div className="flex justify-between items-center mb-6">
 *         <h1>Project Details</h1>
 *         <ExportIntegrationExample
 *           projectId={params.id}
 *           projectName="My Project"
 *         />
 *       </div>
 *
 *       // Rest of project details
 *     </div>
 *   );
 * }
 * ```
 */
