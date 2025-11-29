'use client';

import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { TrendingUp } from 'lucide-react';

interface LapData {
  Driver: string;
  LapNumber: number;
  Position: number;
  LapTime?: number;
}

interface PositionChartProps {
  laps: LapData[];
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

export function PositionChart({ laps, drivers, title = 'Race Position Changes' }: PositionChartProps) {
  // Group laps by driver
  const driverLaps: Record<string, LapData[]> = {};

  laps.forEach(lap => {
    if (!lap.Position || lap.Position === 0) return; // Skip invalid positions

    if (!driverLaps[lap.Driver]) {
      driverLaps[lap.Driver] = [];
    }
    driverLaps[lap.Driver].push(lap);
  });

  // Filter to selected drivers if specified
  const selectedDrivers = drivers || Object.keys(driverLaps).slice(0, 5);

  // Create chart data with one point per lap
  const maxLapNumber = Math.max(...laps.map(l => l.LapNumber));
  const chartData: any[] = [];

  for (let lapNum = 1; lapNum <= maxLapNumber; lapNum++) {
    const point: any = { lap: lapNum };

    selectedDrivers.forEach(driver => {
      const lap = driverLaps[driver]?.find(l => l.LapNumber === lapNum);
      if (lap && lap.Position) {
        point[driver] = lap.Position;
      }
    });

    chartData.push(point);
  }

  // Calculate position changes for summary
  const positionChanges: Record<string, { start: number; end: number; change: number }> = {};
  selectedDrivers.forEach(driver => {
    const dLaps = driverLaps[driver] || [];
    if (dLaps.length > 0) {
      const validLaps = dLaps.filter(l => l.Position && l.Position > 0);
      if (validLaps.length > 0) {
        const startPos = validLaps[0].Position;
        const endPos = validLaps[validLaps.length - 1].Position;
        positionChanges[driver] = {
          start: startPos,
          end: endPos,
          change: startPos - endPos, // Positive means gained positions
        };
      }
    }
  });

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="h-5 w-5" />
            {title}
          </CardTitle>
          <CardDescription>Track position changes throughout the race</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-muted-foreground">
            No position data available
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <TrendingUp className="h-5 w-5" />
          {title}
        </CardTitle>
        <CardDescription>
          Track position changes lap-by-lap (P1 at top)
        </CardDescription>
      </CardHeader>
      <CardContent>
        {/* Position Changes Summary */}
        {Object.keys(positionChanges).length > 0 && (
          <div className="mb-4 p-3 bg-muted/30 rounded-lg">
            <div className="text-sm font-medium mb-2">Position Changes:</div>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-2">
              {selectedDrivers.map(driver => {
                const change = positionChanges[driver];
                if (!change) return null;
                const gained = change.change > 0;
                const lost = change.change < 0;
                return (
                  <div key={driver} className="text-xs">
                    <span
                      className="inline-block w-2 h-2 rounded-full mr-1"
                      style={{ backgroundColor: DRIVER_COLORS[driver] || '#888888' }}
                    />
                    <span className="font-medium">{driver}:</span> P{change.start} → P{change.end}
                    {change.change !== 0 && (
                      <span className={gained ? 'text-green-500 ml-1' : lost ? 'text-red-500 ml-1' : ''}>
                        {gained ? '+' : ''}{change.change}
                      </span>
                    )}
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
              reversed
              domain={[1, 20]}
              ticks={[1, 5, 10, 15, 20]}
              label={{ value: 'Position', angle: -90, position: 'insideLeft' }}
              className="text-xs"
            />
            <Tooltip
              formatter={(value: any) => `P${value}`}
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
                type="stepAfter"
                dataKey={driver}
                stroke={DRIVER_COLORS[driver] || '#888888'}
                strokeWidth={2}
                dot={{ r: 2 }}
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
