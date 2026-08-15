"use client";

import { useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import {
  FileText,
  Search,
  Filter,
  Download,
  CheckCircle2,
  XCircle,
  Clock,
  User,
  Activity,
  AlertCircle,
} from "lucide-react";
import { useAuditLogs } from "@/hooks/useApi";
import { formatDateTime, formatRelativeTime } from "@/lib/utils";

interface AuditLogFilters {
  agent_id?: string;
  action_type?: string;
  action?: string;
  search?: string;
}

export default function AuditPage() {
  const [filters, setFilters] = useState<AuditLogFilters>({});
  const [selectedLog, setSelectedLog] = useState<any>(null);
  const [showFilters, setShowFilters] = useState(false);

  const { data: auditLogs, isLoading } = useAuditLogs({ limit: 100, ...filters });

  const handleViewDetails = (log: any) => {
    setSelectedLog(log);
  };

  const getActionIcon = (action: string | undefined | null) => {
    if (!action) return <Activity className="h-4 w-4 text-gray-500" />;
    if (action.includes("created")) return <CheckCircle2 className="h-4 w-4 text-green-500" />;
    if (action.includes("deleted")) return <XCircle className="h-4 w-4 text-red-500" />;
    if (action.includes("updated") || action.includes("changed")) return <Clock className="h-4 w-4 text-blue-500" />;
    if (action.includes("failed") || action.includes("error")) return <AlertCircle className="h-4 w-4 text-red-500" />;
    return <Activity className="h-4 w-4 text-gray-500" />;
  };

  const getResultBadge = (log: any) => {
    // Infer result from action or check for error fields
    if (log.action && (log.action.includes("failed") || log.action.includes("error"))) {
      return <Badge variant="destructive">Failure</Badge>;
    }
    return <Badge variant="default" className="bg-green-600">Success</Badge>;
  };

  // Calculate statistics
  const stats = auditLogs ? {
    total: auditLogs.length,
    success: auditLogs.filter((l: any) => l.action && !l.action.includes("failed") && !l.action.includes("error")).length,
    failures: auditLogs.filter((l: any) => l.action && (l.action.includes("failed") || l.action.includes("error"))).length,
    uniqueAgents: new Set(auditLogs.map((l: any) => l.agent_id).filter(Boolean)).size,
    uniqueActions: new Set(auditLogs.map((l: any) => l.action).filter(Boolean)).size,
  } : { total: 0, success: 0, failures: 0, uniqueAgents: 0, uniqueActions: 0 };

  const successRate = stats.total > 0 ? Math.round((stats.success / stats.total) * 100) : 0;

  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-96">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary"></div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Audit Log</h1>
            <p className="text-muted-foreground">
              Complete history of all system actions and events
            </p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => setShowFilters(!showFilters)}>
              <Filter className="mr-2 h-4 w-4" />
              {showFilters ? "Hide" : "Show"} Filters
            </Button>
            <Button variant="outline">
              <Download className="mr-2 h-4 w-4" />
              Export CSV
            </Button>
          </div>
        </div>

        {/* Statistics Summary */}
        <div className="grid gap-4 md:grid-cols-5">
          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Total Events
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total}</div>
              <p className="text-xs text-muted-foreground mt-1">
                Last 100 events
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Success Rate
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-green-600">{successRate}%</div>
              <p className="text-xs text-muted-foreground mt-1">
                {stats.success} successful
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Failures
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">{stats.failures}</div>
              <p className="text-xs text-muted-foreground mt-1">
                {Math.round((stats.failures / stats.total) * 100) || 0}% failure rate
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Active Agents
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.uniqueAgents}</div>
              <p className="text-xs text-muted-foreground mt-1">
                Unique agents
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                Action Types
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.uniqueActions}</div>
              <p className="text-xs text-muted-foreground mt-1">
                Different actions
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Search & Filter Panel */}
        {showFilters && (
          <Card>
            <CardHeader>
              <CardTitle>Search & Filters</CardTitle>
              <CardDescription>Filter audit logs by various criteria</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid gap-4 md:grid-cols-3">
                <div className="space-y-2">
                  <Label htmlFor="search">Search</Label>
                  <div className="relative">
                    <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                    <Input
                      id="search"
                      placeholder="Search logs..."
                      className="pl-8"
                      value={filters.search || ""}
                      onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                    />
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="agent">Agent ID</Label>
                  <Input
                    id="agent"
                    placeholder="e.g., ceo_001"
                    value={filters.agent_id || ""}
                    onChange={(e) => setFilters({ ...filters, agent_id: e.target.value })}
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="action">Action Type</Label>
                  <Input
                    id="action"
                    placeholder="e.g., project_created"
                    value={filters.action_type || ""}
                    onChange={(e) => setFilters({ ...filters, action_type: e.target.value })}
                  />
                </div>
              </div>

              <div className="flex justify-end gap-2">
                <Button
                  variant="outline"
                  onClick={() => setFilters({})}
                >
                  Clear Filters
                </Button>
                <Button>Apply Filters</Button>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Results Count */}
        {auditLogs && auditLogs.length > 0 && (
          <div className="flex items-center justify-between text-sm text-muted-foreground">
            <span>
              Showing {auditLogs.length} events
            </span>
          </div>
        )}

        {/* Audit Log Cards */}
        <div className="space-y-3">
          {auditLogs && auditLogs.length > 0 ? (
            auditLogs.map((log) => (
              <Card
                key={log.log_id}
                className={`transition-all duration-200 cursor-pointer border-l-4 ${
                  log.action && (log.action.includes("failed") || log.action.includes("error"))
                    ? 'border-red-500/50 bg-red-500/5 hover:bg-red-500/10'
                    : 'border-green-500/50 bg-green-500/5 hover:bg-green-500/10'
                } ${selectedLog?.log_id === log.log_id ? 'ring-2 ring-primary shadow-lg' : 'shadow-sm hover:shadow-md'}`}
                onClick={() => handleViewDetails(log)}
              >
                <CardContent className="p-4">
                  <div className="space-y-3">
                    {/* Header Row */}
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-3 flex-1 min-w-0">
                        {/* Icon */}
                        <div className="h-10 w-10 rounded-full bg-primary/10 flex items-center justify-center flex-shrink-0">
                          {getActionIcon(log.action)}
                        </div>

                        {/* Actor Info */}
                        <div className="flex flex-col min-w-0 flex-1">
                          <span className="font-semibold truncate">{log.agent_id || "System"}</span>
                          <span className="text-xs text-muted-foreground">{formatRelativeTime(log.timestamp)}</span>
                        </div>
                      </div>

                      {/* Result Badge */}
                      <div className="flex items-center gap-2 flex-shrink-0">
                        {getResultBadge(log)}
                      </div>
                    </div>

                    {/* Action */}
                    <div className="pl-[52px]">
                      <div className="font-mono text-sm mb-1">{log.action || 'Unknown Action'}</div>
                      {log.entity_type && (
                        <div className="text-xs text-muted-foreground">
                          <span className="capitalize">{log.entity_type}</span>
                          {log.entity_id && <span className="ml-1 font-mono">• {log.entity_id}</span>}
                        </div>
                      )}
                    </div>

                    {/* Footer */}
                    <div className="flex items-center justify-between pt-2 border-t">
                      <div className="flex items-center gap-2 text-xs text-muted-foreground">
                        <Clock className="h-3 w-3" />
                        <span className="font-mono">{formatDateTime(log.created_at)}</span>
                      </div>
                      <Button
                        variant="ghost"
                        size="sm"
                        className="h-7 text-xs"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleViewDetails(log);
                        }}
                      >
                        View Details
                      </Button>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          ) : (
            <Card>
              <CardContent className="p-12 text-center">
                <FileText className="h-16 w-16 text-muted-foreground mx-auto mb-4" />
                <h3 className="text-lg font-semibold mb-2">No audit logs found</h3>
                <p className="text-muted-foreground">
                  {filters.search || filters.agent_id || filters.action
                    ? "Try adjusting your filters"
                    : "Actions will be logged here as they occur"}
                </p>
              </CardContent>
            </Card>
          )}
        </div>
      </div>

      {/* Detail Sidebar */}
      {selectedLog && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 bg-black/20 backdrop-blur-sm z-40"
            onClick={() => setSelectedLog(null)}
          />
          {/* Panel */}
          <div className="fixed inset-y-0 right-0 w-full max-w-2xl bg-card border-l shadow-2xl z-50 overflow-y-auto">
            <div className="p-6">
              {/* Header */}
              <div className="flex items-start justify-between mb-6 pb-4 border-b">
                <div>
                  <h2 className="text-2xl font-bold mb-1">Audit Log Details</h2>
                  <p className="text-sm text-muted-foreground">
                    Complete information about this audit event
                  </p>
                </div>
                <button
                  onClick={() => setSelectedLog(null)}
                  className="text-muted-foreground hover:text-foreground"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Content */}
            <div className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <h4 className="text-sm font-semibold mb-1 text-muted-foreground">Timestamp</h4>
                  <p className="text-sm">{formatDateTime(selectedLog.timestamp)}</p>
                  <p className="text-xs text-muted-foreground">{formatRelativeTime(selectedLog.timestamp)}</p>
                </div>
                <div>
                  <h4 className="text-sm font-semibold mb-1 text-muted-foreground">Actor</h4>
                  <p className="text-sm font-medium">{selectedLog.agent_id || "System"}</p>
                </div>
                <div>
                  <h4 className="text-sm font-semibold mb-1 text-muted-foreground">Action</h4>
                  <p className="text-sm font-mono">{selectedLog.action || 'Unknown Action'}</p>
                </div>
                <div>
                  <h4 className="text-sm font-semibold mb-1 text-muted-foreground">Result</h4>
                  {getResultBadge(selectedLog)}
                </div>
              </div>

              {/* Entity Info */}
              {selectedLog.entity_type && (
                <div>
                  <h4 className="text-sm font-semibold mb-2">Target Entity</h4>
                  <div className="bg-secondary p-3 rounded-lg space-y-2">
                    <div>
                      <span className="text-xs text-muted-foreground">Type:</span>{" "}
                      <span className="text-sm font-medium capitalize">{selectedLog.entity_type}</span>
                    </div>
                    {selectedLog.entity_id && (
                      <div>
                        <span className="text-xs text-muted-foreground">ID:</span>{" "}
                        <span className="text-sm font-mono">{selectedLog.entity_id}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Details */}
              {selectedLog.details && Object.keys(selectedLog.details).length > 0 && (
                <div>
                  <h4 className="text-sm font-semibold mb-2">Details</h4>
                  <pre className="bg-secondary p-3 rounded-lg text-xs overflow-x-auto">
                    {JSON.stringify(selectedLog.details, null, 2)}
                  </pre>
                </div>
              )}

              {/* Raw Data */}
              <details className="text-sm">
                <summary className="cursor-pointer font-semibold hover:text-primary">
                  View Raw JSON
                </summary>
                <pre className="mt-2 bg-secondary p-3 rounded-lg text-xs overflow-x-auto">
                  {JSON.stringify(selectedLog, null, 2)}
                </pre>
              </details>
              </div>
            </div>
          </div>
        </>
      )}
    </DashboardLayout>
  );
}
