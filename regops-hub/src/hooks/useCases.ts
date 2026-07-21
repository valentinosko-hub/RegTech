import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';

import { queryKeys } from '@/hooks/useApi';
import { POLL_INTERVALS } from '@/hooks/usePolling';
import {
  type CaseFilter,
  type CloseCasePayload,
  type UpdateCasePayload,
  addComment,
  closeCase,
  createCase,
  extractCase,
  fetchCaseDetail,
  fetchCases,
  updateCase,
} from '@/services/cases';
import type { CreateCasePayload } from '@/types';

export function useCases(filter: CaseFilter, search?: string) {
  return useQuery({
    queryKey: queryKeys.cases(filter, search),
    queryFn: () => fetchCases(filter, search),
    refetchInterval: POLL_INTERVALS.cases,
  });
}

export function useCaseDetail(caseId: string | null) {
  return useQuery({
    queryKey: queryKeys.caseDetail(caseId ?? ''),
    queryFn: () => fetchCaseDetail(caseId as string),
    enabled: caseId !== null,
  });
}

function useInvalidateCases() {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ['cases'] });
    queryClient.invalidateQueries({ queryKey: queryKeys.savedViewCounts });
    queryClient.invalidateQueries({ queryKey: queryKeys.home });
  };
}

export function useExtractCase() {
  return useMutation({ mutationFn: (text: string) => extractCase(text) });
}

export function useCreateCase() {
  const invalidate = useInvalidateCases();
  return useMutation({
    mutationFn: (payload: CreateCasePayload) => createCase(payload),
    onSuccess: invalidate,
  });
}

export function useUpdateCase(caseId: string) {
  const queryClient = useQueryClient();
  const invalidate = useInvalidateCases();
  return useMutation({
    mutationFn: (payload: UpdateCasePayload) => updateCase(caseId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.caseDetail(caseId) });
      invalidate();
    },
  });
}

export function useAddComment(caseId: string) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (body: string) => addComment(caseId, body),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: queryKeys.caseDetail(caseId) }),
  });
}

export function useCloseCase(caseId: string) {
  const queryClient = useQueryClient();
  const invalidate = useInvalidateCases();
  return useMutation({
    mutationFn: (payload: CloseCasePayload) => closeCase(caseId, payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.caseDetail(caseId) });
      invalidate();
    },
  });
}
