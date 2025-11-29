'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Timer } from 'lucide-react';

interface LapTimeData {
  Driver: string;
  LapNumber: number;
  LapTime: number;
  Compound?: string;
  TyreLife?: number;
}

interface LapTimeChartProps {
  laps: LapTimeData[];
  drivers?: string[];
  title?: string;
}

// Team colors for drivers
const DRIVER_COLORS: Record<string, string> = {
  VER: '#3671C6',
  PER: '#3671C6',
  HAM: '#27F4D2',
  RUS: '#27F4D2',
  LEC: '#E8002D',
  SAI: '#E8002D',
  NOR: '#FF8000',
  PIA: '#FF8000',
  ALO: '#229971',
  STR: '#229971',
  TSU: '#6692FF',
  RIC: '#6692FF',
  ALB: '#64C4FF',
  SAR: '#64C4FF',
  HUL: '#B6BABD',
  MAG: '#B6BABD',
  OCO: '#FF87BC',
  GAS: '#FF87BC',
  ZHO: '#52E252',
  BOT: '#52E252',
};

// Tire compound colors (F1 official colors)
const TIRE_COLORS: Record<string, string> = {
  SOFT: '#FF0000',      // Red
  MEDIUM: '#FFD700',    // Yellow
  HARD: '#FFFFFF',      // White
  INTERMEDIATE: '#00FF00', // Green
  WET: '#0000FF',       // Blue
};

// Tire compound with text labels for better visibility
const TireIcon = ({ compound }: { compound: string }) => {
  const color = TIRE_COLORS[compound] || '#888888';
  const textColor = compound === 'HARD' ? '#000000' : '#FFFFFF';
  const label = compound.charAt(0); // S, M, H, I, W

  return (
    <svg width="24" height="24" viewBox="0 0 24 24">
      <circle cx="12" cy="12" r="10" fill={color} stroke="currentColor" strokeWidth="2" />
      <text
        x="12"
        y="12"
        textAnchor="middle"
        dominantBaseline="central"
        fill={textColor}
        fontSize="12"
        fontWeight="bold"
      >
        {label}
      </text>
    </svg>
  );
};

const formatLapTime = (seconds: number): string => {
  if (!seconds || seconds === 0) return '-';
  const minutes = Math.floor(seconds / 60);
  const secs = (seconds % 60).toFixed(3);
  return `${minutes}:${secs.padStart(6, '0')}`;
};

// Detect if a lap is a pit stop lap (outlier)
const isPitStopLap = (lap: LapTimeData, driverLaps: LapTimeData[]): boolean => {
  if (!lap.LapTime) return false;

  // Exclude first 3 laps - these are formation lap and race start, not pit stops
  if (lap.LapNumber <= 3) return false;

  // Method 1: Check if TyreLife is 1 (just left pit lane) AND we're past lap 3
  if (lap.TyreLife === 1 && lap.LapNumber > 3) return true;

  // Method 2: Check if lap time is significantly higher than median
  const validLapTimes = driverLaps
    .filter(l => l.LapTime && l.LapTime > 0 && l.LapNumber > 3) // Exclude first 3 laps from median calculation
    .map(l => l.LapTime)
    .sort((a, b) => a - b);

  if (validLapTimes.length < 3) return false;

  const median = validLapTimes[Math.floor(validLapTimes.length / 2)];
  // If lap time is 15% or more slower than median, likely a pit stop
  return lap.LapTime > median * 1.15;
};

// Custom dot component to show tire compounds
const CustomDot = (props: any) => {
  const { cx, cy, payload, dataKey } = props;

  // Find the compound for this driver at this lap
  const compound = payload[`${dataKey}_compound`];

  if (!cx || !cy) return null;

  const fillColor = compound ? TIRE_COLORS[compound] || '#888888' : '#888888';

  return (
    <circle
      cx={cx}
      cy={cy}
      r={3}
      fill={fillColor}
      stroke={props.stroke}
      strokeWidth={1.5}
    />
  );
};

