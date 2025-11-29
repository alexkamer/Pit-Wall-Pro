import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';

export function useLapTimes(year: number, race: string | number, sessionType: string, driver?: string) {
  return useQuery({
    queryKey: ['lap-times', year, race, sessionType, driver],
    queryFn: () => apiClient.getLapTimes(year, String(race), sessionType, driver),
    staleTime: 1000 * 60 * 60, // 1 hour
    enabled: !!year && !!race && !!sessionType,
  });
}
