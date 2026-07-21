import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { queryKeys } from '@/hooks/useApi';
import { POLL_INTERVALS } from '@/hooks/usePolling';
import {
  fetchCurrentUser,
  fetchNotifications,
  fetchSavedViewCounts,
  markAllNotificationsRead,
  markNotificationRead,
  search,
} from '@/services/shell';

export function useCurrentUser() {
  return useQuery({ queryKey: queryKeys.currentUser, queryFn: fetchCurrentUser, staleTime: Infinity });
}

export function useSavedViewCounts() {
  return useQuery({
    queryKey: queryKeys.savedViewCounts,
    queryFn: fetchSavedViewCounts,
    refetchInterval: POLL_INTERVALS.savedViewCounts,
  });
}

export function useNotifications() {
  return useQuery({
    queryKey: queryKeys.notifications,
    queryFn: fetchNotifications,
    refetchInterval: POLL_INTERVALS.notifications,
  });
}

export function useMarkNotificationRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => markNotificationRead(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.notifications }),
  });
}

export function useMarkAllNotificationsRead() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => markAllNotificationsRead(),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.notifications }),
  });
}

export function useSearch(query: string) {
  return useQuery({
    queryKey: queryKeys.search(query),
    queryFn: () => search(query),
    enabled: query.trim().length > 0,
  });
}
