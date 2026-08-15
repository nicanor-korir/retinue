"use client";

import { useState, useMemo } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useSystemSettings } from "@/hooks/useSettings";
import { Card } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Search,
  Brain,
  Bot,
  Bell,
  Shield,
  Plug,
  Gauge,
  FileText,
  Database,
  Settings as SettingsIcon,
  Save,
  RotateCcw,
  X,
} from "lucide-react";

import { LLMConfigSettings } from "@/components/settings/llm-config-settings";
import { AgentBehaviorSettings } from "@/components/settings/agent-behavior-settings";
import { NotificationsSettings } from "@/components/settings/notifications-settings";
import { SecuritySettings } from "@/components/settings/security-settings";
import { IntegrationsSettings } from "@/components/settings/integrations-settings";
import { PerformanceSettings } from "@/components/settings/performance-settings";
import { LoggingSettings } from "@/components/settings/logging-settings";
import { BackupSettings } from "@/components/settings/backup-settings";
import { AdvancedSettings } from "@/components/settings/advanced-settings";
import { ConfirmDialog } from "@/components/settings/confirm-dialog";

type SettingCategory = {
  id: string;
  name: string;
  description: string;
  icon: any;
  component: React.ComponentType<{ 
    settings?: any;
    onSettingsChange?: (updates: any) => void;
  }>;
  tags?: string[];
};

const categories: SettingCategory[] = [
  {
    id: "llm",
    name: "LLM Configuration",
    description: "System-wide AI model settings and behavior",
    icon: Brain,
    component: LLMConfigSettings,
    tags: ["model", "gpt", "claude", "temperature", "tokens", "ai"],
  },
  {
    id: "agent-behavior",
    name: "Agent Behavior & Policies",
    description: "Default agent behavior and escalation policies",
    icon: Bot,
    component: AgentBehaviorSettings,
    tags: ["agents", "automation", "escalation", "retry", "policies"],
  },
  {
    id: "notifications",
    name: "System Notifications & Alerts",
    description: "Alert routing and system-wide notifications",
    icon: Bell,
    component: NotificationsSettings,
    tags: ["email", "alerts", "webhook", "slack", "routing"],
  },
  {
    id: "integrations",
    name: "Integration & APIs",
    description: "External service connections and API settings",
    icon: Plug,
    component: IntegrationsSettings,
    tags: ["github", "jira", "slack", "api", "webhook"],
  },
  {
    id: "security",
    name: "Security & Compliance",
    description: "System security, compliance, and data policies",
    icon: Shield,
    component: SecuritySettings,
    tags: ["api", "security", "compliance", "privacy", "gdpr"],
  },
  {
    id: "performance",
    name: "Performance & Resources",
    description: "Resource allocation and system optimization",
    icon: Gauge,
    component: PerformanceSettings,
    tags: ["performance", "caching", "resources", "scaling"],
  },
  {
    id: "logging",
    name: "Logging & Debugging",
    description: "System logs and debugging configuration",
    icon: FileText,
    component: LoggingSettings,
    tags: ["logs", "debug", "trace", "monitoring"],
  },
  {
    id: "backup",
    name: "Backup & Data Management",
    description: "System backups and data management",
    icon: Database,
    component: BackupSettings,
    tags: ["backup", "export", "import", "data", "disaster-recovery"],
  },
  {
    id: "advanced",
    name: "Advanced System Settings",
    description: "Experimental features and system overrides",
    icon: SettingsIcon,
    component: AdvancedSettings,
    tags: ["experimental", "beta", "developer", "advanced"],
  },
];

