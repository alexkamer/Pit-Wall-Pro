'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, Flag, Shield, Cloud, CloudRain, Zap, Wind, Thermometer } from 'lucide-react';
import { useTrackStatus, useRaceControlMessages, useWeatherData } from '@/hooks/use-race-events';

interface RaceEventsProps {
  year: number;
  race: string;
}

// Track status codes
const STATUS_CODES = {
  1: { name: 'Green Flag', color: 'bg-green-600', icon: Flag },
  2: { name: 'Yellow Flag', color: 'bg-yellow-500', icon: AlertTriangle },
  4: { name: 'Safety Car', color: 'bg-yellow-600', icon: Shield },
  5: { name: 'Red Flag', color: 'bg-red-600', icon: Flag },
  6: { name: 'VSC Deployed', color: 'bg-yellow-600', icon: Shield },
  7: { name: 'VSC Ending', color: 'bg-yellow-400', icon: Shield },
} as const;

const formatTime = (seconds: number): string => {
  const hours = Math.floor(seconds / 3600);
  const minutes = Math.floor((seconds % 3600) / 60);
  const secs = Math.floor(seconds % 60);
  return `${hours}:${String(minutes).padStart(2, '0')}:${String(secs).padStart(2, '0')}`;
};

export function RaceEvents({ year, race }: RaceEventsProps) {
  const { data: trackStatusData, isLoading: trackLoading } = useTrackStatus(year, race, 'R');
  const { data: raceControlData, isLoading: controlLoading } = useRaceControlMessages(year, race, 'R');
  const { data: weatherData, isLoading: weatherLoading } = useWeatherData(year, race, 'R');

  // Filter significant track status changes (not AllClear events)
  const significantEvents = trackStatusData?.track_status.filter(
    (status) => status.Status !== 1 && status.TimeSeconds
  ) || [];

  // Group consecutive events of the same type
  const groupedEvents: Array<{
    status: number;
    message: string;
    startTime: number;
    endTime?: number;
  }> = [];

  significantEvents.forEach((event, index) => {
    const nextAllClear = trackStatusData?.track_status.find(
      (s, i) => i > trackStatusData.track_status.indexOf(event) && s.Status === 1
    );

    groupedEvents.push({
      status: event.Status,
      message: event.Message,
      startTime: event.TimeSeconds,
      endTime: nextAllClear?.TimeSeconds,
    });
  });

  // Filter red flag messages from race control
  const redFlagMessages = raceControlData?.messages.filter(
    (msg) => msg.Flag?.toLowerCase().includes('red') || msg.Message?.toLowerCase().includes('red flag')
  ) || [];

  // Get average weather conditions
  const avgWeather = weatherData?.weather.length
    ? {
        airTemp: (weatherData.weather.reduce((sum, w) => sum + (w.AirTemp || 0), 0) / weatherData.weather.length).toFixed(1),
        trackTemp: (weatherData.weather.reduce((sum, w) => sum + (w.TrackTemp || 0), 0) / weatherData.weather.length).toFixed(1),
        humidity: (weatherData.weather.reduce((sum, w) => sum + (w.Humidity || 0), 0) / weatherData.weather.length).toFixed(0),
        rainfall: weatherData.weather.some((w) => w.Rainfall),
        windSpeed: (weatherData.weather.reduce((sum, w) => sum + (w.WindSpeed || 0), 0) / weatherData.weather.length).toFixed(1),
      }
    : null;

  if (trackLoading || controlLoading || weatherLoading) {
    return null;
  }

  // Only show if there are significant events or weather data
  if (groupedEvents.length === 0 && !avgWeather) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Weather Conditions */}
      {avgWeather && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Cloud className="h-5 w-5" />
              Weather Conditions
            </CardTitle>
            <CardDescription>Average conditions during the race</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
              <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                <Thermometer className="h-5 w-5 text-orange-500" />
                <div>
                  <div className="text-xs text-muted-foreground">Air Temp</div>
                  <div className="text-lg font-bold">{avgWeather.airTemp}°C</div>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                <Thermometer className="h-5 w-5 text-red-500" />
                <div>
                  <div className="text-xs text-muted-foreground">Track Temp</div>
                  <div className="text-lg font-bold">{avgWeather.trackTemp}°C</div>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                <Cloud className="h-5 w-5 text-blue-500" />
                <div>
                  <div className="text-xs text-muted-foreground">Humidity</div>
                  <div className="text-lg font-bold">{avgWeather.humidity}%</div>
                </div>
              </div>
              <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/50">
                <Wind className="h-5 w-5 text-cyan-500" />
                <div>
                  <div className="text-xs text-muted-foreground">Wind Speed</div>
                  <div className="text-lg font-bold">{avgWeather.windSpeed} m/s</div>
                </div>
              </div>
              {avgWeather.rainfall && (
                <div className="flex items-center gap-3 p-3 rounded-lg bg-blue-500/20 border-2 border-blue-500">
                  <CloudRain className="h-5 w-5 text-blue-600" />
                  <div>
                    <div className="text-xs text-blue-700 font-bold">Rainfall</div>
                    <div className="text-sm font-semibold text-blue-600">Detected</div>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Race Incidents & Flags */}
      {groupedEvents.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-yellow-500" />
              Race Incidents & Flags
            </CardTitle>
            <CardDescription>
              Yellow flags, safety car periods, and red flags during the race
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {groupedEvents.map((event, index) => {
                const statusInfo = STATUS_CODES[event.status as keyof typeof STATUS_CODES];
                const Icon = statusInfo?.icon || Flag;
                const duration = event.endTime
                  ? event.endTime - event.startTime
                  : null;

                return (
                  <div
                    key={index}
                    className={`flex items-start gap-4 p-4 rounded-lg border-2 ${
                      event.status === 5
                        ? 'bg-red-500/10 border-red-500'
                        : event.status === 4 || event.status === 6
                        ? 'bg-yellow-500/10 border-yellow-500'
                        : 'bg-yellow-400/10 border-yellow-400'
                    }`}
                  >
                    <div
                      className={`flex-shrink-0 w-12 h-12 rounded-full ${
                        statusInfo?.color || 'bg-gray-600'
                      } flex items-center justify-center shadow-lg`}
                    >
                      <Icon className="h-6 w-6 text-white" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1 flex-wrap">
                        <Badge
                          className={`${statusInfo?.color || 'bg-gray-600'} text-white font-bold`}
                        >
                          {statusInfo?.name || event.message}
                        </Badge>
                        <span className="text-sm font-mono font-semibold text-muted-foreground">
                          {formatTime(event.startTime)}
                        </span>
                        {duration && (
                          <span className="text-xs text-muted-foreground">
                            (Duration: {formatTime(duration)})
                          </span>
                        )}
                      </div>
                      {event.message && event.message !== statusInfo?.name && (
                        <div className="text-sm text-muted-foreground mt-1">
                          {event.message}
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Red Flag Messages */}
            {redFlagMessages.length > 0 && (
              <div className="mt-6 pt-6 border-t">
                <h4 className="text-sm font-bold text-red-600 mb-3 flex items-center gap-2">
                  <Zap className="h-4 w-4" />
                  Red Flag Details
                </h4>
                <div className="space-y-2">
                  {redFlagMessages.map((msg, index) => (
                    <div
                      key={index}
                      className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-sm"
                    >
                      <div className="font-semibold text-red-700">{msg.Message}</div>
                      {msg.Category && (
                        <div className="text-xs text-muted-foreground mt-1">
                          Category: {msg.Category}
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
