export interface RaceEvent {
  RoundNumber: number;
  Country: string;
  Location: string;
  OfficialEventName: string;
  EventDate: string;
  EventName: string;
  EventFormat: string;
  Session1?: string;
  Session1Date?: string;
  Session2?: string;
  Session2Date?: string;
  Session3?: string;
  Session3Date?: string;
  Session4?: string;
  Session4Date?: string;
  Session5?: string;
  Session5Date?: string;
}

export interface DriverStanding {
  position: number;
  driver: string;
  team: string;
  points: number;
  wins: number;
}

export interface LapTime {
  Driver: string;
  LapNumber: number;
  LapTime: number;
  Sector1Time: number;
  Sector2Time: number;
  Sector3Time: number;
  Compound: string;
  TyreLife: number;
}

export interface TelemetryData {
  Distance: number;
  Speed: number;
  RPM: number;
  nGear: number;
  Throttle: number;
  Brake: number;
  DRS: number;
}
