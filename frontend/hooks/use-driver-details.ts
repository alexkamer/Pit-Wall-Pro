import useSWR from 'swr';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export function useDriverDetails(driverName: string, year: number = 2024) {
  const { data, error, isLoading } = useSWR(
    `http://localhost:8000/api/drivers/${driverName}?year=${year}`,
    fetcher,
    {
      revalidateOnFocus: false,
      dedupingInterval: 60000, // Cache for 1 minute
    }
  );

  return {
    data,
    isLoading,
    error,
  };
}
