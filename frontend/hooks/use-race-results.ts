import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';

export function useRaceResults(year: number, round: number | string) {
  return useQuery({
    queryKey: ['race-results', year, round],
    queryFn: () => apiClient.getSessionResults(year, String(round), 'R'),
    staleTime: 1000 * 60 * 60, // 1 hour
    enabled: !!year && !!round,
  });
}

export function useQualifyingResults(year: number, round: number | string) {
  return useQuery({
    queryKey: ['qualifying-results', year, round],
    queryFn: () => apiClient.getSessionResults(year, String(round), 'Q'),
    staleTime: 1000 * 60 * 60, // 1 hour
    enabled: !!year && !!round,
  });
}
