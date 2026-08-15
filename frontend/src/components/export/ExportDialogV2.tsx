'use client';

/**
 * Export Dialog v2 - Simple, clean export UI.
 *
 * Design principles:
 * 1. Minimal options - format + what to include
 * 2. Smart defaults based on project type
 * 3. One-click export with auto-download
 * 4. Clear feedback on success/error
 */

import { useEffect, useState } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import {
  Download,
  FileText,
  Code,
  Package,
  Loader2,
  CheckCircle,
  AlertCircle,
} from 'lucide-react';
import {
  useExport,
  ExportFormat,
  formatFileSize,
  getFormatInfo,
} from '@/hooks/useExportV2';

interface ExportDialogProps {
  projectId: string;
  projectName: string;
  isOpen: boolean;
  onClose: () => void;
}

export function ExportDialogV2({
  projectId,
  projectName,
  isOpen,
  onClose,
}: ExportDialogProps) {
  const {
    loading,
    error,
    projectInfo,
    result,
    fetchProjectInfo,
    createExport,
    reset,
  } = useExport();

  // Simple state
  const [format, setFormat] = useState<ExportFormat>('pdf');
  const [includeTasks, setIncludeTasks] = useState(true);
  const [includeContent, setIncludeContent] = useState(true);
  const [includeConversations, setIncludeConversations] = useState(false);
  const [includeMetrics, setIncludeMetrics] = useState(false);

  // Fetch project info when dialog opens
  useEffect(() => {
    if (isOpen && projectId) {
      reset();
      fetchProjectInfo(projectId).then((info) => {
        // Set recommended format
        setFormat(info.recommended_format);
        // Enable options based on what exists
        setIncludeTasks(info.has_tasks);
        setIncludeContent(info.has_content);
      });
    }
  }, [isOpen, projectId, fetchProjectInfo, reset]);

  const handleExport = async () => {
    await createExport(projectId, {
      format,
      include_tasks: includeTasks,
      include_content: includeContent,
      include_conversations: includeConversations,
      include_metrics: includeMetrics,
    });
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  // Format buttons config
  const formatButtons: { value: ExportFormat; icon: React.ReactNode }[] = [
    { value: 'pdf', icon: <FileText className="h-5 w-5" /> },
    { value: 'markdown', icon: <Code className="h-5 w-5" /> },
    { value: 'zip', icon: <Package className="h-5 w-5" /> },
  ];

  return (
    <Dialog open={isOpen} onOpenChange={handleClose}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Export Project
          </DialogTitle>
          <DialogDescription>
            Export "{projectName}" to your preferred format
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-4">
          {/* Success State */}
          {result?.status === 'completed' && (
            <div className="rounded-lg bg-green-50 p-4 text-green-800 dark:bg-green-900/20 dark:text-green-200">
              <div className="flex items-center gap-2">
                <CheckCircle className="h-5 w-5" />
                <span className="font-medium">Export Complete!</span>
              </div>
              <p className="mt-1 text-sm">
                {result.file_name} ({result.file_size ? formatFileSize(result.file_size) : 'Unknown size'})
              </p>
              <p className="mt-2 text-xs opacity-75">
                Your download should start automatically. If not, check your browser's download folder.
              </p>
            </div>
          )}

          {/* Error State */}
          {error && (
            <div className="rounded-lg bg-red-50 p-4 text-red-800 dark:bg-red-900/20 dark:text-red-200">
              <div className="flex items-center gap-2">
                <AlertCircle className="h-5 w-5" />
                <span className="font-medium">Export Failed</span>
              </div>
              <p className="mt-1 text-sm">{error}</p>
            </div>
          )}

          {/* Loading State */}
          {loading && !result && (
            <div className="flex items-center justify-center py-8">
              <div className="text-center">
                <Loader2 className="mx-auto h-8 w-8 animate-spin text-blue-600" />
                <p className="mt-2 text-sm text-gray-600">Generating export...</p>
              </div>
            </div>
          )}

          {/* Export Options - only show when not loading/completed */}
          {!loading && !result && (
            <>
              {/* Format Selection */}
              <div>
                <Label className="text-sm font-medium">Format</Label>
                <div className="mt-2 grid grid-cols-3 gap-2">
                  {formatButtons.map(({ value, icon }) => {
                    const info = getFormatInfo(value);
                    const isSelected = format === value;
                    const isRecommended = projectInfo?.recommended_format === value;

                    return (
                      <button
                        key={value}
                        onClick={() => setFormat(value)}
                        className={`relative flex flex-col items-center rounded-lg border-2 p-3 transition-all ${
                          isSelected
                            ? 'border-blue-600 bg-blue-50 dark:bg-blue-900/20'
                            : 'border-gray-200 hover:border-gray-300 dark:border-gray-700'
                        }`}
                      >
                        {isRecommended && (
                          <span className="absolute -top-2 right-1 rounded bg-blue-600 px-1.5 py-0.5 text-[10px] font-medium text-white">
                            Best
                          </span>
                        )}
                        {icon}
                        <span className="mt-1 text-xs font-medium">{info.label}</span>
                      </button>
                    );
                  })}
                </div>
                <p className="mt-2 text-xs text-gray-500">
                  {getFormatInfo(format).description}
                </p>
              </div>

              {/* Include Options */}
              <div>
                <Label className="text-sm font-medium">Include</Label>
                <div className="mt-2 space-y-2">
                  <IncludeOption
                    id="tasks"
                    label="Tasks"
                    description={`${projectInfo?.task_count ?? 0} tasks`}
                    checked={includeTasks}
                    onChange={setIncludeTasks}
                    disabled={!projectInfo?.has_tasks}
                  />
                  <IncludeOption
                    id="content"
                    label="Content & Files"
                    description={`${projectInfo?.content_count ?? 0} items`}
                    checked={includeContent}
                    onChange={setIncludeContent}
                    disabled={!projectInfo?.has_content}
                  />
                  <IncludeOption
                    id="conversations"
                    label="Conversations"
                    description={`${projectInfo?.message_count ?? 0} messages`}
                    checked={includeConversations}
                    onChange={setIncludeConversations}
                    disabled={!projectInfo?.has_conversations}
                  />
                  <IncludeOption
                    id="metrics"
                    label="Metrics & Analytics"
                    description="Progress and performance data"
                    checked={includeMetrics}
                    onChange={setIncludeMetrics}
                    disabled={!projectInfo?.has_metrics}
                  />
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="flex justify-end gap-2 border-t pt-4">
          <Button variant="outline" onClick={handleClose}>
            {result ? 'Close' : 'Cancel'}
          </Button>
          {!result && (
            <Button onClick={handleExport} disabled={loading}>
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Exporting...
                </>
              ) : (
                <>
                  <Download className="mr-2 h-4 w-4" />
                  Export
                </>
              )}
            </Button>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}

// Helper component for include options
function IncludeOption({
  id,
  label,
  description,
  checked,
  onChange,
  disabled,
}: {
  id: string;
  label: string;
  description: string;
  checked: boolean;
  onChange: (checked: boolean) => void;
  disabled: boolean;
}) {
  return (
    <div
      className={`flex items-center gap-3 rounded-lg border p-2 ${
        disabled ? 'opacity-50' : ''
      }`}
    >
      <Checkbox
        id={id}
        checked={checked && !disabled}
        onCheckedChange={(c) => onChange(c === true)}
        disabled={disabled}
      />
      <div className="flex-1">
        <Label
          htmlFor={id}
          className={`text-sm font-medium ${disabled ? 'cursor-not-allowed' : 'cursor-pointer'}`}
        >
          {label}
        </Label>
        <p className="text-xs text-gray-500">{description}</p>
      </div>
    </div>
  );
}
