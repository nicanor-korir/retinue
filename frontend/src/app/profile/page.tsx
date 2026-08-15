"use client";

import { useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useUserProfile } from "@/hooks/useSettings";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  User,
  Palette,
  Bell,
  Shield,
  Briefcase,
  Plug,
  Activity,
  Save,
  Camera,
} from "lucide-react";

import { PersonalInfoSection } from "@/components/profile/personal-info-section";
import { AppearanceSection } from "@/components/profile/appearance-section";
import { NotificationPreferences } from "@/components/profile/notification-preferences";
import { PrivacySection } from "@/components/profile/privacy-section";
import { WorkPreferences } from "@/components/profile/work-preferences";
import { ConnectedAccounts } from "@/components/profile/connected-accounts";
import { ActivityStats } from "@/components/profile/activity-stats";

export default function ProfilePage() {
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const [activeTab, setActiveTab] = useState("personal");
  const [localChanges, setLocalChanges] = useState<Record<string, any>>({});

  // TODO: Get actual user ID from auth context
  // For now using a mock ID - replace with: const { userId } = useAuth();
  const userId = "user-123";

  // Fetch profile from backend
  const { profile, isLoading, updateProfile, isUpdating, error } = useUserProfile(userId);

  // Handle profile changes from child components
  const handleProfileChange = (updates: Record<string, any>) => {
    setLocalChanges((prev) => ({ ...prev, ...updates }));
    setHasUnsavedChanges(true);
  };

  // Handle save
  const handleSave = () => {
    if (Object.keys(localChanges).length > 0) {
      updateProfile(localChanges);
      setLocalChanges({});
      setHasUnsavedChanges(false);
    }
  };

  // Show loading state
  if (isLoading) {
    return (
      <DashboardLayout>
        <div className="flex items-center justify-center h-[600px]">
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto mb-4"></div>
            <p className="text-muted-foreground">Loading profile...</p>
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
            <p className="text-destructive font-medium mb-2">Error loading profile</p>
            <p className="text-sm text-muted-foreground">
              {error instanceof Error ? error.message : "Unknown error"}
            </p>
          </div>
        </div>
      </DashboardLayout>
    );
  }

  // Extract profile data with defaults
  const displayName = profile?.display_name || profile?.full_name || "User";
  const fullName = profile?.full_name || "John Doe";
  const email = profile?.email || "user@example.com";
  const jobTitle = profile?.job_title || "Team Member";
  const department = profile?.department || "General";
  const avatarUrl = profile?.avatar_url;
  const isOnline = profile?.show_online_status !== false;

  // Get initials for avatar
  const initials = fullName
    .split(" ")
    .map((n: string) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);

  return (
    <DashboardLayout>
      <div className="space-y-6 max-w-6xl mx-auto">
        {/* Profile Header */}
        <div className="relative">
          <Card className="p-6">
            <div className="flex items-start gap-6">
              {/* Avatar */}
              <div className="relative">
                {avatarUrl ? (
                  <img
                    src={avatarUrl}
                    alt={fullName}
                    className="h-24 w-24 rounded-full object-cover"
                  />
                ) : (
                  <div className="h-24 w-24 rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center text-3xl font-bold text-white">
                    {initials}
                  </div>
                )}
                <button className="absolute bottom-0 right-0 h-8 w-8 rounded-full bg-primary text-white flex items-center justify-center hover:bg-primary/90 transition-colors">
                  <Camera className="h-4 w-4" />
                </button>
              </div>

              {/* User Info */}
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <h1 className="text-2xl font-bold">{fullName}</h1>
                  <Badge variant="outline">{profile?.role || "Member"}</Badge>
                  {isOnline && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                      <div className="h-2 w-2 rounded-full bg-green-500"></div>
                      <span>Online</span>
                    </div>
                  )}
                </div>
                <p className="text-muted-foreground mt-1">{email}</p>
                <div className="flex items-center gap-4 mt-3 text-sm">
                  <div>
                    <span className="font-medium">{jobTitle}</span>
                  </div>
                  <div className="text-muted-foreground">{department}</div>
                  <div className="text-muted-foreground">
                    Member since {new Date(profile?.created_at || Date.now()).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
                  </div>
                </div>
              </div>

              {/* Quick Stats */}
              <div className="flex gap-6 text-center">
                <div>
                  <div className="text-2xl font-bold">47</div>
                  <div className="text-xs text-muted-foreground">Tasks</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">12</div>
                  <div className="text-xs text-muted-foreground">Projects</div>
                </div>
                <div>
                  <div className="text-2xl font-bold">98%</div>
                  <div className="text-xs text-muted-foreground">On Time</div>
                </div>
              </div>
            </div>
          </Card>

          {/* Unsaved Changes Badge */}
          {hasUnsavedChanges && (
            <div className="absolute top-4 right-4">
              <Badge variant="warning" className="animate-pulse">
                Unsaved Changes
              </Badge>
            </div>
          )}
        </div>

        {/* Profile Content */}
        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-7">
            <TabsTrigger value="personal" className="flex items-center gap-2">
              <User className="h-4 w-4" />
              <span className="hidden sm:inline">Personal</span>
            </TabsTrigger>
            <TabsTrigger value="appearance" className="flex items-center gap-2">
              <Palette className="h-4 w-4" />
              <span className="hidden sm:inline">Appearance</span>
            </TabsTrigger>
            <TabsTrigger value="notifications" className="flex items-center gap-2">
              <Bell className="h-4 w-4" />
              <span className="hidden sm:inline">Notifications</span>
            </TabsTrigger>
            <TabsTrigger value="privacy" className="flex items-center gap-2">
              <Shield className="h-4 w-4" />
              <span className="hidden sm:inline">Privacy</span>
            </TabsTrigger>
            <TabsTrigger value="work" className="flex items-center gap-2">
              <Briefcase className="h-4 w-4" />
              <span className="hidden sm:inline">Work</span>
            </TabsTrigger>
            <TabsTrigger value="connected" className="flex items-center gap-2">
              <Plug className="h-4 w-4" />
              <span className="hidden sm:inline">Connected</span>
            </TabsTrigger>
            <TabsTrigger value="activity" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              <span className="hidden sm:inline">Activity</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="personal" className="space-y-6">
            <PersonalInfoSection onSettingsChange={handleProfileChange} />
          </TabsContent>

          <TabsContent value="appearance" className="space-y-6">
            <AppearanceSection onSettingsChange={handleProfileChange} />
          </TabsContent>

          <TabsContent value="notifications" className="space-y-6">
            <NotificationPreferences onSettingsChange={handleProfileChange} />
          </TabsContent>

          <TabsContent value="privacy" className="space-y-6">
            <PrivacySection onSettingsChange={handleProfileChange} />
          </TabsContent>

          <TabsContent value="work" className="space-y-6">
            <WorkPreferences onSettingsChange={handleProfileChange} />
          </TabsContent>

          <TabsContent value="connected" className="space-y-6">
            <ConnectedAccounts onSettingsChange={handleProfileChange} />
          </TabsContent>

          <TabsContent value="activity" className="space-y-6">
            <ActivityStats />
          </TabsContent>
        </Tabs>

        {/* Sticky Save Button */}
        {hasUnsavedChanges && (
          <div className="sticky bottom-0 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 border-t p-4 rounded-lg shadow-lg">
            <div className="flex items-center justify-between">
              <div className="text-sm text-muted-foreground">
                You have unsaved changes to your profile
              </div>
              <Button onClick={handleSave} disabled={isUpdating}>
                <Save className="h-4 w-4 mr-2" />
                {isUpdating ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}
