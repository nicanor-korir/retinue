"use client";

import { useState, useEffect } from "react";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Mail, MessageSquare, Webhook, Volume2, Bell } from "lucide-react";

interface NotificationsSettingsProps {
  settings?: any;
  onSettingsChange?: (updates: any) => void;
}

export function NotificationsSettings({ settings, onSettingsChange }: NotificationsSettingsProps) {
  const [emailEnabled, setEmailEnabled] = useState(true);
  const [slackEnabled, setSlackEnabled] = useState(false);
  const [frequency, setFrequency] = useState("realtime");

  // Initialize from backend settings
  useEffect(() => {
    if (settings) {
      if (settings.emailEnabled !== undefined) setEmailEnabled(settings.emailEnabled);
      if (settings.slackEnabled !== undefined) setSlackEnabled(settings.slackEnabled);
      if (settings.frequency !== undefined) setFrequency(settings.frequency);
    }
  }, [settings]);

  const handleChange = (updates: Record<string, any>) => {
    onSettingsChange?.(updates);
  };

  return (
    <div className="space-y-8">
      {/* Notification Channels */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">Notification Channels</h3>
          <p className="text-sm text-muted-foreground">
            Choose how you want to receive notifications
          </p>
        </div>

        <div className="space-y-3">
          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="flex items-center gap-3">
              <Bell className="h-5 w-5 text-primary" />
              <div>
                <Label className="text-base">In-App Notifications</Label>
                <p className="text-sm text-muted-foreground">Browser notifications</p>
              </div>
            </div>
            <Switch defaultChecked />
          </div>

          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="flex items-center gap-3">
              <Mail className="h-5 w-5 text-primary" />
              <div>
                <Label className="text-base">Email Alerts</Label>
                <p className="text-sm text-muted-foreground">Send notifications to email</p>
              </div>
            </div>
            <Switch
              checked={emailEnabled}
              onCheckedChange={(checked) => {
                setEmailEnabled(checked);
                handleChange({ emailEnabled: checked });
              }}
            />
          </div>

          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="flex items-center gap-3">
              <MessageSquare className="h-5 w-5 text-primary" />
              <div>
                <Label className="text-base">Slack Integration</Label>
                <p className="text-sm text-muted-foreground">Post to Slack channel</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {slackEnabled && <Badge variant="success">Connected</Badge>}
              <Switch
                checked={slackEnabled}
                onCheckedChange={(checked) => {
                  setSlackEnabled(checked);
                  handleChange({ slackEnabled: checked });
                }}
              />
            </div>
          </div>

          <div className="flex items-center justify-between p-4 border rounded-lg">
            <div className="flex items-center gap-3">
              <Webhook className="h-5 w-5 text-primary" />
              <div>
                <Label className="text-base">Webhook Integrations</Label>
                <p className="text-sm text-muted-foreground">Send to custom endpoints</p>
              </div>
            </div>
            <Button variant="outline" size="sm">Configure</Button>
          </div>
        </div>
      </div>

      {/* Alert Frequency */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">Alert Frequency</h3>
          <p className="text-sm text-muted-foreground">
            How often to receive notifications
          </p>
        </div>

        <Select value={frequency} onValueChange={(value) => {
          setFrequency(value);
          handleChange({ frequency: value });
        }}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="realtime">Real-time - Instant notifications</SelectItem>
            <SelectItem value="hourly">Hourly Digest - Batched every hour</SelectItem>
            <SelectItem value="daily">Daily Digest - Once per day</SelectItem>
            <SelectItem value="custom">Custom Schedule</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Alert Types */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">Alert Types</h3>
          <p className="text-sm text-muted-foreground">
            Choose which events trigger notifications
          </p>
        </div>

        <div className="grid gap-3">
          {[
            { label: "System status changes", description: "Service up/down events" },
            { label: "Agent escalations", description: "When agents need help", checked: true },
            { label: "Task completions", description: "Successful task finishes", checked: true },
            { label: "Stuck tasks", description: "Tasks with no progress", checked: true },
            { label: "Health alerts", description: "System health issues" },
            { label: "Security events", description: "Security-related notifications", checked: true },
            { label: "Performance warnings", description: "Slow response times" },
            { label: "Error notifications", description: "System errors" },
          ].map((item, index) => (
            <div key={index} className="flex items-center justify-between p-3 border rounded-lg">
              <div>
                <Label className="text-sm font-medium">{item.label}</Label>
                <p className="text-xs text-muted-foreground">{item.description}</p>
              </div>
              <Switch defaultChecked={item.checked} />
            </div>
          ))}
        </div>
      </div>

      {/* Sound Notifications */}
      <div className="flex items-center justify-between py-4 border-b">
        <div className="space-y-0.5">
          <Label className="text-base font-semibold flex items-center gap-2">
            <Volume2 className="h-4 w-4" />
            Sound Notifications
          </Label>
          <p className="text-sm text-muted-foreground">
            Play sound for important alerts
          </p>
        </div>
        <Switch defaultChecked />
      </div>

      {/* Do Not Disturb */}
      <div className="space-y-4 p-4 border rounded-lg">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label className="text-base font-semibold">Do Not Disturb Schedule</Label>
            <p className="text-sm text-muted-foreground">
              Silence notifications during specific hours
            </p>
          </div>
          <Switch />
        </div>

        <div className="grid grid-cols-2 gap-4 pt-3 border-t">
          <div className="space-y-2">
            <Label className="text-sm">Start Time</Label>
            <Input type="time" defaultValue="22:00" />
          </div>
          <div className="space-y-2">
            <Label className="text-sm">End Time</Label>
            <Input type="time" defaultValue="08:00" />
          </div>
        </div>
      </div>
    </div>
  );
}
