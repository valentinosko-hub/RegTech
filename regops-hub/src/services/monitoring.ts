import { apiClient } from '@/services/client';
import type { Alert, AlertDetail, Case, FeedStatusItem, ReportSubmission } from '@/types';

export function fetchReports(): Promise<ReportSubmission[]> {
  return apiClient.get<ReportSubmission[]>('/monitoring/reports');
}

export function fetchFeeds(): Promise<FeedStatusItem[]> {
  return apiClient.get<FeedStatusItem[]>('/monitoring/feeds');
}

export function fetchAlerts(): Promise<Alert[]> {
  return apiClient.get<Alert[]>('/monitoring/alerts');
}

export function fetchAlertDetail(eventId: string): Promise<AlertDetail> {
  return apiClient.get<AlertDetail>(`/monitoring/alerts/${eventId}`);
}

export function createCaseFromAlert(eventId: string): Promise<Case> {
  return apiClient.post<Case>(`/monitoring/alerts/${eventId}/create-case`);
}
