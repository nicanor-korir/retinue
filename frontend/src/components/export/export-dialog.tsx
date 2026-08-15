'use client';

import { useState, useEffect } from 'react';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Checkbox } from '@/components/ui/checkbox';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Download, FileText, Loader2, AlertCircle, Package } from 'lucide-react';
import axios from 'axios';

interface ExportDialogProps {
  projectId: string;
  projectName: string;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onExportStart?: (jobId: string) => void;
}

export type ExportType =
  | 'project_summary'
  | 'full_documentation'
  | 'task_report'
  | 'agent_activity_report'
  | 'code_documentation'
  | 'analytics_metrics'
  | 'project_files_zip';

export type ExportFormat = 'pdf' | 'markdown' | 'zip';

interface ExportOptions {
  export_type: ExportType;
  export_format: ExportFormat;
  include_sections?: string[];
  syntax_theme?: 'light' | 'dark';
  include_code?: boolean;
  include_images?: boolean;
  include_conversations?: boolean;
}

interface ContentAvailability {
  available_export_types: ExportType[];
  content_flags: {
    has_tasks: boolean;
    has_completed_tasks: boolean;
    has_code_files: boolean;
    has_images: boolean;
    has_conversations: boolean;
    has_agent_activity: boolean;
    has_documentation: boolean;
  };
  recommendations: Record<string, string>;
}

const EXPORT_TYPES: Array<{ id: ExportType; label: string; description: string }> = [
  {
    id: 'project_summary',
    label: 'Project Summary',
    description: 'Quick overview with key metrics (2-5 pages)',
  },
  {
    id: 'full_documentation',
    label: 'Full Documentation',
    description: 'Comprehensive project documentation (20-100 pages)',
  },
  {
    id: 'task_report',
    label: 'Task Report',
    description: 'Detailed task breakdown with timeline and blockers',
  },
  {
    id: 'agent_activity_report',
    label: 'Agent Activity Report',
    description: 'Agent performance metrics and activity timeline',
  },
  {
    id: 'code_documentation',
    label: 'Code Documentation',
    description: 'Code files, API docs, and technical specs',
  },
  {
    id: 'analytics_metrics',
    label: 'Analytics & Metrics',
    description: 'Comprehensive analytics and trend analysis',
  },
  {
    id: 'project_files_zip',
    label: 'Download Project Files (ZIP)',
    description: 'Complete project files, code, and configuration for local development',
  },
];

