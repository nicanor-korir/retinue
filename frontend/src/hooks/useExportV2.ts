/**
 * Export Hook v2 - Simple, clean export state management.
 *
 * Design principles:
 * 1. Minimal state - just what's needed
 * 2. Single action flow - start export, get file
 * 3. Clear loading/error states
 * 4. No complex job polling - exports complete synchronously
 */

import { useState, useCallback } from 'react';

// Types
export type ExportFormat = 'pdf' | 'markdown' | 'zip';

export interface ExportOptions {
  format: ExportFormat;
  include_tasks?: boolean;
  include_content?: boolean;
  include_conversations?: boolean;
  include_metrics?: boolean;
}

export interface ProjectExportInfo {
  project_id: string;
  project_name: string;
  project_type: 'software' | 'content' | 'marketing' | 'legal' | 'general';
  has_tasks: boolean;
  has_content: boolean;
  has_conversations: boolean;
  has_metrics: boolean;
  task_count: number;
  content_count: number;
  message_count: number;
  recommended_format: ExportFormat;
}

export interface ExportResult {
  job_id: string;
  status: 'completed' | 'failed';
  progress: number;
  message: string | null;
  download_url: string | null;
  file_name: string | null;
  file_size: number | null;
}

interface UseExportState {
  loading: boolean;
  error: string | null;
  projectInfo: ProjectExportInfo | null;
  result: ExportResult | null;
}

interface UseExportActions {
  fetchProjectInfo: (projectId: string) => Promise<ProjectExportInfo>;
  createExport: (projectId: string, options: ExportOptions) => Promise<ExportResult>;
  downloadFile: (downloadUrl: string, fileName: string) => void;
  reset: () => void;
}

export function useExport(): UseExportState & UseExportActions {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [projectInfo, setProjectInfo] = useState<ProjectExportInfo | null>(null);
  const [result, setResult] = useState<ExportResult | null>(null);

  const fetchProjectInfo = useCallback(async (projectId: string): Promise<ProjectExportInfo> => {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/v2/exports/projects/${projectId}/info`);

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || `Failed to fetch project info: ${response.status}`);
      }

      const info: ProjectExportInfo = await response.json();
      setProjectInfo(info);
      return info;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to fetch project info';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const createExport = useCallback(async (projectId: string, options: ExportOptions): Promise<ExportResult> => {
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch(`/api/v2/exports/projects/${projectId}/export`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(options),
      });

      if (!response.ok) {
        const data = await response.json().catch(() => ({}));
        throw new Error(data.detail || `Export failed: ${response.status}`);
      }

      const exportResult: ExportResult = await response.json();
      setResult(exportResult);

      // Auto-download on success
      if (exportResult.status === 'completed' && exportResult.download_url && exportResult.file_name) {
        downloadFile(exportResult.download_url, exportResult.file_name);
      }

      return exportResult;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Export failed';
      setError(message);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  const downloadFile = useCallback((downloadUrl: string, fileName: string) => {
    // Create a temporary link and click it to download
    const link = document.createElement('a');
    // downloadUrl is already absolute (e.g., /api/v2/exports/download/filename.pdf)
    link.href = downloadUrl;
    link.download = fileName;
    link.style.display = 'none';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  }, []);

  const reset = useCallback(() => {
    setLoading(false);
    setError(null);
    setProjectInfo(null);
    setResult(null);
  }, []);

  return {
    loading,
    error,
    projectInfo,
    result,
    fetchProjectInfo,
    createExport,
    downloadFile,
    reset,
  };
}

// Helper to format file sizes
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

// Helper to get format info
export function getFormatInfo(format: ExportFormat): { icon: string; label: string; description: string } {
  const formats = {
    pdf: {
      icon: '📄',
      label: 'PDF',
      description: 'Professional document, great for sharing and printing',
    },
    markdown: {
      icon: '📝',
      label: 'Markdown',
      description: 'Plain text, easy to edit and version control',
    },
    zip: {
      icon: '📦',
      label: 'ZIP Archive',
      description: 'All files packaged together, ready for development',
    },
  };
  return formats[format];
}
