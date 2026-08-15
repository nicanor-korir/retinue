"use client";

import { useState, useEffect } from "react";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Card } from "@/components/ui/card";
import { Sparkles, Info, DollarSign, Zap, AlertCircle } from "lucide-react";

interface LLMConfigSettingsProps {
  settings?: any;
  onSettingsChange?: (updates: any) => void;
}

const MODELS = [
  {
    id: "gpt-4",
    name: "GPT-4",
    provider: "OpenAI",
    tokens: "8K context",
    cost: "$0.03/1K tokens",
    capabilities: ["Advanced reasoning", "Code generation", "Analysis"],
  },
  {
    id: "gpt-4-turbo",
    name: "GPT-4 Turbo",
    provider: "OpenAI",
    tokens: "128K context",
    cost: "$0.01/1K tokens",
    capabilities: ["Extended context", "Fast", "Cost-effective"],
  },
  {
    id: "claude-sonnet-4.5",
    name: "Claude Sonnet 4.5",
    provider: "Anthropic",
    tokens: "200K context",
    cost: "$0.015/1K tokens",
    capabilities: ["Large context", "Reasoning", "Creative writing"],
    recommended: true,
  },
  {
    id: "claude-opus",
    name: "Claude Opus",
    provider: "Anthropic",
    tokens: "200K context",
    cost: "$0.075/1K tokens",
    capabilities: ["Best performance", "Complex tasks", "High accuracy"],
  },
];

