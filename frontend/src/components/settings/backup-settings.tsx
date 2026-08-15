"use client";

import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Download, Upload, Trash2 } from "lucide-react";

interface BackupSettingsProps {
  settings?: any;
  onSettingsChange?: (updates: any) => void;
}

export function BackupSettings({ settings, onSettingsChange }: BackupSettingsProps) {
  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold mb-1">Automatic Backups</h3>
            <p className="text-sm text-muted-foreground">Scheduled data backups</p>
          </div>
          <Switch defaultChecked />
        </div>
        <Select defaultValue="daily">
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="hourly">Every Hour</SelectItem>
            <SelectItem value="daily">Daily</SelectItem>
            <SelectItem value="weekly">Weekly</SelectItem>
            <SelectItem value="monthly">Monthly</SelectItem>
          </SelectContent>
        </Select>
      </div>

      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">Export Data</h3>
          <p className="text-sm text-muted-foreground">Download your data in various formats</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Export JSON
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Export CSV
          </Button>
          <Button variant="outline" className="flex items-center gap-2">
            <Download className="h-4 w-4" />
            Database Dump
          </Button>
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">Import Settings</h3>
          <p className="text-sm text-muted-foreground">Restore settings from file</p>
        </div>
        <Button variant="outline" className="flex items-center gap-2">
          <Upload className="h-4 w-4" />
          Import from File
        </Button>
      </div>

      <div className="space-y-4 p-4 border border-destructive/50 rounded-lg bg-destructive/5">
        <div>
          <h3 className="text-lg font-semibold mb-1 text-destructive">Danger Zone</h3>
          <p className="text-sm text-muted-foreground">Irreversible actions</p>
        </div>
        <Button variant="destructive" className="flex items-center gap-2">
          <Trash2 className="h-4 w-4" />
          Delete All Data
        </Button>
      </div>
    </div>
  );
}
