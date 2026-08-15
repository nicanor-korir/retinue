"use client";

import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface LoggingSettingsProps {
  settings?: any;
  onSettingsChange?: (updates: any) => void;
}

export function LoggingSettings({ settings, onSettingsChange }: LoggingSettingsProps) {
  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">Log Level</h3>
          <p className="text-sm text-muted-foreground">Set the verbosity of system logs</p>
        </div>
        <Select defaultValue="info">
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="error">Error - Critical issues only</SelectItem>
            <SelectItem value="warning">Warning - Errors and warnings</SelectItem>
            <SelectItem value="info">Info - General information (Recommended)</SelectItem>
            <SelectItem value="debug">Debug - Detailed debugging info</SelectItem>
            <SelectItem value="trace">Trace - Maximum verbosity</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="flex items-center justify-between py-4 border-b">
        <div className="space-y-0.5">
          <Label className="text-base font-semibold">Show LLM Thinking Process</Label>
          <p className="text-sm text-muted-foreground">Display detailed AI reasoning</p>
        </div>
        <Switch defaultChecked />
      </div>

      <div className="flex items-center justify-between py-4 border-b">
        <div className="space-y-0.5">
          <Label className="text-base font-semibold">Performance Metrics</Label>
          <p className="text-sm text-muted-foreground">Collect response times and latency</p>
        </div>
        <Switch defaultChecked />
      </div>

      <div className="flex items-center justify-between py-4 border-b">
        <div className="space-y-0.5">
          <Label className="text-base font-semibold">Debug Mode</Label>
          <p className="text-sm text-muted-foreground">Enable verbose debugging output</p>
        </div>
        <Switch />
      </div>
    </div>
  );
}
