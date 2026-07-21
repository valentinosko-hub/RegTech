import { useQuery } from '@tanstack/react-query';

import { queryKeys } from '@/hooks/useApi';
import { fetchHomeSummary } from '@/services/home';

export function useHomeSummary() {
  return useQuery({
    queryKey: queryKeys.home,
    queryFn: fetchHomeSummary,
    refetchInterval: 30_000,
  });
}
