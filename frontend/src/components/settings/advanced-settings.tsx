"use client";

import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle } from "lucide-react";

interface AdvancedSettingsProps {
  settings?: any;
  onSettingsChange?: (updates: any) => void;
}

export function AdvancedSettings({ settings, onSettingsChange }: AdvancedSettingsProps) {
  return (
    <div className="space-y-8">
      <div className="flex gap-3 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
        <AlertTriangle className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-0.5" />
        <div className="text-sm">
          <p className="font-medium text-yellow-500 mb-1">Experimental Features</p>
          <p className="text-muted-foreground">
            These settings are experimental and may be unstable. Use at your own risk.
          </p>
        </div>
      </div>

      <div className="space-y-3">
        <div className="flex items-center justify-between p-3 border rounded-lg">
          <div className="space-y-0.5">
            <Label className="text-sm font-medium flex items-center gap-2">
              Experimental Features
              <Badge variant="outline" className="text-xs">Beta</Badge>
            </Label>
            <p className="text-xs text-muted-foreground">Enable experimental functionality</p>
          </div>
          <Switch />
        </div>

        <div className="flex items-center justify-between p-3 border rounded-lg">
          <div className="space-y-0.5">
            <Label className="text-sm font-medium flex items-center gap-2">
              Beta Features
              <Badge variant="outline" className="text-xs">Preview</Badge>
            </Label>
            <p className="text-xs text-muted-foreground">Access beta features early</p>
          </div>
          <Switch />
        </div>

        <div className="flex items-center justify-between p-3 border rounded-lg">
          <div className="space-y-0.5">
            <Label className="text-sm font-medium">Developer Mode</Label>
            <p className="text-xs text-muted-foreground">Advanced debugging and development tools</p>
          </div>
          <Switch />
        </div>

        <div className="flex items-center justify-between p-3 border rounded-lg">
          <div className="space-y-0.5">
            <Label className="text-sm font-medium">Feature Flags</Label>
            <p className="text-xs text-muted-foreground">Toggle individual features</p>
          </div>
          <Switch />
        </div>

        <div className="flex items-center justify-between p-3 border rounded-lg">
          <div className="space-y-0.5">
            <Label className="text-sm font-medium">Custom Code Injection</Label>
            <p className="text-xs text-muted-foreground">Allow custom code execution hooks</p>
          </div>
          <Switch />
        </div>

        <div className="flex items-center justify-between p-3 border rounded-lg">
          <div className="space-y-0.5">
            <Label className="text-sm font-medium">System Override</Label>
            <p className="text-xs text-muted-foreground">Override default system behavior</p>
          </div>
          <Switch />
        </div>
      </div>
    </div>
  );
}
