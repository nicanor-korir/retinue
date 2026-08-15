"use client";

import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Github, Trello, MessageSquare, CheckCircle2 } from "lucide-react";

interface IntegrationsSettingsProps {
  settings?: any;
  onSettingsChange?: (updates: any) => void;
}

export function IntegrationsSettings({ settings, onSettingsChange }: IntegrationsSettingsProps) {
  const integrations = [
    { name: "GitHub", icon: Github, connected: true, description: "Repository and issue tracking" },
    { name: "Jira", icon: Trello, connected: false, description: "Project management" },
    { name: "Slack", icon: MessageSquare, connected: true, description: "Team communication" },
  ];

  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">Connected Services</h3>
          <p className="text-sm text-muted-foreground">Manage external service integrations</p>
        </div>
        <div className="space-y-3">
          {integrations.map((integration) => {
            const Icon = integration.icon;
            return (
              <div key={integration.name} className="flex items-center justify-between p-4 border rounded-lg">
                <div className="flex items-center gap-3">
                  <Icon className="h-5 w-5 text-primary" />
                  <div>
                    <Label className="text-base">{integration.name}</Label>
                    <p className="text-sm text-muted-foreground">{integration.description}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {integration.connected ? (
                    <>
                      <Badge variant="success" className="flex items-center gap-1">
                        <CheckCircle2 className="h-3 w-3" />
                        Connected
                      </Badge>
                      <Button variant="outline" size="sm">Configure</Button>
                    </>
                  ) : (
                    <Button variant="outline" size="sm">Connect</Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">Webhook Configuration</h3>
          <p className="text-sm text-muted-foreground">Custom webhook endpoints</p>
        </div>
        <div className="space-y-2">
          <Input placeholder="https://your-endpoint.com/webhook" />
          <Button variant="outline" size="sm">Add Webhook</Button>
        </div>
      </div>

      <div className="flex items-center justify-between py-4 border-b">
        <div className="space-y-0.5">
          <Label className="text-base font-semibold">API Rate Limiting</Label>
          <p className="text-sm text-muted-foreground">Enable rate limits for external APIs</p>
        </div>
        <Switch defaultChecked />
      </div>
    </div>
  );
}