export default function SettingsPage() {
  const [selectedCategory, setSelectedCategory] = useState<string>("llm");
  const [searchQuery, setSearchQuery] = useState("");
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);
  const [pendingCategory, setPendingCategory] = useState<string | null>(null);
  const [showResetDialog, setShowResetDialog] = useState(false);
  const [localChanges, setLocalChanges] = useState<Record<string, any>>({});

  // Fetch settings from backend
  const { settings, isLoading, updateSettings, isUpdating, error } = useSystemSettings();

  // Filter categories based on search
  const filteredCategories = useMemo(() => {
    if (!searchQuery) return categories;
    
    const query = searchQuery.toLowerCase();
    return categories.filter(
      (cat) =>
        cat.name.toLowerCase().includes(query) ||
        cat.description.toLowerCase().includes(query) ||
        cat.tags?.some((tag) => tag.toLowerCase().includes(query))
    );
  }, [searchQuery]);

  // Handle category change with unsaved changes check
  const handleCategoryChange = (categoryId: string) => {
    if (hasUnsavedChanges) {
      setPendingCategory(categoryId);
      setShowConfirmDialog(true);
    } else {
      setSelectedCategory(categoryId);
    }
  };

  // Confirm category change
  const confirmCategoryChange = () => {
    if (pendingCategory) {
      setSelectedCategory(pendingCategory);
      setPendingCategory(null);
      setHasUnsavedChanges(false);
      setLocalChanges({});
    }
    setShowConfirmDialog(false);
  };

  // Handle setting changes from child components
  const handleSettingChange = (updates: Record<string, any>) => {
    console.log("Settings changed:", updates);
    setLocalChanges((prev) => ({ ...prev, ...updates }));
    setHasUnsavedChanges(true);
  };

  // Handle save
  const handleSave = () => {
    console.log("Save clicked. Local changes:", localChanges);
    console.log("Has unsaved changes:", hasUnsavedChanges);
    console.log("Changes count:", Object.keys(localChanges).length);
    
    if (Object.keys(localChanges).length > 0) {
      console.log("Calling updateSettings with:", localChanges);
      updateSettings(localChanges);
      setLocalChanges({});
      setHasUnsavedChanges(false);
    } else {
      console.log("No changes to save");
    }
  };

  // Handle reset
  const handleReset = () => {
    setShowResetDialog(true);
  };

  const confirmReset = () => {
    // Reset to server values
    setLocalChanges({});
    setHasUnsavedChanges(false);
    setShowResetDialog(false);
  };

  const currentCategory = categories.find((c) => c.id === selectedCategory);
  const CurrentComponent = currentCategory?.component;

  // Show loading state
  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-[600px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading settings...</p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  // Show error state
  if (error) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-[600px]">
          <div className="text-center">
            <p className="text-destructive font-medium mb-2">Error loading settings</p>
            <p className="text-sm text-muted-foreground">
              {error instanceof Error ? error.message : "Unknown error"}
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout>
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center gap-3">
              <h1 className="text-3xl font-bold tracking-tight">System Settings</h1>
              <Badge variant="outline" className="text-xs">Admin Only</Badge>
            </div>
            <p className="text-muted-foreground">
              Configure system-wide settings and operational policies
            </p>
          </div>
          {hasUnsavedChanges && (
            <Badge variant="warning" className="animate-pulse">
              Unsaved Changes
            </Badge>
          )}
        </div>

        {/* Search Bar */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search settings..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10"
          />
          {searchQuery && (
            <Button
              variant="ghost"
              size="sm"
              className="absolute right-2 top-1/2 -translate-y-1/2 h-7 w-7 p-0"
              onClick={() => setSearchQuery("")}
            >
              <X className="h-4 w-4" />
            </Button>
          )}
        </div>

        {/* Main Content */}
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
          {/* Sidebar */}
          <div className="lg:col-span-1">
            <Card className="p-2">
              <ScrollArea className="h-[calc(100vh-300px)]">
                <div className="space-y-1">
                  {filteredCategories.map((category) => {
                    const Icon = category.icon;
                    const isSelected = category.id === selectedCategory;

                    return (
                      <button
                        key={category.id}
                        onClick={() => handleCategoryChange(category.id)}
                        className={`w-full flex items-start gap-3 p-3 rounded-lg text-left transition-colors ${
                          isSelected
                            ? "bg-primary text-primary-foreground"
                            : "hover:bg-accent"
                        }`}
                      >
                        <Icon className="h-5 w-5 mt-0.5 flex-shrink-0" />
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-sm">{category.name}</div>
                          <div
                            className={`text-xs mt-0.5 ${
                              isSelected
                                ? "text-primary-foreground/80"
                                : "text-muted-foreground"
                            }`}
                          >
                            {category.description}
                          </div>
                        </div>
                      </button>
                    );
                  })}
                </div>
              </ScrollArea>
            </Card>
          </div>

          {/* Content Area */}
          <div className="lg:col-span-3">
            <Card className="p-6">
              <div className="space-y-6">
                {/* Breadcrumb */}
                <div className="flex items-center text-sm text-muted-foreground">
                  <span>Settings</span>
                  <span className="mx-2">/</span>
                  <span className="text-foreground font-medium">
                    {currentCategory?.name}
                  </span>
                </div>

                {/* Category Content */}
                <div className="border-t pt-6">
                  {CurrentComponent && (
                    <CurrentComponent
                      settings={settings}
                      onSettingsChange={handleSettingChange}
                    />
                  )}
                </div>
              </div>
            </Card>

            {/* Sticky Action Bar */}
            <div className="sticky bottom-0 mt-6 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-t p-4 rounded-lg shadow-lg">
              <div className="flex items-center justify-between">
                <div className="text-sm text-muted-foreground">
                  {hasUnsavedChanges
                    ? "You have unsaved changes"
                    : "All changes saved"}
                </div>
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    onClick={handleReset}
                    disabled={!hasUnsavedChanges}
                  >
                    <RotateCcw className="h-4 w-4 mr-2" />
                    Reset to Defaults
                  </Button>
                  <Button 
                    onClick={handleSave} 
                    disabled={!hasUnsavedChanges || isUpdating}
                  >
                    <Save className="h-4 w-4 mr-2" />
                    {isUpdating ? "Saving..." : "Save Changes"}
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Confirmation Dialogs */}
      <ConfirmDialog
        open={showConfirmDialog}
        onOpenChange={setShowConfirmDialog}
        onConfirm={confirmCategoryChange}
        title="Unsaved Changes"
        description="You have unsaved changes. Are you sure you want to leave this section? Your changes will be lost."
        confirmText="Leave"
        cancelText="Stay"
      />

      <ConfirmDialog
        open={showResetDialog}
        onOpenChange={setShowResetDialog}
        onConfirm={confirmReset}
        title="Reset to Defaults"
        description="Are you sure you want to reset all settings in this section to their default values? This action cannot be undone."
        confirmText="Reset"
        cancelText="Cancel"
        variant="destructive"
      />
    </DashboardLayout>
  );
}
