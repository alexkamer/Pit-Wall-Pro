import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';

export function useDriverStandings(year: number = 2025) {
  return useQuery({
    queryKey: ['standings', 'drivers', year],
    queryFn: () => apiClient.getDriverStandings(year),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}

export function useConstructorStandings(year: number = 2025) {
  return useQuery({
    queryKey: ['standings', 'constructors', year],
    queryFn: () => apiClient.getConstructorStandings(year),
    staleTime: 1000 * 60 * 5, // 5 minutes
  });
}
