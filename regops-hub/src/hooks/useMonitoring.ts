import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { queryKeys } from '@/hooks/useApi';
import { POLL_INTERVALS } from '@/hooks/usePolling';
import { createCaseFromAlert, fetchAlertDetail, fetchAlerts, fetchFeeds, fetchReports } from '@/services/monitoring';

export function useReports() {
  return useQuery({
    queryKey: queryKeys.reports,
    queryFn: fetchReports,
    refetchInterval: POLL_INTERVALS.reportSubmissions,
  });
}

export function useFeeds() {
  return useQuery({
    queryKey: queryKeys.feeds,
    queryFn: fetchFeeds,
    refetchInterval: POLL_INTERVALS.feedStatus,
  });
}

export function useAlerts() {
  return useQuery({
    queryKey: queryKeys.alerts,
    queryFn: fetchAlerts,
    refetchInterval: POLL_INTERVALS.activeAlerts,
  });
}

export function useAlertDetail(eventId: string | null) {
  return useQuery({
    queryKey: queryKeys.alertDetail(eventId ?? ''),
    queryFn: () => fetchAlertDetail(eventId as string),
    enabled: eventId !== null,
  });
}

export function useCreateCaseFromAlert() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (eventId: string) => createCaseFromAlert(eventId),
    onSuccess: (_case, eventId) => {
      queryClient.invalidateQueries({ queryKey: queryKeys.alerts });
      queryClient.invalidateQueries({ queryKey: queryKeys.alertDetail(eventId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.savedViewCounts });
      queryClient.invalidateQueries({ queryKey: ['cases'] });
      queryClient.invalidateQueries({ queryKey: queryKeys.home });
    },
  });
}
