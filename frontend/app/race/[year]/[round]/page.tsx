'use client';

import { useState, useMemo } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft, Trophy, Timer, Flag } from 'lucide-react';
import { useRaceResults, useQualifyingResults } from '@/hooks/use-race-results';
import { useLapTimes } from '@/hooks/use-lap-times';
import { LapTimeChart } from '@/components/charts/LapTimeChart';
import { PositionChart } from '@/components/charts/PositionChart';
import { DriverSelector } from '@/components/DriverSelector';
import { EnhancedRaceResults } from '@/components/EnhancedRaceResults';
import { TrackMap } from '@/components/TrackMap';
import { MapPin, Calendar } from 'lucide-react';

export default function RaceDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const year = parseInt(params.year as string);
  // Convert race name from URL format back to normal (e.g., "Bahrain_Grand_Prix" -> "Bahrain Grand Prix")
  const round = (params.round as string).replace(/_/g, ' ');

  const { data: raceData, isLoading: raceLoading, error: raceError } = useRaceResults(year, round);
  const { data: qualifyingData, isLoading: qualifyingLoading, error: qualifyingError } = useQualifyingResults(year, round);
  const { data: raceLapData, isLoading: raceLapLoading } = useLapTimes(year, round, 'R');

  // Get all drivers from race results
  const allDrivers = useMemo(() => {
    if (!raceData?.results) return [];
    return raceData.results.map((r: any) => ({
      abbreviation: r.Abbreviation,
      name: r.FullName || r.Driver,
      team: r.TeamName || r.Team,
    }));
  }, [raceData]);

  // Initialize selected drivers with top 5
  const [selectedDrivers, setSelectedDrivers] = useState<string[]>([]);

  // Set initial selection when data loads
  useMemo(() => {
    if (selectedDrivers.length === 0 && allDrivers.length > 0) {
      setSelectedDrivers(allDrivers.slice(0, 5).map((d: any) => d.abbreviation));
    }
  }, [allDrivers, selectedDrivers.length]);

  const handleDriverToggle = (abbreviation: string) => {
    setSelectedDrivers((prev) =>
      prev.includes(abbreviation)
        ? prev.filter((d) => d !== abbreviation)
        : [...prev, abbreviation]
    );
  };

  // Format date nicely
  const formattedDate = useMemo(() => {
    if (!raceData?.date) return '';
    try {
      const date = new Date(raceData.date);
      return new Intl.DateTimeFormat('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
      }).format(date);
    } catch {
      return raceData.date;
    }
  }, [raceData?.date]);

  return (
    <div className="space-y-6">
      {/* Enhanced Race Header */}
      <div className="relative">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => router.push('/schedule')}
          className="absolute top-4 left-4 z-10"
        >
          <ArrowLeft className="h-5 w-5" />
        </Button>

        <Card className="overflow-hidden">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 p-6">
            {/* Left: Race Information */}
            <div className="lg:col-span-2 space-y-4">
              <div>
                <div className="text-sm text-muted-foreground mb-1">
                  {year} FORMULA 1 • ROUND {round}
                </div>
                <h1 className="text-4xl md:text-5xl font-bold tracking-tight">
                  {raceData?.event_name || 'Loading...'}
                </h1>
              </div>

              <div className="flex flex-wrap gap-4 text-sm">
                {raceData?.circuit && raceData?.country && (
                  <div className="flex items-center gap-2">
                    <MapPin className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{raceData.circuit}, {raceData.country}</span>
                  </div>
                )}
                {formattedDate && (
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-muted-foreground" />
                    <span>{formattedDate}</span>
                  </div>
                )}
              </div>

              {/* Race Stats */}
              {raceData?.results && raceData.results.length > 0 && (
                <div className="grid grid-cols-3 gap-4 pt-4 border-t">
                  <div>
                    <div className="text-xs text-muted-foreground">WINNER</div>
                    <div className="text-lg font-bold">{raceData.results[0]?.Abbreviation || 'N/A'}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">LAPS</div>
                    <div className="text-lg font-bold">{raceData.results[0]?.Laps || 'N/A'}</div>
                  </div>
                  <div>
                    <div className="text-xs text-muted-foreground">POLE POSITION</div>
                    <div className="text-lg font-bold">
                      {qualifyingData?.results?.[0]?.Abbreviation || 'N/A'}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Right: Track Map */}
            <div className="flex items-center justify-center lg:justify-end">
              <div className="w-full max-w-xs aspect-square">
                <TrackMap
                  circuitInfo={raceData?.circuit_info || null}
                  className="w-full h-full"
                />
              </div>
            </div>
          </div>
        </Card>
      </div>

      <Tabs defaultValue="race" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="race">Race Results</TabsTrigger>
          <TabsTrigger value="qualifying">Qualifying</TabsTrigger>
        </TabsList>

        <TabsContent value="race" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Flag className="h-5 w-5" />
                Race Results
              </CardTitle>
              <CardDescription>Final classification and points scored</CardDescription>
            </CardHeader>
            <CardContent>
              {raceLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <Skeleton key={i} className="h-20 w-full" />
                  ))}
                </div>
              ) : raceError ? (
                <div className="text-center py-8 text-muted-foreground">
                  Failed to load race results. This race may not have data available yet.
                </div>
              ) : raceData?.results ? (
                <EnhancedRaceResults results={raceData.results} lapData={raceLapData} />
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No race results available
                </div>
              )}
            </CardContent>
          </Card>

          {/* Lap Time Analysis */}
          <div className="mt-6 space-y-6">
            {raceLapLoading ? (
              <Card>
                <CardContent className="pt-6">
                  <Skeleton className="h-[400px] w-full" />
                </CardContent>
              </Card>
            ) : raceLapData?.laps && raceLapData.laps.length > 0 ? (
              <>
                {/* Driver Selector */}
                {allDrivers.length > 0 && (
                  <DriverSelector
                    drivers={allDrivers}
                    selectedDrivers={selectedDrivers}
                    onDriverToggle={handleDriverToggle}
                    maxSelection={10}
                  />
                )}

                {/* Position Chart */}
                {selectedDrivers.length > 0 && (
                  <PositionChart
                    laps={raceLapData.laps}
                    drivers={selectedDrivers}
                    title={`Position Changes - ${selectedDrivers.length} Driver${selectedDrivers.length > 1 ? 's' : ''}`}
                  />
                )}

                {/* Lap Time Chart */}
                {selectedDrivers.length > 0 && (
                  <LapTimeChart
                    laps={raceLapData.laps}
                    drivers={selectedDrivers}
                    title={`Lap Time Comparison - ${selectedDrivers.length} Driver${selectedDrivers.length > 1 ? 's' : ''}`}
                  />
                )}
              </>
            ) : null}
          </div>
        </TabsContent>

        <TabsContent value="qualifying" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Timer className="h-5 w-5" />
                Qualifying Results
              </CardTitle>
              <CardDescription>Grid positions and lap times</CardDescription>
            </CardHeader>
            <CardContent>
              {qualifyingLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : qualifyingError ? (
                <div className="text-center py-8 text-muted-foreground">
                  Failed to load qualifying results. This session may not have data available yet.
                </div>
              ) : qualifyingData?.results ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-16">Pos</TableHead>
                      <TableHead>Driver</TableHead>
                      <TableHead>Team</TableHead>
                      <TableHead className="text-right">Q1</TableHead>
                      <TableHead className="text-right">Q2</TableHead>
                      <TableHead className="text-right">Q3</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {qualifyingData.results.map((result: any, index: number) => {
                      const position = result.Position || index + 1;
                      return (
                        <TableRow key={result.DriverNumber || index}>
                          <TableCell className="font-bold">
                            <Badge
                              variant={position <= 3 ? 'default' : 'outline'}
                              className={
                                position === 1
                                  ? 'bg-yellow-600'
                                  : position === 2
                                  ? 'bg-gray-400'
                                  : position === 3
                                  ? 'bg-amber-600'
                                  : ''
                              }
                            >
                              {position}
                            </Badge>
                          </TableCell>
                          <TableCell className="font-semibold">
                            {result.Abbreviation || result.Driver}
                          </TableCell>
                          <TableCell>{result.TeamName || result.Team}</TableCell>
                          <TableCell className="text-right font-mono text-sm">
                            {result.Q1 || '-'}
                          </TableCell>
                          <TableCell className="text-right font-mono text-sm">
                            {result.Q2 || '-'}
                          </TableCell>
                          <TableCell className="text-right font-mono text-sm">
                            {result.Q3 || '-'}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No qualifying results available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