export function LapTimeChart({ laps, drivers, title = 'Lap Time Comparison' }: LapTimeChartProps) {
  // Group laps by driver
  const driverLaps: Record<string, LapTimeData[]> = {};

  laps.forEach(lap => {
    if (!lap.LapTime || lap.LapTime === 0) return; // Skip invalid lap times

    if (!driverLaps[lap.Driver]) {
      driverLaps[lap.Driver] = [];
    }
    driverLaps[lap.Driver].push(lap);
  });

  // Filter to selected drivers if specified
  const selectedDrivers = drivers || Object.keys(driverLaps).slice(0, 5); // Default to first 5

  // Track pit stops for each driver
  const pitStops: Record<string, number[]> = {};
  selectedDrivers.forEach(driver => {
    pitStops[driver] = [];
    const laps = driverLaps[driver] || [];
    laps.forEach(lap => {
      if (isPitStopLap(lap, laps)) {
        pitStops[driver].push(lap.LapNumber);
      }
    });
  });

  // Create chart data with one point per lap, filtering out pit stop laps
  const maxLapNumber = Math.max(...laps.map(l => l.LapNumber));
  const chartData: any[] = [];

  for (let lapNum = 1; lapNum <= maxLapNumber; lapNum++) {
    const point: any = { lap: lapNum };

    selectedDrivers.forEach(driver => {
      const lap = driverLaps[driver]?.find(l => l.LapNumber === lapNum);
      if (lap && lap.LapTime) {
        // Skip pit stop laps for cleaner visualization
        if (!isPitStopLap(lap, driverLaps[driver] || [])) {
          point[driver] = lap.LapTime;
          point[`${driver}_compound`] = lap.Compound; // Store compound info
        }
      }
    });

    chartData.push(point);
  }

  // Get unique compounds used in this race
  const usedCompounds = new Set<string>();
  laps.forEach(lap => {
    if (lap.Compound) usedCompounds.add(lap.Compound);
  });

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Timer className="h-5 w-5" />
            {title}
          </CardTitle>
          <CardDescription>Track lap-by-lap performance</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            No lap time data available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Timer className="h-5 w-5" />
          {title}
        </CardTitle>
        <CardDescription>
          Lap-by-lap performance comparison (lower is faster)
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Tire Compound Legend */}
        {usedCompounds.size > 0 && (
          <div className="flex items-center justify-center gap-4 mb-4 p-3 bg-muted/50 rounded-lg">
            <span className="text-sm font-medium">Tire Compounds:</span>
            {Array.from(usedCompounds).map(compound => (
              <div key={compound} className="flex items-center gap-2">
                <TireIcon compound={compound} />
                <span className="text-sm capitalize">{compound.toLowerCase()}</span>
              </div>
            ))}
          </div>
        )}

        {/* Pit Stop Summary */}
        {Object.keys(pitStops).some(driver => pitStops[driver].length > 0) && (
          <div className="mb-4 p-3 bg-muted/30 rounded-lg">
            <div className="text-sm font-medium mb-2">Pit Stops (laps excluded from chart):</div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2">
              {selectedDrivers.map(driver => {
                const stops = pitStops[driver] || [];
                if (stops.length === 0) return null;
                return (
                  <div key={driver} className="text-xs">
                    <span
                      className="inline-block w-2 h-2 rounded-full mr-1"
                      style={{ backgroundColor: DRIVER_COLORS[driver] || '#888888' }}
                    />
                    <span className="font-medium">{driver}:</span> L{stops.join(', L')}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />
            <XAxis
              dataKey="lap"
              label={{ value: 'Lap Number', position: 'insideBottom', offset: -5 }}
              className="text-xs"
            />
            <YAxis
              tickFormatter={formatLapTime}
              label={{ value: 'Lap Time', angle: -90, position: 'insideLeft' }}
              className="text-xs"
              domain={['auto', 'auto']}
            />
            <Tooltip
              formatter={(value: any) => formatLapTime(value)}
              labelFormatter={(label) => `Lap ${label}`}
              contentStyle={{
                backgroundColor: 'hsl(var(--background))',
                border: '1px solid hsl(var(--border))',
                borderRadius: '6px'
              }}
            />
            <Legend />
            {selectedDrivers.map(driver => (
              <Line
                key={driver}
                type="monotone"
                dataKey={driver}
                stroke={DRIVER_COLORS[driver] || '#888888'}
                strokeWidth={2}
                dot={<CustomDot />}
                activeDot={{ r: 5 }}
                connectNulls
              />
            ))}
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}
