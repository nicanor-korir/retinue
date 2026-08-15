'use client';

import { useEffect, useState, useRef } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { AlertCircle, CheckCircle, Loader2, Download, Copy, X } from 'lucide-react';

interface ExportProgressProps {
  jobId: string | null;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
}

interface ExportJob {
  job_id: string;
  status: string;
  progress_percentage: number;
  current_step: string | null;
  export_format: string;
  export_type: string;
  created_at: string;
  completed_at: string | null;
  file_size_bytes: number | null;
  error_message: string | null;
}

const STATUS_STEPS = [
  { id: 'gathering_data', label: 'Gathering data', icon: '📊' },
  { id: 'rendering', label: 'Rendering', icon: '🎨' },
  { id: 'generating', label: 'Generating', icon: '⚙️' },
  { id: 'completed', label: 'Completed', icon: '✅' },
];

export function ExportProgress({ jobId, isOpen, onOpenChange }: ExportProgressProps) {
  const [job, setJob] = useState<ExportJob | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // Stream job status updates via SSE
  useEffect(() => {
    if (!jobId || !isOpen) {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
      return;
    }

    // Create SSE connection
    const eventSource = new EventSource(`/api/v1/exports/${jobId}/stream`);
    eventSourceRef.current = eventSource;

    // Handle incoming status messages
    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setJob(data);
        setError(null);
        setLoading(false);

        // If completed, generate download URL
        if (data.status === 'completed') {
          setDownloadUrl(`/api/v1/exports/${jobId}/download`);
        }
      } catch (err) {
        console.error('Failed to parse SSE message:', err);
      }
    };

    // Handle errors
    eventSource.addEventListener('error', (event: Event) => {
      const messageEvent = event as MessageEvent;
      const data = messageEvent.data ? JSON.parse(messageEvent.data) : null;
      const message = data?.error || 'Connection to server lost';
      setError(message);
      setLoading(false);
      eventSource.close();
    });

    // Handle completion
    eventSource.addEventListener('done', () => {
      eventSource.close();
    });

    // Handle connection errors
    eventSource.onerror = () => {
      setError('Failed to connect to server');
      setLoading(false);
      eventSource.close();
    };

    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
        eventSourceRef.current = null;
      }
    };
  }, [jobId, isOpen]);

  const handleDownload = async () => {
    if (!downloadUrl) return;

    try {
      const response = await fetch(downloadUrl);
      const blob = await response.blob();

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', job?.export_type || 'export');
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);

      onOpenChange(false)
    } catch (err) {
      console.error('Download failed:', err);
    }
  };

  const handleCopyUrl = async () => {
    if (downloadUrl) {
      const fullUrl = `${window.location.origin}${downloadUrl}`;
      await navigator.clipboard.writeText(fullUrl);
    }
  };

  const isCompleted = job?.status === 'completed';
  const isFailed = job?.status === 'failed';
  const isPending = job?.status === 'pending' || job?.status === 'gathering_data' || job?.status === 'rendering' || job?.status === 'generating';

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {isCompleted ? (
              <>
                <CheckCircle className="h-5 w-5 text-green-600" />
                Export Complete
              </>
            ) : isFailed ? (
              <>
                <AlertCircle className="h-5 w-5 text-red-600" />
                Export Failed
              </>
            ) : (
              <>
                <Loader2 className="h-5 w-5 animate-spin" />
                Generating Export
              </>
            )}
          </DialogTitle>
        </DialogHeader>

        {loading && !job ? (
          <div className="space-y-4 py-4">
            <div className="flex justify-center">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
            </div>
            <p className="text-center text-sm text-gray-600">Loading export status...</p>
          </div>
        ) : error && !job ? (
          <div className="space-y-4 py-4">
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700">
                <span className="font-medium">Error:</span> {error}
              </p>
            </div>
          </div>
        ) : job ? (
          <div className="space-y-6">
            {/* Format Info */}
            <div className="text-sm">
              <p className="text-gray-600">
                <span className="font-medium">{job.export_type.replace(/_/g, ' ').toUpperCase()}</span>
                {' • '}
                <span className="font-medium">{job.export_format.toUpperCase()}</span>
              </p>
            </div>

            {/* Progress Section */}
            {isPending && (
              <div className="space-y-4">
                {/* Progress Bar */}
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <p className="text-sm font-medium">Progress</p>
                    <span className="text-sm text-gray-600">{job.progress_percentage || 0}%</span>
                  </div>
                  <Progress value={job.progress_percentage || 0} className="h-2" />
                </div>

                {/* Current Step */}
                {job.current_step && (
                  <div className="p-3 bg-blue-50 rounded-lg">
                    <p className="text-sm">
                      <span className="font-medium">Current step:</span> {job.current_step}
                    </p>
                  </div>
                )}

                {/* Steps Timeline */}
                <div className="space-y-2 text-sm">
                  {STATUS_STEPS.map((step, idx) => {
                    const isActive = job.current_step?.toLowerCase().includes(step.id);
                    const isCompleted = (job.progress_percentage || 0) >= (idx + 1) * 25;

                    return (
                      <div key={step.id} className="flex items-center gap-2">
                        <div
                          className={`h-4 w-4 rounded-full flex items-center justify-center text-xs font-bold ${
                            isCompleted ? 'bg-green-600 text-white' : isActive ? 'bg-blue-600 text-white' : 'bg-gray-200'
                          }`}
                        >
                          {isCompleted ? '✓' : idx + 1}
                        </div>
                        <span className={isActive || isCompleted ? 'font-medium text-gray-900' : 'text-gray-600'}>
                          {step.label}
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Completed Section */}
            {isCompleted && (
              <div className="space-y-4">
                <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                  <p className="text-sm text-green-800">
                    <span className="font-medium">Success!</span> Your export is ready for download.
                  </p>
                </div>

                {job.file_size_bytes && (
                  <div className="text-sm text-gray-600">
                    File size: <span className="font-medium">{(job.file_size_bytes / 1024 / 1024).toFixed(2)} MB</span>
                  </div>
                )}

                <div className="flex gap-2">
                  <Button onClick={handleDownload} className="flex-1 gap-2" variant="default">
                    <Download className="h-4 w-4" />
                    Download
                  </Button>
                  <Button onClick={handleCopyUrl} variant="outline" size="icon" title="Copy download link">
                    <Copy className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            )}

            {/* Failed Section */}
            {isFailed && (
              <div className="space-y-4">
                <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                  <p className="text-sm text-red-800">
                    <span className="font-medium">Export Failed</span>
                  </p>
                  {job.error_message && (
                    <p className="text-sm text-red-700 mt-2">{job.error_message}</p>
                  )}
                </div>
              </div>
            )}

            {/* Meta Info */}
            <div className="text-xs text-gray-500 space-y-1 border-t pt-3">
              <p>Job ID: {job.job_id.substring(0, 8)}...</p>
              <p>Created: {new Date(job.created_at).toLocaleString()}</p>
            </div>
          </div>
        ) : null}

        {/* Footer */}
        <div className="flex justify-end gap-3 pt-6 border-t">
          {isCompleted ? (
            <>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Close
              </Button>
              <Button onClick={handleDownload} className="gap-2">
                <Download className="h-4 w-4" />
                Download
              </Button>
            </>
          ) : isFailed ? (
            <Button variant="outline" onClick={() => onOpenChange(false)}>
              Close
            </Button>
          ) : (
            <Button variant="outline" onClick={() => onOpenChange(false)} disabled={isPending}>
              Close
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
