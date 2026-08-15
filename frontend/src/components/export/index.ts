/**
 * Export components index.
 *
 * Exports the new v2 components as the default, with legacy components
 * still available for backwards compatibility.
 */

// New v2 components (recommended)
export { ExportDialogV2 as ExportDialog } from './ExportDialogV2';
export { useExport, formatFileSize, getFormatInfo } from '@/hooks/useExportV2';
export type {
  ExportFormat,
  ExportOptions,
  ProjectExportInfo,
  ExportResult,
} from '@/hooks/useExportV2';

// Legacy components (deprecated, will be removed in future version)
export { ExportDialog as ExportDialogLegacy } from './export-dialog';
export { ExportProgress as ExportProgressLegacy } from './export-progress';
