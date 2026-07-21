import { apiClient } from '@/services/client';
import type { CurrentUser, Notification, SavedViewCounts, SearchResult } from '@/types';

export function fetchCurrentUser(): Promise<CurrentUser> {
  return apiClient.get<CurrentUser>('/me');
}

export function fetchSavedViewCounts(): Promise<SavedViewCounts> {
  return apiClient.get<SavedViewCounts>('/views/counts');
}

export function fetchNotifications(): Promise<Notification[]> {
  return apiClient.get<Notification[]>('/notifications');
}

export function markNotificationRead(id: string): Promise<Notification> {
  return apiClient.post<Notification>(`/notifications/${id}/read`);
}

export function markAllNotificationsRead(): Promise<{ updated: number }> {
  return apiClient.post<{ updated: number }>('/notifications/read-all');
}

export function search(query: string): Promise<SearchResult[]> {
  return apiClient.get<SearchResult[]>(`/search?q=${encodeURIComponent(query)}`);
}
