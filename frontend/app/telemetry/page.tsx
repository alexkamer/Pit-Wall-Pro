'use client';

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Activity, BarChart3, Gauge } from 'lucide-react';

export default function TelemetryPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-4xl font-bold tracking-tight flex items-center gap-3">
          <Activity className="h-10 w-10 text-blue-600" />
          Telemetry Analysis
        </h1>
        <p className="text-muted-foreground mt-2">
          In-depth car telemetry and performance data
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader>
            <Gauge className="h-8 w-8 mb-2 text-blue-600" />
            <CardTitle>Speed Traces</CardTitle>
            <CardDescription>
              Compare driver speeds throughout the lap
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Visualize speed, throttle, and brake data on a circuit map
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <BarChart3 className="h-8 w-8 mb-2 text-green-600" />
            <CardTitle>Lap Comparisons</CardTitle>
            <CardDescription>
              Head-to-head lap time analysis
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Compare sector times and identify where time is gained or lost
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <Activity className="h-8 w-8 mb-2 text-purple-600" />
            <CardTitle>Gear & RPM</CardTitle>
            <CardDescription>
              Transmission and engine data
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              Analyze gear changes and RPM throughout the lap
            </p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Coming Soon</CardTitle>
          <CardDescription>
            Interactive telemetry visualization is under development
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <p className="text-muted-foreground">
              The telemetry page will include:
            </p>
            <ul className="list-disc list-inside space-y-2 text-sm text-muted-foreground">
              <li>Interactive speed trace charts</li>
              <li>Throttle and brake application visualization</li>
              <li>Gear change indicators</li>
              <li>Driver comparison overlays</li>
              <li>Sector-by-sector analysis</li>
              <li>DRS usage tracking</li>
            </ul>
            <p className="text-sm text-muted-foreground mt-4">
              Use the API directly at{' '}
              <code className="bg-muted px-2 py-1 rounded">
                http://localhost:8000/api/session/&#123;year&#125;/&#123;race&#125;/&#123;session&#125;/telemetry
              </code>
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
