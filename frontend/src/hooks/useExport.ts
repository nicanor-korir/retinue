import { useState, useCallback } from 'react';
import axios from 'axios';

export type ExportType =
  | 'project_summary'
  | 'full_documentation'
  | 'task_report'
  | 'agent_activity_report'
  | 'code_documentation'
  | 'analytics_metrics';

export type ExportFormat = 'pdf' | 'markdown';

export interface ExportJob {
  job_id: string;
  project_id: string;
  export_format: ExportFormat;
  export_type: ExportType;
  status: 'pending' | 'gathering_data' | 'rendering' | 'generating' | 'completed' | 'failed' | 'cancelled';
  progress_percentage: number;
  current_step: string | null;
  created_at: string;
  completed_at: string | null;
  file_size_bytes: number | null;
  error_message: string | null;
}

export interface ExportOptions {
  export_type: ExportType;
  export_format: ExportFormat;
  include_sections?: string[];
  syntax_theme?: 'light' | 'dark';
  include_code?: boolean;
  include_images?: boolean;
  include_conversations?: boolean;
  date_range?: Record<string, string>;
}

interface UseExportState {
  job: ExportJob | null;
  loading: boolean;
  error: string | null;
}

interface UseExportActions {
  startExport: (projectId: string, options: ExportOptions) => Promise<string>;
  getJobStatus: (jobId: string) => Promise<ExportJob>;
  downloadExport: (jobId: string) => Promise<void>;
  cancelExport: (jobId: string) => Promise<void>;
  clearError: () => void;
}

export function useExport(initialJob: ExportJob | null = null): UseExportState & UseExportActions {
  const [job, setJob] = useState<ExportJob | null>(initialJob);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const startExport = useCallback(
    async (projectId: string, options: ExportOptions): Promise<string> => {
      setLoading(true);
      setError(null);

      try {
        const endpoint =
          options.export_format === 'pdf'
            ? `/api/v1/projects/${projectId}/export/pdf`
            : `/api/v1/projects/${projectId}/export/markdown`;

        const response = await axios.post(endpoint, options);
        const jobId = response.data.job_id;

        return jobId;
      } catch (err) {
        const message = axios.isAxiosError(err)
          ? err.response?.data?.detail || err.message
          : 'Failed to start export';
        setError(message);
        throw err;
      } finally {
        setLoading(false);
      }
    },
    []
  );

  const getJobStatus = useCallback(async (jobId: string): Promise<ExportJob> => {
    try {
      const response = await axios.get<ExportJob>(`/api/v1/exports/${jobId}/status`);
      setJob(response.data);
      setError(null);
      return response.data;
    } catch (err) {
      const message = axios.isAxiosError(err)
        ? err.response?.data?.detail || err.message
        : 'Failed to fetch job status';
      setError(message);
      throw err;
    }
  }, []);

  const downloadExport = useCallback(async (jobId: string): Promise<void> => {
    try {
      const response = await axios.get(`/api/v1/exports/${jobId}/download`, {
        responseType: 'blob',
      });

      // Get filename from Content-Disposition header or use default
      const contentDisposition = response.headers['content-disposition'];
      let filename = 'export';
      if (contentDisposition) {
        const match = contentDisposition.match(/filename="([^"]+)"/);
        if (match) {
          filename = match[1];
        }
      }

      // Create blob URL and trigger download
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', filename);
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);

      setError(null);
    } catch (err) {
      const message = axios.isAxiosError(err)
        ? err.response?.data?.detail || err.message
        : 'Failed to download export';
      setError(message);
      throw err;
    }
  }, []);

  const cancelExport = useCallback(async (jobId: string): Promise<void> => {
    try {
      const response = await axios.post(`/api/v1/exports/${jobId}/cancel`);
      if (job && job.job_id === jobId) {
        setJob({ ...job, status: 'cancelled' });
      }
      setError(null);
    } catch (err) {
      const message = axios.isAxiosError(err)
        ? err.response?.data?.detail || err.message
        : 'Failed to cancel export';
      setError(message);
      throw err;
    }
  }, [job]);

  return {
    job,
    loading,
    error,
    startExport,
    getJobStatus,
    downloadExport,
    cancelExport,
    clearError,
  };
}
