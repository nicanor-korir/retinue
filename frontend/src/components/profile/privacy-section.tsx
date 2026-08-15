"use client";

import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";

interface PrivacySectionProps {
  onSettingsChange?: (updates: Record<string, any>) => void;
}

export function PrivacySection({ onSettingsChange }: PrivacySectionProps) {
  const handleChange = () => {
    onSettingsChange?.({});
  };

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold mb-6">Privacy Settings</h2>
      <div className="space-y-4">
        {[
          { label: "Show online status", description: "Let others see when you're online", checked: true },
          { label: "Show last active time", description: "Display your last activity time", checked: true },
          { label: "Display email in directory", description: "Make your email visible to team", checked: false },
          { label: "Activity status broadcasting", description: "Share your current activity", checked: true },
        ].map((item, index) => (
          <div key={index} className="flex items-center justify-between p-4 border rounded-lg">
            <div>
              <Label className="text-base font-medium">{item.label}</Label>
              <p className="text-sm text-muted-foreground">{item.description}</p>
            </div>
            <Switch defaultChecked={item.checked} onCheckedChange={() => handleChange()} />
          </div>
        ))}
      </div>
    </Card>
  );
}
