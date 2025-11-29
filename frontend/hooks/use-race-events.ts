'use client';

import useSWR from 'swr';

const API_BASE = 'http://localhost:8000/api';

const fetcher = (url: string) => fetch(url).then((res) => res.json());

export interface TrackStatusData {
  Time: string;
  TimeSeconds: number;
  Status: number;
  Message: string;
}

export interface RaceControlMessage {
  Time: string;
  Category: string;
  Message: string;
  Status: string;
  Flag: string;
  Scope: string;
  Sector: number | string;
  RacingNumber: string;
  Lap: number | string;
}

export interface WeatherData {
  Time: string;
  TimeSeconds: number;
  AirTemp: number;
  Humidity: number;
  Pressure: number;
  Rainfall: boolean;
  TrackTemp: number;
  WindDirection: number;
  WindSpeed: number;
}

export function useTrackStatus(year: number, race: string, sessionType: string = 'R') {
  const url = `${API_BASE}/session/${year}/${race}/${sessionType}/track-status`;

  const { data, error, isLoading } = useSWR<{
    session_name: string;
    track_status: TrackStatusData[];
  }>(url, fetcher);

  return {
    data,
    isLoading,
    error,
  };
}

export function useRaceControlMessages(year: number, race: string, sessionType: string = 'R') {
  const url = `${API_BASE}/session/${year}/${race}/${sessionType}/race-control`;

  const { data, error, isLoading } = useSWR<{
    session_name: string;
    messages: RaceControlMessage[];
  }>(url, fetcher);

  return {
    data,
    isLoading,
    error,
  };
}

export function useWeatherData(year: number, race: string, sessionType: string = 'R') {
  const url = `${API_BASE}/session/${year}/${race}/${sessionType}/weather`;

  const { data, error, isLoading } = useSWR<{
    session_name: string;
    weather: WeatherData[];
  }>(url, fetcher);

  return {
    data,
    isLoading,
    error,
  };
}
