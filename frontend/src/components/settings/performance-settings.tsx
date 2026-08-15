"use client";

import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Badge } from "@/components/ui/badge";
import { useState, useEffect } from "react";

interface PerformanceSettingsProps {
  settings?: any;
  onSettingsChange?: (updates: any) => void;
}

export function PerformanceSettings({ settings, onSettingsChange }: PerformanceSettingsProps) {
  const [concurrentAgents, setConcurrentAgents] = useState<number[]>([5]);

  // Initialize from backend settings
  useEffect(() => {
    if (settings) {
      if (settings.concurrentAgents !== undefined) setConcurrentAgents([settings.concurrentAgents]);
    }
  }, [settings]);

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between py-4 border-b">
        <div className="space-y-0.5">
          <Label className="text-base font-semibold">Request Caching</Label>
          <p className="text-sm text-muted-foreground">Cache repeated requests</p>
        </div>
        <Switch defaultChecked />
      </div>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold mb-1">Concurrent Agent Limit</h3>
            <p className="text-sm text-muted-foreground">Maximum agents running simultaneously</p>
          </div>
          <Badge variant="outline">{concurrentAgents[0]}</Badge>
        </div>
        <Slider value={concurrentAgents} onValueChange={setConcurrentAgents} min={1} max={20} step={1} />
      </div>

      <div className="flex items-center justify-between py-4 border-b">
        <div className="space-y-0.5">
          <Label className="text-base font-semibold">Auto-Scaling</Label>
          <p className="text-sm text-muted-foreground">Automatically scale resources</p>
        </div>
        <Switch defaultChecked />
      </div>
    </div>
  );
}
