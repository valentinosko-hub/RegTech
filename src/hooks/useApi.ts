import { QueryClient } from '@tanstack/react-query';

// Single QueryClient instance shared by the whole app (see src/index.tsx).
export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      staleTime: 10_000,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 0,
    },
  },
});

// Query key factory — keeps cache keys consistent across hooks so that
// mutations know exactly which queries to invalidate.
export const queryKeys = {
  home: ['home'] as const,
  reports: ['monitoring', 'reports'] as const,
  feeds: ['monitoring', 'feeds'] as const,
  alerts: ['monitoring', 'alerts'] as const,
  alertDetail: (id: string) => ['monitoring', 'alerts', id] as const,
  runs: ['reconciliation', 'runs'] as const,
  breaks: (runId: string) => ['reconciliation', 'runs', runId, 'breaks'] as const,
  breakDetail: (id: string) => ['reconciliation', 'breaks', id] as const,
  mappingRules: ['reconciliation', 'mapping-rules'] as const,
  cases: (filter: string, search?: string) => ['cases', filter, search ?? ''] as const,
  caseDetail: (id: string) => ['cases', id] as const,
  currentUser: ['me'] as const,
  savedViewCounts: ['views', 'counts'] as const,
  notifications: ['notifications'] as const,
  search: (q: string) => ['search', q] as const,
};
