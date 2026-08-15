"use client";

import { useState } from "react";
import {
  Download,
  Globe,
  CheckCircle2,
  Loader2,
  AlertCircle,
  Copy,
} from "lucide-react";
import { Button } from "@/components/ui/button";

interface ProjectCompletionDialogProps {
  projectId: string;
  projectName: string;
  onClose: () => void;
}

type DeliverableType = "download" | "hosted";

export function ProjectCompletionDialog({
  projectId,
  projectName,
  onClose,
}: ProjectCompletionDialogProps) {
  const [selectedType, setSelectedType] = useState<DeliverableType | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deliverableInfo, setDeliverableInfo] = useState<any>(null);
  const [copiedUrl, setCopiedUrl] = useState(false);

  const handleCompleteProject = async () => {
    if (!selectedType) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch(
        `/api/v1/projects/${projectId}/complete?deliverable_type=${selectedType}`,
        { method: "POST" }
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to complete project");
      }

      const data = await response.json();
      setDeliverableInfo(data);
      setIsComplete(true);

      // If hosted, also trigger deployment
      if (selectedType === "hosted") {
        await handleDeploy(data.hosted_url);
      }
    } catch (err: any) {
      setError(err.message || "An error occurred");
    } finally {
      setIsLoading(false);
    }
  };

  const handleDeploy = async (hostedUrl: string) => {
    try {
      const response = await fetch(
        `/api/v1/projects/${projectId}/deploy?hosting_provider=Deviant_cloud`,
        { method: "POST" }
      );

      if (!response.ok) {
        console.error("Deployment failed");
      }
    } catch (err) {
      console.error("Deployment error:", err);
    }
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopiedUrl(true);
      setTimeout(() => setCopiedUrl(false), 2000);
    } catch (err) {
      console.error("Failed to copy:", err);
    }
  };

  if (isComplete && deliverableInfo) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
        <div className="bg-card rounded-xl border border-border shadow-lg max-w-md w-full p-6 space-y-4">
          <div className="flex justify-center">
            <div className="relative">
              <div className="absolute inset-0 bg-green-500 rounded-full blur-xl opacity-20 animate-pulse" />
              <CheckCircle2 className="h-16 w-16 text-green-500 relative" />
            </div>
          </div>

          <div className="space-y-2 text-center">
            <h2 className="text-2xl font-bold">Project Complete!</h2>
            <p className="text-sm text-muted-foreground">
              {projectName} has been successfully processed
            </p>
          </div>

          {selectedType === "download" ? (
            <div className="bg-accent/50 rounded-lg p-4 space-y-3">
              <p className="text-sm font-medium">Ready for Download</p>
              <p className="text-xs text-muted-foreground">
                Your project files are packaged and ready to download. This includes all
                code, documentation, and outputs from your agent team.
              </p>
              <Button className="w-full" size="sm" asChild>
                <a
                  href={`/api/v1/projects/${projectId}/download`}
                  download={`${projectName}.zip`}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download Project
                </a>
              </Button>
            </div>
          ) : (
            <div className="bg-accent/50 rounded-lg p-4 space-y-3">
              <p className="text-sm font-medium">Deploying to Hosting</p>
              <div className="flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
                <p className="text-xs text-muted-foreground">
                  Your project is being deployed...
                </p>
              </div>
              {deliverableInfo.hosted_url && (
                <div className="space-y-2">
                  <p className="text-xs font-medium">Access URL:</p>
                  <div className="flex items-center gap-2 bg-background/50 rounded p-2">
                    <code className="text-xs flex-1 truncate">
                      {deliverableInfo.hosted_url}
                    </code>
                    <button
                      onClick={() => copyToClipboard(deliverableInfo.hosted_url)}
                      className="text-muted-foreground hover:text-foreground transition-colors"
                    >
                      {copiedUrl ? (
                        <CheckCircle2 className="h-4 w-4 text-green-500" />
                      ) : (
                        <Copy className="h-4 w-4" />
                      )}
                    </button>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    {deliverableInfo.estimated_time} deployment time
                  </p>
                </div>
              )}
            </div>
          )}

          <div className="pt-2 border-t">
            <p className="text-xs text-muted-foreground text-center mb-3">
              What's next?
            </p>
            <ul className="text-xs space-y-1 text-muted-foreground">
              <li>✓ Review deliverables</li>
              <li>✓ Test the project thoroughly</li>
              <li>✓ Deploy to production if needed</li>
              <li>✓ Provide feedback to agents</li>
            </ul>
          </div>

          <Button onClick={onClose} className="w-full" variant="outline">
            Close
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
      <div className="bg-card rounded-xl border border-border shadow-lg max-w-md w-full p-6 space-y-4">
        <div className="space-y-2">
          <h2 className="text-xl font-bold">Complete Project</h2>
          <p className="text-sm text-muted-foreground">
            How would you like to receive your completed {projectName} project?
          </p>
        </div>

        {error && (
          <div className="bg-destructive/10 border border-destructive/20 rounded-lg p-3 flex gap-2">
            <AlertCircle className="h-4 w-4 text-destructive flex-shrink-0 mt-0.5" />
            <div>
              <p className="text-xs text-destructive">{error}</p>
            </div>
          </div>
        )}

        <div className="space-y-3">
          {/* Download Option */}
          <button
            onClick={() => setSelectedType("download")}
            className={`w-full p-4 rounded-lg border-2 transition-all text-left ${
              selectedType === "download"
                ? "border-primary bg-primary/10"
                : "border-border/50 hover:border-primary/50"
            }`}
          >
            <div className="flex items-start gap-3">
              <div
                className={`p-2 rounded-lg ${
                  selectedType === "download"
                    ? "bg-blue-500/20 text-blue-500"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                <Download className="h-5 w-5" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold">Download</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Get all project files as a ZIP archive. Includes code, docs, and assets.
                </p>
              </div>
              {selectedType === "download" && (
                <div className="text-primary font-bold">✓</div>
              )}
            </div>
          </button>

          {/* Hosted Option */}
          <button
            onClick={() => setSelectedType("hosted")}
            className={`w-full p-4 rounded-lg border-2 transition-all text-left ${
              selectedType === "hosted"
                ? "border-primary bg-primary/10"
                : "border-border/50 hover:border-primary/50"
            }`}
          >
            <div className="flex items-start gap-3">
              <div
                className={`p-2 rounded-lg ${
                  selectedType === "hosted"
                    ? "bg-green-500/20 text-green-500"
                    : "bg-muted text-muted-foreground"
                }`}
              >
                <Globe className="h-5 w-5" />
              </div>
              <div className="flex-1">
                <p className="text-sm font-semibold">Deploy to Hosting</p>
                <p className="text-xs text-muted-foreground mt-1">
                  Automatically deploy and host your project. Get a live URL immediately.
                </p>
              </div>
              {selectedType === "hosted" && (
                <div className="text-primary font-bold">✓</div>
              )}
            </div>
          </button>
        </div>

        <div className="bg-accent/50 rounded-lg p-3 space-y-2">
          <p className="text-xs font-medium">About Hosting</p>
          <p className="text-xs text-muted-foreground">
            Projects are hosted on Deviant Cloud with automatic SSL, CDN, and monitoring.
            You can also export to Vercel or Heroku.
          </p>
        </div>

        <div className="flex gap-3 pt-2">
          <Button
            variant="outline"
            onClick={onClose}
            disabled={isLoading}
            className="flex-1"
          >
            Cancel
          </Button>
          <Button
            onClick={handleCompleteProject}
            disabled={!selectedType || isLoading}
            className="flex-1"
          >
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Processing...
              </>
            ) : (
              "Continue"
            )}
          </Button>
        </div>
      </div>
    </div>
  );
}
