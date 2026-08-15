"use client";

import { useState } from "react";
import { Card } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Monitor, Moon, Sun } from "lucide-react";

interface AppearanceSectionProps {
  onSettingsChange?: (updates: Record<string, any>) => void;
}

export function AppearanceSection({ onSettingsChange }: AppearanceSectionProps) {
  const [theme, setTheme] = useState<string>("dark");
  const [density, setDensity] = useState<string>("comfortable");
  const [fontSize, setFontSize] = useState<number[]>([14]);
  const [animations, setAnimations] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  const handleChange = () => {
    onSettingsChange?.({});
  };

  return (
    <Card className="p-6">
      <h2 className="text-xl font-semibold mb-6">Appearance Preferences</h2>
      
      <div className="space-y-8">
        {/* Theme Selection */}
        <div className="space-y-4">
          <div>
            <h3 className="text-base font-medium mb-1">Theme</h3>
            <p className="text-sm text-muted-foreground">
              Choose your preferred color scheme
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {[
              { value: "light", label: "Light Mode", icon: Sun },
              { value: "dark", label: "Dark Mode", icon: Moon },
              { value: "auto", label: "Auto (System)", icon: Monitor },
            ].map((option) => {
              const Icon = option.icon;
              return (
                <button
                  key={option.value}
                  onClick={() => {
                    setTheme(option.value);
                    handleChange();
                  }}
                  className={`relative flex flex-col items-center gap-3 p-4 border-2 rounded-lg transition-colors ${
                    theme === option.value
                      ? "border-primary bg-primary/5"
                      : "border-border hover:border-primary/50"
                  }`}
                >
                  {theme === option.value && (
                    <Badge className="absolute top-2 right-2" variant="default">
                      Active
                    </Badge>
                  )}
                  <Icon className="h-8 w-8" />
                  <span className="font-medium">{option.label}</span>
                </button>
              );
            })}
          </div>
        </div>

        {/* Display Density */}
        <div className="space-y-4">
          <div>
            <h3 className="text-base font-medium mb-1">Display Density</h3>
            <p className="text-sm text-muted-foreground">
              Adjust spacing and information density
            </p>
          </div>

          <Select value={density} onValueChange={(value) => {
            setDensity(value);
            handleChange();
          }}>
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="compact">Compact - More content, less spacing</SelectItem>
              <SelectItem value="comfortable">Comfortable - Balanced layout</SelectItem>
              <SelectItem value="spacious">Spacious - Maximum readability</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Font Size */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-medium mb-1">Font Size</h3>
              <p className="text-sm text-muted-foreground">
                Adjust text size for better readability
              </p>
            </div>
            <Badge variant="outline">{fontSize[0]}px</Badge>
          </div>

          <div className="space-y-2">
            <Slider
              value={fontSize}
              onValueChange={(value) => {
                setFontSize(value);
                handleChange();
              }}
              min={12}
              max={20}
              step={1}
              className="w-full"
            />
            <div className="flex justify-between text-xs text-muted-foreground">
              <span>Smaller</span>
              <span>Default (14px)</span>
              <span>Larger</span>
            </div>
          </div>

          {/* Preview */}
          <div className="p-4 border rounded-lg" style={{ fontSize: `${fontSize[0]}px` }}>
            <p className="font-medium mb-1">Preview Text</p>
            <p className="text-muted-foreground">
              This is how your text will appear at the selected size.
            </p>
          </div>
        </div>

        {/* Language */}
        <div className="space-y-4">
          <div>
            <h3 className="text-base font-medium mb-1">Language</h3>
            <p className="text-sm text-muted-foreground">
              Select your preferred language
            </p>
          </div>

          <Select defaultValue="en">
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="en">English</SelectItem>
              <SelectItem value="es">Español</SelectItem>
              <SelectItem value="fr">Français</SelectItem>
              <SelectItem value="de">Deutsch</SelectItem>
              <SelectItem value="ja">日本語</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Animations */}
        <div className="flex items-center justify-between py-4 border-t">
          <div className="space-y-0.5">
            <Label className="text-base font-medium">Enable Animations</Label>
            <p className="text-sm text-muted-foreground">
              Smooth transitions and motion effects
            </p>
          </div>
          <Switch
            checked={animations}
            onCheckedChange={(checked) => {
              setAnimations(checked);
              handleChange();
            }}
          />
        </div>

        {/* Sidebar Default State */}
        <div className="flex items-center justify-between py-4 border-t">
          <div className="space-y-0.5">
            <Label className="text-base font-medium">Sidebar Collapsed by Default</Label>
            <p className="text-sm text-muted-foreground">
              Start with sidebar minimized on page load
            </p>
          </div>
          <Switch
            checked={sidebarCollapsed}
            onCheckedChange={(checked) => {
              setSidebarCollapsed(checked);
              handleChange();
            }}
          />
        </div>

        {/* Default Landing Page */}
        <div className="space-y-4 border-t pt-4">
          <div>
            <h3 className="text-base font-medium mb-1">Default Landing Page</h3>
            <p className="text-sm text-muted-foreground">
              Page to show after login
            </p>
          </div>

          <Select defaultValue="dashboard">
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="dashboard">Dashboard</SelectItem>
              <SelectItem value="projects">Projects</SelectItem>
              <SelectItem value="tasks">Tasks</SelectItem>
              <SelectItem value="agents">Agents</SelectItem>
              <SelectItem value="messages">Messages</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
    </Card>
  );
}