export function LLMConfigSettings({ settings, onSettingsChange }: LLMConfigSettingsProps) {
  const [selectedModel, setSelectedModel] = useState("claude-sonnet-4.5");
  const [temperature, setTemperature] = useState<number[]>([0.7]);
  const [maxTokens, setMaxTokens] = useState<number[]>([2000]);
  const [showThinking, setShowThinking] = useState(true);
  const [showConfidence, setShowConfidence] = useState(false);
  const [contextStrategy, setContextStrategy] = useState("full");

  // Initialize from backend settings
  useEffect(() => {
    if (settings) {
      if (settings.selectedModel !== undefined) setSelectedModel(settings.selectedModel);
      if (settings.temperature !== undefined) setTemperature([settings.temperature]);
      if (settings.maxTokens !== undefined) setMaxTokens([settings.maxTokens]);
      if (settings.showThinking !== undefined) setShowThinking(settings.showThinking);
      if (settings.showConfidence !== undefined) setShowConfidence(settings.showConfidence);
      if (settings.contextStrategy !== undefined) setContextStrategy(settings.contextStrategy);
    }
  }, [settings]);

  const handleChange = (updates: Record<string, any>) => {
    onSettingsChange?.(updates);
  };

  const estimatedCost = ((maxTokens[0] / 1000) * 0.015).toFixed(4);

  return (
    <div className="space-y-8">
      {/* Model Selection */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">Model Selection</h3>
          <p className="text-sm text-muted-foreground">
            Choose the AI model for agent operations
          </p>
        </div>

        <div className="grid gap-4">
          {MODELS.map((model) => (
            <Card
              key={model.id}
              className={`p-4 cursor-pointer transition-all ${
                selectedModel === model.id
                  ? "border-primary bg-primary/5 ring-2 ring-primary"
                  : "hover:border-primary/50"
              }`}
              onClick={() => {
                setSelectedModel(model.id);
                handleChange({ selectedModel: model.id });
              }}
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="h-5 w-5 text-primary" />
                  <div>
                    <h4 className="font-semibold">{model.name}</h4>
                    <p className="text-sm text-muted-foreground">{model.provider}</p>
                  </div>
                </div>
                <div className="flex gap-2">
                  {model.recommended && (
                    <Badge variant="default">Recommended</Badge>
                  )}
                  {selectedModel === model.id && (
                    <Badge variant="outline">Active</Badge>
                  )}
                </div>
              </div>

              <div className="grid grid-cols-2 gap-4 text-sm mb-3">
                <div>
                  <span className="text-muted-foreground">Context:</span>
                  <span className="ml-2 font-medium">{model.tokens}</span>
                </div>
                <div>
                  <span className="text-muted-foreground">Cost:</span>
                  <span className="ml-2 font-medium">{model.cost}</span>
                </div>
              </div>

              <div className="flex flex-wrap gap-2">
                {model.capabilities.map((cap) => (
                  <Badge key={cap} variant="secondary" className="text-xs">
                    {cap}
                  </Badge>
                ))}
              </div>
            </Card>
          ))}
        </div>
      </div>

      {/* Temperature Control */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold mb-1">Temperature</h3>
            <p className="text-sm text-muted-foreground">
              Controls randomness in responses (0 = focused, 2 = creative)
            </p>
          </div>
          <Badge variant="outline">{temperature[0].toFixed(1)}</Badge>
        </div>

        <div className="space-y-2">
          <Slider
            value={temperature}
            onValueChange={(value) => {
              setTemperature(value);
              handleChange({ temperature: value[0] });
            }}
            min={0}
            max={2}
            step={0.1}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Focused (0.0)</span>
            <span>Balanced (1.0)</span>
            <span>Creative (2.0)</span>
          </div>
        </div>

        <div className="p-3 bg-muted/50 rounded-lg text-sm">
          <p className="font-medium mb-1">Current Setting: {temperature[0] < 0.5 ? "Focused" : temperature[0] > 1.5 ? "Creative" : "Balanced"}</p>
          <p className="text-muted-foreground">
            {temperature[0] < 0.5 && "More deterministic and consistent responses. Best for code generation."}
            {temperature[0] >= 0.5 && temperature[0] <= 1.5 && "Balanced creativity and consistency. Recommended for most tasks."}
            {temperature[0] > 1.5 && "More varied and creative responses. Good for brainstorming."}
          </p>
        </div>
      </div>

      {/* Max Tokens */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold mb-1">Max Tokens</h3>
            <p className="text-sm text-muted-foreground">
              Maximum response length
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">{maxTokens[0]} tokens</Badge>
            <Badge variant="secondary" className="flex items-center gap-1">
              <DollarSign className="h-3 w-3" />
              ~${estimatedCost}
            </Badge>
          </div>
        </div>

        <div className="space-y-2">
          <Slider
            value={maxTokens}
            onValueChange={(value) => {
              setMaxTokens(value);
              handleChange({ maxTokens: value[0] });
            }}
            min={500}
            max={8000}
            step={100}
            className="w-full"
          />
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>Short (500)</span>
            <span>Medium (2000)</span>
            <span>Long (8000)</span>
          </div>
        </div>
      </div>

      {/* Show Thinking Process */}
      <div className="space-y-4 p-4 border rounded-lg">
        <div className="flex items-center justify-between">
          <div className="space-y-0.5">
            <Label className="text-base font-semibold flex items-center gap-2">
              Show Thinking Process
              <Badge variant="outline" className="text-xs">Glass Box AI</Badge>
            </Label>
            <p className="text-sm text-muted-foreground">
              Display internal reasoning and thought process
            </p>
          </div>
          <Switch
            checked={showThinking}
            onCheckedChange={(checked) => {
              setShowThinking(checked);
              handleChange({ showThinking: checked });
            }}
          />
        </div>

        {showThinking && (
          <div className="space-y-3 pt-3 border-t">
            <div className="flex items-center justify-between">
              <Label className="text-sm">Show step-by-step breakdown</Label>
              <Switch defaultChecked />
            </div>
            <div className="flex items-center justify-between">
              <Label className="text-sm">Include confidence scores</Label>
              <Switch
                checked={showConfidence}
                onCheckedChange={setShowConfidence}
              />
            </div>
            <div className="flex items-center justify-between">
              <Label className="text-sm">Display reasoning chains</Label>
              <Switch defaultChecked />
            </div>
          </div>
        )}
      </div>

      {/* Context Strategy */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">Context Management</h3>
          <p className="text-sm text-muted-foreground">
            How to handle conversation history
          </p>
        </div>

        <Select value={contextStrategy} onValueChange={(value) => {
          setContextStrategy(value);
          handleChange({ contextStrategy: value });
        }}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="full">Full History - Keep all context</SelectItem>
            <SelectItem value="summary">Summarization - Compress old messages</SelectItem>
            <SelectItem value="sliding">Sliding Window - Keep recent messages only</SelectItem>
            <SelectItem value="hybrid">Hybrid - Smart combination</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Response Format */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">Response Format</h3>
          <p className="text-sm text-muted-foreground">
            Preferred output structure
          </p>
        </div>

        <Select defaultValue="hybrid">
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="json">Structured JSON</SelectItem>
            <SelectItem value="natural">Natural Language</SelectItem>
            <SelectItem value="hybrid">Hybrid (Recommended)</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Warning */}
      <div className="flex gap-3 p-4 bg-yellow-500/10 border border-yellow-500/20 rounded-lg">
        <AlertCircle className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-0.5" />
        <div className="text-sm">
          <p className="font-medium text-yellow-500 mb-1">Cost Considerations</p>
          <p className="text-muted-foreground">
            Higher token limits and more powerful models increase costs. Monitor usage regularly to stay within budget.
          </p>
        </div>
      </div>
    </div>
  );
}
