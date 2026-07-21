import { apiClient } from '@/services/client';
import type {
  BulkResolveResult,
  Case,
  MappingRule,
  ReconBreak,
  ReconRun,
  ResolutionType,
} from '@/types';

export function fetchRuns(): Promise<ReconRun[]> {
  return apiClient.get<ReconRun[]>('/reconciliation/runs');
}

export function fetchBreaks(runId: string): Promise<ReconBreak[]> {
  return apiClient.get<ReconBreak[]>(`/reconciliation/runs/${runId}/breaks`);
}

export function fetchBreakDetail(breakId: string): Promise<ReconBreak> {
  return apiClient.get<ReconBreak>(`/reconciliation/breaks/${breakId}`);
}

export interface ResolveBreakPayload {
  resolutionType: ResolutionType;
  note?: string;
  mappingRuleId?: string;
}

export function resolveBreak(breakId: string, payload: ResolveBreakPayload): Promise<ReconBreak> {
  return apiClient.post<ReconBreak>(`/reconciliation/breaks/${breakId}/resolve`, payload);
}

export interface BulkResolvePayload extends ResolveBreakPayload {
  breakIds: string[];
}

export function bulkResolveBreaks(payload: BulkResolvePayload): Promise<BulkResolveResult> {
  return apiClient.post<BulkResolveResult>('/reconciliation/breaks/bulk-resolve', payload);
}

export function signOffRun(runId: string): Promise<{ run: ReconRun }> {
  return apiClient.post<{ run: ReconRun }>(`/reconciliation/runs/${runId}/sign-off`);
}

export function createCaseFromBreak(breakId: string): Promise<Case> {
  return apiClient.post<Case>(`/reconciliation/breaks/${breakId}/create-case`);
}

export function fetchMappingRules(): Promise<MappingRule[]> {
  return apiClient.get<MappingRule[]>('/reconciliation/mapping-rules');
}
