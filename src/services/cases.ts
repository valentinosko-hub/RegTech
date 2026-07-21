import { apiClient } from '@/services/client';
import type { Case, CaseDetail, CaseExtraction, Comment, CreateCasePayload } from '@/types';

export type CaseFilter = 'mine' | 'open' | 'all';

export function fetchCases(filter: CaseFilter, search?: string): Promise<Case[]> {
  const params = new URLSearchParams({ filter });
  if (search) params.set('search', search);
  return apiClient.get<Case[]>(`/cases?${params.toString()}`);
}

export function fetchCaseDetail(caseId: string): Promise<CaseDetail> {
  return apiClient.get<CaseDetail>(`/cases/${caseId}`);
}

export function extractCase(text: string): Promise<CaseExtraction> {
  return apiClient.post<CaseExtraction>('/cases/extract', { text });
}

export function createCase(payload: CreateCasePayload): Promise<Case> {
  return apiClient.post<Case>('/cases', payload);
}

export interface UpdateCasePayload {
  status?: Case['status'];
  severity?: Case['severity'];
  owner?: string;
}

export function updateCase(caseId: string, payload: UpdateCasePayload): Promise<Case> {
  return apiClient.patch<Case>(`/cases/${caseId}`, payload);
}

export function addComment(caseId: string, body: string): Promise<Comment> {
  return apiClient.post<Comment>(`/cases/${caseId}/comments`, { body });
}

export interface CloseCasePayload {
  resolutionType: string;
  resolutionNote: string;
}

export function closeCase(caseId: string, payload: CloseCasePayload): Promise<Case> {
  return apiClient.post<Case>(`/cases/${caseId}/close`, payload);
}
