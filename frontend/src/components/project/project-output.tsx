"use client";

import { useState } from "react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  CheckCircle2,
  FileText,
  Sparkles,
  ArrowRight,
  RefreshCw,
  MessageSquare,
} from "lucide-react";
import ReactMarkdown from 'react-markdown';
import { FollowUpQuestionModal } from "./follow-up-question-modal";

interface ProjectOutputProps {
  output: {
    query_type?: string;
    question?: string;
    answer?: string;
    answered_by?: string;
    can_continue?: boolean;
    decision?: string;
    analysis?: string;
    [key: string]: any;
  };
  projectName: string;
  projectId: string;
  projectStatus: string;
  onContinue?: () => void;
  onExpand?: () => void;
}

export function ProjectOutput({
  output,
  projectName,
  projectId,
  projectStatus,
  onContinue,
  onExpand,
}: ProjectOutputProps) {
  const [showFollowUpModal, setShowFollowUpModal] = useState(false);
  const isSimpleQuery = output.query_type === "simple_query";
  const isCompleted = projectStatus === "COMPLETED";

  if (!output || Object.keys(output).length === 0) {
    return null;
  }

  const handleAskFollowUp = () => {
    setShowFollowUpModal(true);
  };

  // Handle simple query output
  if (isSimpleQuery && output.answer) {
    return (
      <>
      <Card className="border-2 border-green-200 dark:border-green-900 bg-gradient-to-br from-green-50 to-emerald-50 dark:from-green-950/50 dark:to-emerald-950/30">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-6 w-6 text-green-600" />
                <CardTitle className="text-2xl">Answer Ready</CardTitle>
              </div>
              <CardDescription className="text-base">
                {output.answered_by || "CEO Agent"} has provided a comprehensive answer to your query
              </CardDescription>
            </div>
            <Badge variant="default" className="bg-green-600 text-white">
              <Sparkles className="h-3 w-3 mr-1" />
              Completed
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* The Question */}
          {output.question && (
            <div className="p-4 rounded-lg bg-white dark:bg-gray-900 border border-green-200 dark:border-green-800">
              <div className="flex items-start gap-3">
                <MessageSquare className="h-5 w-5 text-green-600 mt-1 flex-shrink-0" />
                <div>
                  <h3 className="font-semibold text-sm text-muted-foreground mb-1">Your Question:</h3>
                  <p className="text-lg font-medium">{output.question}</p>
                </div>
              </div>
            </div>
          )}

          {/* The Answer */}
          <div className="p-6 rounded-lg bg-white dark:bg-gray-900 border border-green-200 dark:border-green-800 shadow-sm">
            <div className="flex items-center gap-2 mb-4 pb-3 border-b">
              <FileText className="h-5 w-5 text-green-600" />
              <h3 className="font-semibold text-lg">Detailed Answer</h3>
            </div>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown
                components={{
                  h1: ({ node, ...props }) => <h1 className="text-2xl font-bold mt-6 mb-4" {...props} />,
                  h2: ({ node, ...props }) => <h2 className="text-xl font-bold mt-5 mb-3" {...props} />,
                  h3: ({ node, ...props }) => <h3 className="text-lg font-semibold mt-4 mb-2" {...props} />,
                  p: ({ node, ...props }) => <p className="mb-4 leading-7" {...props} />,
                  ul: ({ node, ...props }) => <ul className="list-disc pl-6 mb-4 space-y-2" {...props} />,
                  ol: ({ node, ...props }) => <ol className="list-decimal pl-6 mb-4 space-y-2" {...props} />,
                  li: ({ node, ...props }) => <li className="leading-7" {...props} />,
                  strong: ({ node, ...props }) => <strong className="font-semibold text-foreground" {...props} />,
                  code: ({ node, inline, ...props }: any) =>
                    inline ? (
                      <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono" {...props} />
                    ) : (
                      <code className="block bg-muted p-4 rounded-lg text-sm font-mono overflow-x-auto" {...props} />
                    ),
                }}
              >
                {output.answer}
              </ReactMarkdown>
            </div>
          </div>

          {/* Action Buttons */}
          {output.can_continue && (
            <div className="flex gap-3 pt-4 border-t">
              <Button
                onClick={onExpand}
                variant="outline"
                className="flex-1 gap-2"
              >
                <RefreshCw className="h-4 w-4" />
                Approve
              </Button>
              <Button
                onClick={handleAskFollowUp}
                className="flex-1 gap-2 bg-green-600 hover:bg-green-700"
              >
                <ArrowRight className="h-4 w-4" />
                Ask a Follow-up Question
              </Button>
            </div>
          )}

          {/* Info Box */}
          <div className="p-4 rounded-lg bg-blue-50 dark:bg-blue-950/30 border border-blue-200 dark:border-blue-900">
            <div className="flex items-start gap-3">
              <Sparkles className="h-5 w-5 text-blue-600 mt-0.5 flex-shrink-0" />
              <div className="text-sm text-blue-900 dark:text-blue-100">
                <p className="font-medium mb-1">Quick Research Completed</p>
                <p className="text-blue-700 dark:text-blue-300">
                  This was a simple information request that the CEO Agent handled directly.
                  If you need development work based on this information, click "Expand into Full Project" to involve the engineering team.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Follow-up Question Modal */}
      <FollowUpQuestionModal
        open={showFollowUpModal}
        onOpenChange={setShowFollowUpModal}
        projectName={projectName}
        projectId={projectId}
        originalQuestion={output.question}
      />
      </>
    );
  }

  // Handle development project output (decision/analysis)
  if (output.decision || output.analysis) {
    return (
      <Card className="border-2 border-blue-200 dark:border-blue-900 bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-950/50 dark:to-indigo-950/30">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-6 w-6 text-blue-600" />
                <CardTitle className="text-2xl">Project Analysis Complete</CardTitle>
              </div>
              <CardDescription className="text-base">
                CEO evaluation and decision on your project request
              </CardDescription>
            </div>
            <Badge 
              variant={output.decision === "approved" ? "default" : "secondary"}
              className={output.decision === "approved" ? "bg-green-600" : ""}
            >
              {output.decision?.toUpperCase() || "REVIEWED"}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="p-6 rounded-lg bg-white dark:bg-gray-900 border border-blue-200 dark:border-blue-800 shadow-sm">
            <div className="flex items-center gap-2 mb-4 pb-3 border-b">
              <FileText className="h-5 w-5 text-blue-600" />
              <h3 className="font-semibold text-lg">Analysis & Decision</h3>
            </div>
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown
                components={{
                  h1: ({ node, ...props }) => <h1 className="text-2xl font-bold mt-6 mb-4" {...props} />,
                  h2: ({ node, ...props }) => <h2 className="text-xl font-bold mt-5 mb-3" {...props} />,
                  h3: ({ node, ...props }) => <h3 className="text-lg font-semibold mt-4 mb-2" {...props} />,
                  p: ({ node, ...props }) => <p className="mb-4 leading-7" {...props} />,
                  ul: ({ node, ...props }) => <ul className="list-disc pl-6 mb-4 space-y-2" {...props} />,
                  ol: ({ node, ...props }) => <ol className="list-decimal pl-6 mb-4 space-y-2" {...props} />,
                  code: ({ node, inline, ...props }: any) =>
                    inline ? (
                      <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono" {...props} />
                    ) : (
                      <code className="block bg-muted p-4 rounded-lg text-sm font-mono overflow-x-auto" {...props} />
                    ),
                }}
              >
                {output.analysis}
              </ReactMarkdown>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  // Handle task outputs (code, files, deliverables)
  if (output.files || output.code || output.deliverables || output.implementation) {
    return (
      <Card className="border-2 border-purple-200 dark:border-purple-900 bg-gradient-to-br from-purple-50 to-pink-50 dark:from-purple-950/50 dark:to-pink-950/30">
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-6 w-6 text-purple-600" />
                <CardTitle className="text-2xl">Task Completed</CardTitle>
              </div>
              <CardDescription className="text-base">
                Deliverables and implementation details
              </CardDescription>
            </div>
            <Badge variant="default" className="bg-purple-600 text-white">
              <Sparkles className="h-3 w-3 mr-1" />
              Delivered
            </Badge>
          </div>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Files Created */}
          {output.files && Array.isArray(output.files) && output.files.length > 0 && (
            <div className="p-6 rounded-lg bg-white dark:bg-gray-900 border border-purple-200 dark:border-purple-800 shadow-sm">
              <div className="flex items-center gap-2 mb-4 pb-3 border-b">
                <FileText className="h-5 w-5 text-purple-600" />
                <h3 className="font-semibold text-lg">Files Created ({output.files.length})</h3>
              </div>
              <div className="space-y-4">
                {output.files.map((file: any, index: number) => (
                  <div key={index} className="border rounded-lg overflow-hidden">
                    <div className="bg-muted px-4 py-2 font-mono text-sm flex items-center justify-between">
                      <span className="font-semibold">{file.path || file.name || `File ${index + 1}`}</span>
                      {file.language && (
                        <Badge variant="outline" className="text-xs">{file.language}</Badge>
                      )}
                    </div>
                    <div className="p-4">
                      <pre className="text-sm overflow-x-auto">
                        <code>{file.content || file.code || JSON.stringify(file, null, 2)}</code>
                      </pre>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Code Implementation */}
          {output.code && (
            <div className="p-6 rounded-lg bg-white dark:bg-gray-900 border border-purple-200 dark:border-purple-800 shadow-sm">
              <div className="flex items-center gap-2 mb-4 pb-3 border-b">
                <FileText className="h-5 w-5 text-purple-600" />
                <h3 className="font-semibold text-lg">Code Implementation</h3>
              </div>
              <pre className="bg-muted p-4 rounded-lg text-sm overflow-x-auto">
                <code>{typeof output.code === 'string' ? output.code : JSON.stringify(output.code, null, 2)}</code>
              </pre>
            </div>
          )}

          {/* Implementation Details */}
          {output.implementation && (
            <div className="p-6 rounded-lg bg-white dark:bg-gray-900 border border-purple-200 dark:border-purple-800 shadow-sm">
              <div className="flex items-center gap-2 mb-4 pb-3 border-b">
                <Sparkles className="h-5 w-5 text-purple-600" />
                <h3 className="font-semibold text-lg">Implementation Details</h3>
              </div>
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown
                  components={{
                    code: ({ node, inline, ...props }: any) =>
                      inline ? (
                        <code className="bg-muted px-1.5 py-0.5 rounded text-sm font-mono" {...props} />
                      ) : (
                        <code className="block bg-muted p-4 rounded-lg text-sm font-mono overflow-x-auto" {...props} />
                      ),
                  }}
                >
                  {typeof output.implementation === 'string' 
                    ? output.implementation 
                    : JSON.stringify(output.implementation, null, 2)}
                </ReactMarkdown>
              </div>
            </div>
          )}

          {/* Deliverables */}
          {output.deliverables && (
            <div className="p-6 rounded-lg bg-white dark:bg-gray-900 border border-purple-200 dark:border-purple-800 shadow-sm">
              <div className="flex items-center gap-2 mb-4 pb-3 border-b">
                <CheckCircle2 className="h-5 w-5 text-purple-600" />
                <h3 className="font-semibold text-lg">Deliverables</h3>
              </div>
              <div className="prose prose-sm dark:prose-invert max-w-none">
                <ReactMarkdown>
                  {typeof output.deliverables === 'string' 
                    ? output.deliverables 
                    : JSON.stringify(output.deliverables, null, 2)}
                </ReactMarkdown>
              </div>
            </div>
          )}

          {/* Summary/Description if present */}
          {output.summary && (
            <div className="p-4 rounded-lg bg-purple-50 dark:bg-purple-950/30 border border-purple-200 dark:border-purple-900">
              <p className="text-sm text-purple-900 dark:text-purple-100">{output.summary}</p>
            </div>
          )}

          {/* Action Buttons */}
          {isCompleted && (
            <div className="flex gap-3 pt-4 border-t">
              <Button
                onClick={handleAskFollowUp}
                className="flex-1 gap-2 bg-purple-600 hover:bg-purple-700"
              >
                <MessageSquare className="h-4 w-4" />
                Ask Follow-up Question
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    );
  }

  // Handle generic output with better formatting
  return (
    <Card className="border-2 border-gray-200 dark:border-gray-800">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-2">
            <div className="flex items-center gap-2">
              <CheckCircle2 className="h-6 w-6 text-gray-600" />
              <CardTitle className="text-2xl">Output Available</CardTitle>
            </div>
            <CardDescription className="text-base">
              Task or project output details
            </CardDescription>
          </div>
          <Badge variant="outline">
            Completed
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="p-6 rounded-lg bg-white dark:bg-gray-900 border shadow-sm">
          <div className="flex items-center gap-2 mb-4 pb-3 border-b">
            <FileText className="h-5 w-5 text-gray-600" />
            <h3 className="font-semibold text-lg">Details</h3>
          </div>
          <pre className="bg-muted p-4 rounded-lg text-sm overflow-x-auto whitespace-pre-wrap break-words">
            {JSON.stringify(output, null, 2)}
          </pre>
        </div>

        {/* Action Buttons */}
        {isCompleted && (
          <div className="flex gap-3 pt-4 border-t">
            <Button
              onClick={handleAskFollowUp}
              variant="outline"
              className="flex-1 gap-2"
            >
              <MessageSquare className="h-4 w-4" />
              Ask Follow-up Question
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
