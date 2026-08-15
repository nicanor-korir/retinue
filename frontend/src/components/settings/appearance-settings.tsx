"use client";

import { useState, useEffect } from "react";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Monitor, Moon, Sun, Info } from "lucide-react";

interface AppearanceSettingsProps {
  settings?: any;
  onSettingsChange?: (updates: any) => void;
}

export function AppearanceSettings({ settings, onSettingsChange }: AppearanceSettingsProps) {
  const [theme, setTheme] = useState<string>("dark");
  const [density, setDensity] = useState<string>("comfortable");
  const [fontSize, setFontSize] = useState<number[]>([14]);
  const [animations, setAnimations] = useState(true);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);

  // Initialize from backend settings
  useEffect(() => {
    if (settings) {
      if (settings.theme !== undefined) setTheme(settings.theme);
      if (settings.density !== undefined) setDensity(settings.density);
      if (settings.fontSize !== undefined) setFontSize([settings.fontSize]);
      if (settings.animations !== undefined) setAnimations(settings.animations);
      if (settings.sidebarCollapsed !== undefined) setSidebarCollapsed(settings.sidebarCollapsed);
    }
  }, [settings]);

  const handleChange = (updates: Record<string, any>) => {
    onSettingsChange?.(updates);
  };

  return (
    <div className="space-y-8">
      {/* Theme Selection */}
      <div className="space-y-4">
        <div>
          <h3 className="text-lg font-semibold mb-1">Theme</h3>
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
                  handleChange({ theme: option.value });
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
          <h3 className="text-lg font-semibold mb-1">Display Density</h3>
          <p className="text-sm text-muted-foreground">
            Adjust spacing and information density
          </p>
        </div>

        <Select value={density} onValueChange={(value) => {
          setDensity(value);
          handleChange({ density: value });
        }}>
          <SelectTrigger>
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="compact">Compact - More content, less spacing</SelectItem>
            <SelectItem value="comfortable">Comfortable - Balanced layout (Recommended)</SelectItem>
            <SelectItem value="spacious">Spacious - Maximum readability</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Font Size */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-semibold mb-1">Font Size</h3>
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
              handleChange({ fontSize: value[0] });
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
            This is how your text will appear at the selected size. The quick brown fox jumps over the lazy dog.
          </p>
        </div>
      </div>

      {/* Animations */}
      <div className="flex items-center justify-between py-4 border-b">
        <div className="space-y-0.5">
          <Label className="text-base font-semibold">Enable Animations</Label>
          <p className="text-sm text-muted-foreground">
            Smooth transitions and motion effects
          </p>
        </div>
        <Switch
          checked={animations}
          onCheckedChange={(checked) => {
            setAnimations(checked);
            handleChange({ animations: checked });
          }}
        />
      </div>

      {/* Sidebar Default State */}
      <div className="flex items-center justify-between py-4 border-b">
        <div className="space-y-0.5">
          <Label className="text-base font-semibold">Sidebar Collapsed by Default</Label>
          <p className="text-sm text-muted-foreground">
            Start with sidebar minimized on page load
          </p>
        </div>
        <Switch
          checked={sidebarCollapsed}
          onCheckedChange={(checked) => {
            setSidebarCollapsed(checked);
            handleChange({ sidebarCollapsed: checked });
          }}
        />
      </div>

      {/* Info Box */}
      <div className="flex gap-3 p-4 bg-blue-500/10 border border-blue-500/20 rounded-lg">
        <Info className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
        <div className="text-sm">
          <p className="font-medium text-blue-500 mb-1">Theme Customization</p>
          <p className="text-muted-foreground">
            Theme changes apply immediately. Some settings may require a page refresh to take full effect.
          </p>
        </div>
      </div>
    </div>
  );
}
