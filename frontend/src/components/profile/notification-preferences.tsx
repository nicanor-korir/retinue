"use client";

import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

interface NotificationPreferencesProps {
  onSettingsChange?: (updates: Record<string, any>) => void;
}

export function NotificationPreferences({ onSettingsChange }: NotificationPreferencesProps) {
  const handleChange = () => {
    onSettingsChange?.({});
  };

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold mb-6">Notification Preferences</h2>

      <div className="space-y-6">
        <div className="space-y-4">
          <h3 className="text-base font-medium">Email Notifications</h3>
          <Select defaultValue="realtime" onValueChange={() => handleChange()}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="realtime">Real-time</SelectItem>
              <SelectItem value="daily">Daily Digest</SelectItem>
              <SelectItem value="weekly">Weekly Summary</SelectItem>
              <SelectItem value="never">Never</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-3">
          {[
            { label: "Task assignments", checked: true },
            { label: "Task completions", checked: true },
            { label: "Mentions in messages", checked: true },
            { label: "Agent escalations", checked: true },
            { label: "Project updates", checked: false },
            { label: "System announcements", checked: true },
          ].map((item, index) => (
            <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
              <Label className="text-sm">{item.label}</Label>
              <Switch defaultChecked={item.checked} onCheckedChange={() => handleChange()} />
            </div>
          ))}
        </div>

        <div className="flex items-center justify-between py-4 border-t">
          <div className="space-y-0.5">
            <Label className="text-base font-medium">Desktop Push Notifications</Label>
            <p className="text-sm text-muted-foreground">Browser notifications</p>
          </div>
          <Switch defaultChecked onCheckedChange={() => handleChange()} />
        </div>

        <div className="flex items-center justify-between py-4 border-t">
          <div className="space-y-0.5">
            <Label className="text-base font-medium">Notification Sounds</Label>
            <p className="text-sm text-muted-foreground">Play sound for alerts</p>
          </div>
          <Switch defaultChecked onCheckedChange={() => handleChange()} />
        </div>
      </div>
    </Card>
  );
}
