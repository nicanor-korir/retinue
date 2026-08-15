"use client";

import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Key, Shield, Lock, Eye, EyeOff } from "lucide-react";

interface SecuritySettingsProps {
  settings?: any;
  onSettingsChange?: (updates: any) => void;
}

export function SecuritySettings({ settings, onSettingsChange }: SecuritySettingsProps) {
  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">API Key Management</h3>
          <p className="text-sm text-muted-foreground">Manage your API keys and access tokens</p>
        </div>
        <div className="flex gap-2">
          <Input type="password" placeholder="••••••••••••••••" className="flex-1" />
          <Button variant="outline">Generate</Button>
          <Button variant="outline">Rotate</Button>
        </div>
      </div>

      <div className="flex items-center justify-between py-4 border-b">
        <div className="space-y-0.5">
          <Label className="text-base font-semibold flex items-center gap-2">
            <Shield className="h-4 w-4" />
            Two-Factor Authentication
          </Label>
          <p className="text-sm text-muted-foreground">Add an extra layer of security</p>
        </div>
        <Switch />
      </div>

      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">Session Timeout</h3>
          <p className="text-sm text-muted-foreground">Automatically log out after inactivity</p>
        </div>
        <Input type="number" defaultValue="30" className="max-w-[200px]" />
      </div>

      <div className="flex items-center justify-between py-4 border-b">
        <div className="space-y-0.5">
          <Label className="text-base font-semibold">Audit Logging</Label>
          <p className="text-sm text-muted-foreground">Track all system access and changes</p>
        </div>
        <Switch defaultChecked />
      </div>
    </div>
  );
}
