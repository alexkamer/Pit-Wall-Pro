import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';

export function useSchedule(year: number = 2025) {
  return useQuery({
    queryKey: ['schedule', year],
    queryFn: () => apiClient.getSchedule(year),
    staleTime: 1000 * 60 * 60, // 1 hour
  });
}
