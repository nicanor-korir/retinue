import { useMutation, useQueryClient, QueryKey } from "@tanstack/react-query";

/**
 * Configuration for creating mutation hooks
 */
interface MutationConfig<TVariables, TData> {
  /** The mutation function to execute */
  mutationFn: (variables: TVariables) => Promise<TData>;
  /** Query keys to invalidate on success */
  invalidateKeys: QueryKey[];
  /** Optional additional onSuccess logic */
  onSuccess?: (data: TData, variables: TVariables) => void;
}

/**
 * Factory function to create standardized mutation hooks
 * Reduces duplication across cancel, approve, delete operations
 */
export function createMutation<TVariables = void, TData = any>(
  config: MutationConfig<TVariables, TData>
) {
  return () => {
    const queryClient = useQueryClient();

    return useMutation({
      mutationFn: config.mutationFn,
      onSuccess: (data, variables) => {
        // Invalidate all specified query keys
        config.invalidateKeys.forEach((key) => {
          queryClient.invalidateQueries({ queryKey: key });
        });

        // Run additional onSuccess logic if provided
        config.onSuccess?.(data, variables);
      },
    });
  };
}

/**
 * Factory for entity-specific mutations (cancel, approve, delete)
 * Further reduces duplication for common entity operations
 */
interface EntityMutationConfig<TVariables = string> {
  /** The API function to call */
  apiFn: (variables: TVariables) => Promise<any>;
  /** Base query keys to invalidate (e.g., ['projects'], ['tasks']) */
  entityKeys: QueryKey[];
  /** Optional dashboard key to invalidate */
  invalidateDashboard?: boolean;
  /** Function to get entity-specific key (e.g., project(id)) */
  getEntityKey?: (variables: TVariables) => QueryKey;
}

/**
 * Create a mutation hook for entity operations
 */
export function createEntityMutation<TVariables = string>(
  config: EntityMutationConfig<TVariables>
) {
  const invalidateKeys = [...config.entityKeys];

  if (config.invalidateDashboard) {
    invalidateKeys.push(["dashboard"]);
  }

  return createMutation<TVariables, any>({
    mutationFn: config.apiFn,
    invalidateKeys,
    onSuccess: (_, variables) => {
      // Also invalidate the specific entity key if provided
      if (config.getEntityKey) {
        const queryClient = useQueryClient();
        queryClient.invalidateQueries({
          queryKey: config.getEntityKey(variables)
        });
      }
    },
  });
}
