import { apiClient } from '@/services/client';
import type { HomeSummary } from '@/types';

export function fetchHomeSummary(): Promise<HomeSummary> {
  return apiClient.get<HomeSummary>('/home');
}
