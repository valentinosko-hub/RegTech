import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { queryKeys } from '@/hooks/useApi';
import {
  type BulkResolvePayload,
  type ResolveBreakPayload,
  bulkResolveBreaks,
  createCaseFromBreak,
  fetchBreakDetail,
  fetchBreaks,
  fetchMappingRules,
  fetchRuns,
  resolveBreak,
  signOffRun,
} from '@/services/reconciliation';
import type { ReconRun } from '@/types';

// Reconciliation data doesn't change intraday — fetch once on mount, no
// polling (per ARCHITECTURE.md's polling configuration).
export function useRuns() {
  return useQuery({ queryKey: queryKeys.runs, queryFn: fetchRuns });
}

export function useBreaks(runId: string | null) {
  return useQuery({
    queryKey: queryKeys.breaks(runId ?? ''),
    queryFn: () => fetchBreaks(runId as string),
    enabled: runId !== null,
  });
}

export function useBreakDetail(breakId: string | null) {
  return useQuery({
    queryKey: queryKeys.breakDetail(breakId ?? ''),
    queryFn: () => fetchBreakDetail(breakId as string),
    enabled: breakId !== null,
  });
}

export function useMappingRules() {
  return useQuery({ queryKey: queryKeys.mappingRules, queryFn: fetchMappingRules });
}

// Used by the "Today's Breaks" saved view, which flattens open breaks across
// every jurisdiction's run into a single list.
export function useAllOpenBreaks(runs: ReconRun[] | undefined) {
  const runIds = (runs ?? []).map((r) => r.runId);
  return useQuery({
    queryKey: ['reconciliation', 'all-breaks', runIds.join(',')],
    queryFn: async () => {
      const results = await Promise.all(runIds.map((runId) => fetchBreaks(runId)));
      return results.flat().filter((b) => b.status === 'open');
    },
    enabled: runIds.length > 0,
  });
}

function useInvalidateAfterBreakChange(runId: string) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.breaks(runId) });
    queryClient.invalidateQueries({ queryKey: queryKeys.runs });
    queryClient.invalidateQueries({ queryKey: queryKeys.savedViewCounts });
    queryClient.invalidateQueries({ queryKey: queryKeys.home });
  };
}

export function useResolveBreak(runId: string) {
  const invalidate = useInvalidateAfterBreakChange(runId);
  return useMutation({
    mutationFn: ({ breakId, payload }: { breakId: string; payload: ResolveBreakPayload }) =>
      resolveBreak(breakId, payload),
    onSuccess: invalidate,
  });
}

export function useBulkResolveBreaks(runId: string) {
  const invalidate = useInvalidateAfterBreakChange(runId);
  return useMutation({
    mutationFn: (payload: BulkResolvePayload) => bulkResolveBreaks(payload),
    onSuccess: invalidate,
  });
}

export function useSignOffRun() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (runId: string) => signOffRun(runId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.runs });
      queryClient.invalidateQueries({ queryKey: queryKeys.home });
    },
  });
}

export function useCreateCaseFromBreak(runId: string) {
  const invalidate = useInvalidateAfterBreakChange(runId);
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (breakId: string) => createCaseFromBreak(breakId),
    onSuccess: () => {
      invalidate();
      queryClient.invalidateQueries({ queryKey: ['cases'] });
    },
  });
}
