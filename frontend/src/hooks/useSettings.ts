import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { systemSettingsAPI, userProfilesAPI, settingsAuditAPI } from "@/lib/api";

/**
 * Hook for fetching and managing system settings
 */
export function useSystemSettings() {
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["system-settings"],
    queryFn: async () => {
      const response = await systemSettingsAPI.get();
      return response.data;
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (updates: any) => {
      const response = await systemSettingsAPI.update(updates);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["system-settings"] });
      console.log("Settings updated successfully");
    },
    onError: (error: any) => {
      console.error("Failed to update settings:", error);
    },
  });

  return {
    settings: data,
    isLoading,
    error,
    refetch,
    updateSettings: updateMutation.mutate,
    isUpdating: updateMutation.isPending,
  };
}

/**
 * Hook for fetching and managing user profile
 */
export function useUserProfile(userId: string) {
  const queryClient = useQueryClient();

  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["user-profile", userId],
    queryFn: async () => {
      const response = await userProfilesAPI.get(userId);
      return response.data;
    },
    enabled: !!userId,
  });

  const updateMutation = useMutation({
    mutationFn: async (updates: any) => {
      const response = await userProfilesAPI.update(userId, updates);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user-profile", userId] });
      console.log("Profile updated successfully");
    },
    onError: (error: any) => {
      console.error("Failed to update profile:", error);
    },
  });

  return {
    profile: data,
    isLoading,
    error,
    refetch,
    updateProfile: updateMutation.mutate,
    isUpdating: updateMutation.isPending,
  };
}

/**
 * Hook for listing all user profiles (admin only)
 */
export function useUserProfiles(limit?: number) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["user-profiles", limit],
    queryFn: async () => {
      const response = await userProfilesAPI.list(limit);
      return response.data;
    },
  });

  return {
    profiles: data || [],
    isLoading,
    error,
    refetch,
  };
}

/**
 * Hook for creating a new user profile
 */
export function useCreateUserProfile() {
  const queryClient = useQueryClient();

  const createMutation = useMutation({
    mutationFn: async (profileData: any) => {
      const response = await userProfilesAPI.create(profileData);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["user-profiles"] });
      console.log("Profile created successfully");
    },
    onError: (error: any) => {
      console.error("Failed to create profile:", error);
    },
  });

  return {
    createProfile: createMutation.mutate,
    isCreating: createMutation.isPending,
    error: createMutation.error,
  };
}

/**
 * Hook for fetching settings audit log
 */
export function useSettingsAuditLog(filters?: {
  entity_type?: "system_settings" | "user_profile";
  entity_id?: string;
  limit?: number;
}) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ["settings-audit-log", filters],
    queryFn: async () => {
      const response = await settingsAuditAPI.list(filters);
      return response.data;
    },
  });

  return {
    auditLogs: data || [],
    isLoading,
    error,
    refetch,
  };
}
