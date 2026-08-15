"use client";

import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Github, MessageSquare, Mail } from "lucide-react";

interface ConnectedAccountsProps {
  onSettingsChange?: (updates: Record<string, any>) => void;
}

export function ConnectedAccounts({ onSettingsChange }: ConnectedAccountsProps) {
  const accounts = [
    { name: "GitHub", icon: Github, connected: true, email: "john.doe@github.com" },
    { name: "Slack", icon: MessageSquare, connected: true, email: "john.doe@workspace.slack.com" },
    { name: "Google", icon: Mail, connected: false, email: null },
  ];

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold mb-6">Connected Accounts</h2>
      <div className="space-y-4">
        {accounts.map((account, index) => {
          const Icon = account.icon;
          return (
            <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
              <div className="flex items-center gap-3">
                <Icon className="h-8 w-8 text-primary" />
                <div>
                  <div className="font-medium">{account.name}</div>
                  {account.email && (
                    <div className="text-sm text-muted-foreground">{account.email}</div>
                  )}
                </div>
              </div>
              <div className="flex items-center gap-2">
                {account.connected ? (
                  <>
                    <Badge variant="success">Connected</Badge>
                    <Button variant="outline" size="sm" onClick={onSettingsChange}>
                      Disconnect
                    </Button>
                  </>
                ) : (
                  <Button variant="outline" size="sm" onClick={onSettingsChange}>
                    Connect
                  </Button>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
