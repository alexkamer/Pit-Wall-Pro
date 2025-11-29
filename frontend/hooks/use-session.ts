import { useQuery } from '@tanstack/react-query';
import { apiClient } from '@/lib/api/client';

export function useSessionResults(year: number, race: string, sessionType: string) {
  return useQuery({
    queryKey: ['session', 'results', year, race, sessionType],
    queryFn: () => apiClient.getSessionResults(year, race, sessionType),
    enabled: !!year && !!race && !!sessionType,
  });
}

export function useLapTimes(year: number, race: string, sessionType: string, driver?: string) {
  return useQuery({
    queryKey: ['session', 'laps', year, race, sessionType, driver],
    queryFn: () => apiClient.getLapTimes(year, race, sessionType, driver),
    enabled: !!year && !!race && !!sessionType,
  });
}

export function useFastestLap(year: number, race: string, sessionType: string) {
  return useQuery({
    queryKey: ['session', 'fastest', year, race, sessionType],
    queryFn: () => apiClient.getFastestLap(year, race, sessionType),
    enabled: !!year && !!race && !!sessionType,
  });
}

export function useTelemetry(year: number, race: string, sessionType: string, driver: string, lap: number) {
  return useQuery({
    queryKey: ['session', 'telemetry', year, race, sessionType, driver, lap],
    queryFn: () => apiClient.getTelemetry(year, race, sessionType, driver, lap),
    enabled: !!year && !!race && !!sessionType && !!driver && !!lap,
  });
}
