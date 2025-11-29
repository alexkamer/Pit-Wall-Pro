import { API_BASE_URL } from '../constants';

class APIClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  private async request<T>(endpoint: string): Promise<T> {
    const response = await fetch(`${this.baseURL}${endpoint}`);

    if (!response.ok) {
      throw new Error(`API Error: ${response.statusText}`);
    }

    return response.json();
  }

  // Schedule
  async getSchedule(year: number = 2025) {
    return this.request(`/api/schedule?year=${year}`);
  }

  // Standings
  async getDriverStandings(year: number = 2025) {
    return this.request(`/api/standings/drivers?year=${year}`);
  }

  async getConstructorStandings(year: number = 2025) {
    return this.request(`/api/standings/constructors?year=${year}`);
  }

  // Session Data
  async getSessionResults(year: number, race: string, sessionType: string) {
    return this.request(`/api/session/${year}/${encodeURIComponent(race)}/${sessionType}/results`);
  }

  async getLapTimes(year: number, race: string, sessionType: string, driver?: string) {
    const params = driver ? `?driver=${driver}` : '';
    return this.request(`/api/session/${year}/${encodeURIComponent(race)}/${sessionType}/laps${params}`);
  }

  async getFastestLap(year: number, race: string, sessionType: string) {
    return this.request(`/api/session/${year}/${encodeURIComponent(race)}/${sessionType}/fastest`);
  }

  async getTelemetry(year: number, race: string, sessionType: string, driver: string, lap: number) {
    return this.request(`/api/session/${year}/${encodeURIComponent(race)}/${sessionType}/telemetry?driver=${driver}&lap=${lap}`);
  }
}

export const apiClient = new APIClient();
