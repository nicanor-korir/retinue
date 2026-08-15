"use client";

import { useState, useEffect } from "react";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Info } from "lucide-react";

interface AgentBehaviorSettingsProps {
  settings?: any;
  onSettingsChange?: (updates: any) => void;
}

export function AgentBehaviorSettings({ settings, onSettingsChange }: AgentBehaviorSettingsProps) {
  const [communicationStyle, setCommunicationStyle] = useState("technical");
  const [autoRetry, setAutoRetry] = useState(true);
  const [maxRetries, setMaxRetries] = useState<number[]>([3]);
  const [escalationTime, setEscalationTime] = useState<number[]>([30]);
  const [autonomyLevel, setAutonomyLevel] = useState<number[]>([70]);
  const [taskTimeout, setTaskTimeout] = useState("60");

  // Initialize from backend settings
  useEffect(() => {
    if (settings) {
      if (settings.communicationStyle !== undefined) setCommunicationStyle(settings.communicationStyle);
      if (settings.autoRetry !== undefined) setAutoRetry(settings.autoRetry);
      if (settings.maxRetries !== undefined) setMaxRetries([settings.maxRetries]);
      if (settings.escalationTime !== undefined) setEscalationTime([settings.escalationTime]);
      if (settings.autonomyLevel !== undefined) setAutonomyLevel([settings.autonomyLevel]);
      if (settings.taskTimeout !== undefined) setTaskTimeout(settings.taskTimeout.toString());
    }
  }, [settings]);

  const handleChange = (updates: Record<string, any>) => {
    onSettingsChange?.(updates);
  };

  return (
    <div className="space-y-8">
      {/* Communication Style */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">Communication Style</h3>
          <p className="text-sm text-muted-foreground">
            How agents communicate with users and each other
          </p>
        </div>

        <Select value={communicationStyle} onValueChange={(value) => {
          setCommunicationStyle(value);
          handleChange({ communicationStyle: value });
        }}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="formal">Formal - Professional and structured</SelectItem>
            <SelectItem value="casual">Casual - Friendly and conversational</SelectItem>
            <SelectItem value="technical">Technical - Precise and detailed (Recommended)</SelectItem>
            <SelectItem value="concise">Concise - Brief and to the point</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Auto-Retry Settings */}
      <div className="space-y-4 p-4 border rounded-lg">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label className="text-base font-semibold">Auto-Retry Failed Tasks</Label>
            <p className="text-sm text-muted-foreground">
              Automatically retry when tasks fail
            </p>
          </div>
          <Switch
            checked={autoRetry}
            onCheckedChange={(checked) => {
              setAutoRetry(checked);
              handleChange({ autoRetry: checked });
            }}
          />
        </div>

        {autoRetry && (
          <div className="space-y-4 pt-3 border-t">
            <div>
              <div className="flex items-center justify-between mb-2">
                <Label className="text-sm">Maximum Retry Attempts</Label>
                <Badge variant="outline">{maxRetries[0]}</Badge>
              </div>
              <Slider
                value={maxRetries}
                onValueChange={(value) => {
                  setMaxRetries(value);
                  handleChange({ maxRetries: value[0] });
                }}
                min={1}
                max={10}
                step={1}
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground mt-1">
                <span>1 retry</span>
                <span>10 retries</span>
              </div>
            </div>

            <div className="flex items-center gap-2 p-3 bg-muted/50 rounded-lg text-sm">
              <Info className="h-4 w-4 text-muted-foreground flex-shrink-0" />
              <p className="text-muted-foreground">
                Retry attempts use exponential backoff (1s, 2s, 4s, 8s, etc.)
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Escalation Settings */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">Escalation Triggers</h3>
          <p className="text-sm text-muted-foreground">
            When agents should escalate to human review
          </p>
        </div>

        <div className="space-y-4">
          <div>
            <div className="flex items-center justify-between mb-2">
              <Label>Time Without Progress</Label>
              <Badge variant="outline">{escalationTime[0]} minutes</Badge>
            </div>
            <Slider
              value={escalationTime}
              onValueChange={(value) => {
                setEscalationTime(value);
                handleChange({ escalationTime: value[0] });
              }}
              min={5}
              max={120}
              step={5}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground mt-1">
              <span>5 min</span>
              <span>120 min</span>
            </div>
          </div>

          <div className="space-y-3 p-4 bg-muted/30 rounded-lg">
            <Label className="text-sm font-medium">Escalate on:</Label>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label className="text-sm font-normal">Complexity threshold exceeded</Label>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <Label className="text-sm font-normal">Error count exceeds limit</Label>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <Label className="text-sm font-normal">Uncertain decision required</Label>
                <Switch defaultChecked />
              </div>
              <div className="flex items-center justify-between">
                <Label className="text-sm font-normal">Security-sensitive operation</Label>
                <Switch defaultChecked />
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Agent Autonomy */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold mb-1">Agent Autonomy Level</h3>
            <p className="text-sm text-muted-foreground">
              How much agents can do without approval
            </p>
          </div>
          <Badge variant="outline">{autonomyLevel[0]}%</Badge>
        </div>

        <Slider
          value={autonomyLevel}
          onValueChange={(value) => {
            setAutonomyLevel(value);
            handleChange({ autonomyLevel: value[0] });
          }}
          min={0}
          max={100}
          step={10}
          className="w-full"
        />
        <div className="flex justify-between text-xs text-muted-foreground">
          <span>Low</span>
          <span>Medium</span>
          <span>High</span>
        </div>

        <div className="p-3 bg-muted/50 rounded-lg text-sm">
          <p className="font-medium mb-1">
            {autonomyLevel[0] < 30 ? "Low Autonomy" : autonomyLevel[0] > 70 ? "High Autonomy" : "Medium Autonomy"}
          </p>
          <p className="text-muted-foreground">
            {autonomyLevel[0] < 30 && "Requires approval for most actions. Best for critical systems."}
            {autonomyLevel[0] >= 30 && autonomyLevel[0] <= 70 && "Balanced approach with selective approvals. Recommended for most use cases."}
            {autonomyLevel[0] > 70 && "High independence with minimal approvals. Suitable for trusted operations."}
          </p>
        </div>
      </div>

      {/* Task Timeout */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">Task Timeout Duration</h3>
          <p className="text-sm text-muted-foreground">
            Maximum time before a task is marked as timed out
          </p>
        </div>

        <div className="flex gap-2">
          <Input
            type="number"
            value={taskTimeout}
            onChange={(e) => {
              setTaskTimeout(e.target.value);
              handleChange({ taskTimeout: e.target.value });
            }}
            className="max-w-[120px]"
          />
          <Select defaultValue="minutes">
            <SelectTrigger className="max-w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="minutes">Minutes</SelectItem>
              <SelectItem value="hours">Hours</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Agent Collaboration */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">Agent Collaboration</h3>
          <p className="text-sm text-muted-foreground">
            When agents should communicate with each other
          </p>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between p-3 border rounded-lg">
            <Label className="text-sm">Shared task coordination</Label>
            <Switch defaultChecked />
          </div>
          <div className="flex items-center justify-between p-3 border rounded-lg">
            <Label className="text-sm">Knowledge sharing</Label>
            <Switch defaultChecked />
          </div>
          <div className="flex items-center justify-between p-3 border rounded-lg">
            <Label className="text-sm">Cross-agent learning</Label>
            <Switch />
          </div>
          <div className="flex items-center justify-between p-3 border rounded-lg">
            <Label className="text-sm">Automatic handoffs</Label>
            <Switch defaultChecked />
          </div>
        </div>
      </div>

      {/* Default Priority */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">Default Task Priority</h3>
          <p className="text-sm text-muted-foreground">
            Priority level for new tasks
          </p>
        </div>

        <Select defaultValue="medium">
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="low">Low - Can wait</SelectItem>
            <SelectItem value="medium">Medium - Normal priority (Default)</SelectItem>
            <SelectItem value="high">High - Important</SelectItem>
            <SelectItem value="urgent">Urgent - Immediate attention</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