export function ExportDialog({
  projectId,
  projectName,
  isOpen,
  onOpenChange,
  onExportStart,
}: ExportDialogProps) {
  const [exportType, setExportType] = useState<ExportType>('project_summary');
  const [exportFormat, setExportFormat] = useState<ExportFormat>('pdf');
  const [syntaxTheme, setSyntaxTheme] = useState<'light' | 'dark'>('light');
  const [includeCode, setIncludeCode] = useState(true);
  const [includeImages, setIncludeImages] = useState(true);
  const [includeConversations, setIncludeConversations] = useState(true);
  const [isExporting, setIsExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [contentAvailability, setContentAvailability] = useState<ContentAvailability | null>(null);

  // ZIP export specific options
  const [zipIncludeSourceCode, setZipIncludeSourceCode] = useState(true);
  const [zipIncludeTests, setZipIncludeTests] = useState(true);
  const [zipIncludeDocumentation, setZipIncludeDocumentation] = useState(true);
  const [zipIncludeAssets, setZipIncludeAssets] = useState(true);
  const [zipIncludeRetinueMetadata, setZipIncludeRetinueMetadata] = useState(true);
  const [zipIncludeEnvExample, setZipIncludeEnvExample] = useState(true);
  const [zipDocumentationLevel, setZipDocumentationLevel] = useState('standard');
  const [zipGenerateSetupScript, setZipGenerateSetupScript] = useState(true);

  const selectedExportType = EXPORT_TYPES.find((t) => t.id === exportType);

  // Fetch content availability when dialog opens
  useEffect(() => {
    if (isOpen) {
      fetchContentAvailability();
    }
  }, [isOpen, projectId]);

  const fetchContentAvailability = async () => {
    setIsAnalyzing(true);
    try {
      const response = await axios.get<ContentAvailability>(
        `/api/v1/projects/${projectId}/export-availability`
      );
      setContentAvailability(response.data);

      // Set default export type to first available type
      if (response.data.available_export_types.length > 0) {
        setExportType(response.data.available_export_types[0] as ExportType);
      }
    } catch (err) {
      console.error('Failed to analyze project content:', err);
      // Fall back to showing all options if analysis fails
      setContentAvailability(null);
    } finally {
      setIsAnalyzing(false);
    }
  };

  // Check if an export type is available
  const isExportTypeAvailable = (type: ExportType): boolean => {
    if (!contentAvailability) return true; // Show all if not analyzed
    return contentAvailability.available_export_types.includes(type);
  };

  // Check if a checkbox should be available
  const isCheckboxAvailable = (checkboxType: 'code' | 'images' | 'conversations'): boolean => {
    if (!contentAvailability) return true; // Show all if not analyzed
    switch (checkboxType) {
      case 'code':
        return contentAvailability.content_flags.has_code_files;
      case 'images':
        return contentAvailability.content_flags.has_images;
      case 'conversations':
        return contentAvailability.content_flags.has_conversations;
      default:
        return true;
    }
  };

  // Get recommendation for unavailable option
  const getRecommendation = (type: ExportType): string | undefined => {
    if (!contentAvailability) return undefined;
    return contentAvailability.recommendations[type];
  };

  const handleExport = async () => {
    setError(null);
    setIsExporting(true);

    try {
      let endpoint: string;
      let options: any;

      if (exportFormat === 'zip') {
        // ZIP export options
        options = {
          include_source_code: zipIncludeSourceCode,
          include_tests: zipIncludeTests,
          include_documentation: zipIncludeDocumentation,
          include_assets: zipIncludeAssets,
          include_database_schema: true,
          include_docker_config: false,
          include_ci_cd_config: false,
          include_retinue_metadata: zipIncludeRetinueMetadata,
          include_env_example: zipIncludeEnvExample,
          format_code: false,
          fix_linting_issues: false,
          documentation_level: zipDocumentationLevel,
          generate_setup_script: zipGenerateSetupScript,
          compression_level: 6,
        };
        endpoint = `/api/v1/projects/${projectId}/export/zip`;
      } else {
        // PDF/Markdown options
        options = {
          export_type: exportType,
          export_format: exportFormat,
          syntax_theme: syntaxTheme,
          include_code: includeCode,
          include_images: includeImages,
          include_conversations: includeConversations,
        };
        endpoint =
          exportFormat === 'pdf'
            ? `/api/v1/projects/${projectId}/export/pdf`
            : `/api/v1/projects/${projectId}/export/markdown`;
      }

      const response = await axios.post(endpoint, options);
      const jobId = response.data.job_id;

      onExportStart?.(jobId);
      onOpenChange(false);

      // Show success toast or notification
      console.log('Export job created:', jobId);
    } catch (err) {
      const message = axios.isAxiosError(err) ? err.response?.data?.detail || err.message : 'Export failed';
      setError(message);
      console.error('Export error:', err);
    } finally {
      setIsExporting(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Download className="h-5 w-5" />
            Export Project
          </DialogTitle>
          <DialogDescription>
            Choose export type and format for "{projectName}"
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6">
          {/* Loading State */}
          {isAnalyzing && (
            <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
              <p className="text-sm text-blue-700">Analyzing project content...</p>
            </div>
          )}

          {/* Export Type Selection */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold">Export Type</h3>
            <RadioGroup value={exportType} onValueChange={(value) => setExportType(value as ExportType)}>
              <div className="space-y-2">
                {EXPORT_TYPES.map((type) => {
                  const available = isExportTypeAvailable(type.id);
                  const recommendation = getRecommendation(type.id);

                  return (
                    <div key={type.id}>
                      <div
                        className={`flex items-start space-x-3 p-3 border rounded-lg transition-colors ${
                          available
                            ? 'hover:bg-gray-50 cursor-pointer'
                            : 'bg-gray-50 opacity-50 cursor-not-allowed border-dashed'
                        }`}
                      >
                        <RadioGroupItem
                          value={type.id}
                          id={type.id}
                          className="mt-1"
                          disabled={!available}
                        />
                        <div className="flex-1">
                          <Label
                            htmlFor={type.id}
                            className={`font-medium ${available ? 'cursor-pointer' : 'cursor-not-allowed text-gray-500'}`}
                          >
                            {type.label}
                          </Label>
                          <p className={`text-xs mt-1 ${available ? 'text-gray-600' : 'text-gray-500'}`}>
                            {type.description}
                          </p>
                        </div>
                      </div>

                      {/* Recommendation for unavailable export types */}
                      {!available && recommendation && (
                        <div className="mt-2 ml-7 flex items-start gap-2 p-2 bg-amber-50 border-l-2 border-amber-300 rounded text-sm">
                          <AlertCircle className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
                          <p className="text-amber-700">{recommendation}</p>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </RadioGroup>
          </div>

          {/* Format Selection */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold">Export Format</h3>
            <RadioGroup value={exportFormat} onValueChange={(value) => setExportFormat(value as ExportFormat)}>
              <div className="space-y-2">
                <div className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
                  <RadioGroupItem value="pdf" id="format-pdf" />
                  <Label htmlFor="format-pdf" className="flex-1 cursor-pointer">
                    <span className="font-medium">PDF</span>
                    <p className="text-xs text-gray-600">Professional, print-ready format</p>
                  </Label>
                </div>
                <div className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
                  <RadioGroupItem value="markdown" id="format-markdown" />
                  <Label htmlFor="format-markdown" className="flex-1 cursor-pointer">
                    <span className="font-medium">Markdown</span>
                    <p className="text-xs text-gray-600">Git-friendly, editable format</p>
                  </Label>
                </div>
                <div className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50 cursor-pointer">
                  <RadioGroupItem value="zip" id="format-zip" />
                  <Label htmlFor="format-zip" className="flex-1 cursor-pointer">
                    <span className="font-medium flex items-center gap-2">
                      <Package className="h-4 w-4" /> Project Files (ZIP)
                    </span>
                    <p className="text-xs text-gray-600">All code, docs, and configuration files</p>
                  </Label>
                </div>
              </div>
            </RadioGroup>
          </div>

          {/* PDF-specific Options */}
          {exportFormat === 'pdf' && (
            <div className="space-y-3 p-3 bg-blue-50 rounded-lg">
              <h3 className="text-sm font-semibold">PDF Styling</h3>
              <div className="space-y-2">
                <Label htmlFor="syntax-theme">Syntax Highlighting Theme</Label>
                <Select value={syntaxTheme} onValueChange={(value: any) => setSyntaxTheme(value)}>
                  <SelectTrigger id="syntax-theme">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">Light Theme</SelectItem>
                    <SelectItem value="dark">Dark Theme</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}

          {/* ZIP-specific Options */}
          {exportFormat === 'zip' && (
            <div className="space-y-3 p-3 bg-green-50 rounded-lg">
              <h3 className="text-sm font-semibold">Project Files Options</h3>
              <div className="space-y-3">
                {/* Documentation Level */}
                <div className="space-y-2">
                  <Label htmlFor="zip-doc-level">Documentation Level</Label>
                  <Select value={zipDocumentationLevel} onValueChange={setZipDocumentationLevel}>
                    <SelectTrigger id="zip-doc-level">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="minimal">Minimal (just README)</SelectItem>
                      <SelectItem value="standard">Standard (README + API docs)</SelectItem>
                      <SelectItem value="comprehensive">Comprehensive (all docs)</SelectItem>
                    </SelectContent>
                  </Select>
                </div>

                {/* File Inclusion */}
                <div className="space-y-2 border-t pt-3">
                  <p className="text-xs font-semibold text-gray-700">Include in Archive:</p>
                  <div className="space-y-2">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="zip-source"
                        checked={zipIncludeSourceCode}
                        onCheckedChange={(checked) => setZipIncludeSourceCode(checked as boolean)}
                      />
                      <Label htmlFor="zip-source" className="font-normal cursor-pointer text-sm">
                        Source code
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="zip-tests"
                        checked={zipIncludeTests}
                        onCheckedChange={(checked) => setZipIncludeTests(checked as boolean)}
                      />
                      <Label htmlFor="zip-tests" className="font-normal cursor-pointer text-sm">
                        Tests and test data
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="zip-docs"
                        checked={zipIncludeDocumentation}
                        onCheckedChange={(checked) => setZipIncludeDocumentation(checked as boolean)}
                      />
                      <Label htmlFor="zip-docs" className="font-normal cursor-pointer text-sm">
                        Documentation files
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="zip-assets"
                        checked={zipIncludeAssets}
                        onCheckedChange={(checked) => setZipIncludeAssets(checked as boolean)}
                      />
                      <Label htmlFor="zip-assets" className="font-normal cursor-pointer text-sm">
                        Assets (images, fonts)
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="zip-metadata"
                        checked={zipIncludeRetinueMetadata}
                        onCheckedChange={(checked) => setZipIncludeRetinueMetadata(checked as boolean)}
                      />
                      <Label htmlFor="zip-metadata" className="font-normal cursor-pointer text-sm">
                        Retinue metadata (project info, tasks)
                      </Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="zip-env"
                        checked={zipIncludeEnvExample}
                        onCheckedChange={(checked) => setZipIncludeEnvExample(checked as boolean)}
                      />
                      <Label htmlFor="zip-env" className="font-normal cursor-pointer text-sm">
                        .env.example configuration template
                      </Label>
                    </div>
                  </div>
                </div>

                {/* Setup Script */}
                <div className="border-t pt-3">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      id="zip-setup-script"
                      checked={zipGenerateSetupScript}
                      onCheckedChange={(checked) => setZipGenerateSetupScript(checked as boolean)}
                    />
                    <Label htmlFor="zip-setup-script" className="font-normal cursor-pointer text-sm">
                      Generate setup script (setup.sh/setup.bat)
                    </Label>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Additional Options */}
          <div className="space-y-3">
            <h3 className="text-sm font-semibold">Additional Options</h3>
            <div className="space-y-2">
              {isCheckboxAvailable('code') && (
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="include-code"
                    checked={includeCode}
                    onCheckedChange={(checked) => setIncludeCode(checked as boolean)}
                  />
                  <Label htmlFor="include-code" className="font-normal cursor-pointer">
                    Include code files
                  </Label>
                </div>
              )}

              {isCheckboxAvailable('images') && (
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="include-images"
                    checked={includeImages}
                    onCheckedChange={(checked) => setIncludeImages(checked as boolean)}
                  />
                  <Label htmlFor="include-images" className="font-normal cursor-pointer">
                    Include images and assets
                  </Label>
                </div>
              )}

              {isCheckboxAvailable('conversations') && (
                <div className="flex items-center space-x-2">
                  <Checkbox
                    id="include-conversations"
                    checked={includeConversations}
                    onCheckedChange={(checked) => setIncludeConversations(checked as boolean)}
                  />
                  <Label htmlFor="include-conversations" className="font-normal cursor-pointer">
                    Include agent conversations
                  </Label>
                </div>
              )}

              {!isCheckboxAvailable('code') && !isCheckboxAvailable('images') && !isCheckboxAvailable('conversations') && (
                <p className="text-sm text-gray-500 italic">
                  No additional content options available for this project
                </p>
              )}
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              <p className="font-medium">Export Failed</p>
              <p className="mt-1">{error}</p>
            </div>
          )}

          {/* Selected Summary */}
          {selectedExportType && (
            <div className="p-3 bg-gray-50 rounded-lg text-sm">
              <p className="text-gray-700">
                <span className="font-medium">Summary:</span> {selectedExportType.label} in {exportFormat.toUpperCase()}
              </p>
            </div>
          )}
        </div>

        {/* Footer Buttons */}
        <div className="flex justify-end gap-3 pt-6 border-t">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button
            onClick={handleExport}
            disabled={isExporting}
            className="gap-2"
          >
            {isExporting ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                Exporting...
              </>
            ) : (
              <>
                <Download className="h-4 w-4" />
                Export Project
              </>
            )}
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
}
