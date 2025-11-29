'use client';

import { useState, useMemo } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft, Trophy, Timer, Flag, MapPin, Calendar } from 'lucide-react';
import { useRaceResults, useQualifyingResults } from '@/hooks/use-race-results';
import { useLapTimes } from '@/hooks/use-lap-times';
import { LapTimeChart } from '@/components/charts/LapTimeChart';
import { PositionChart } from '@/components/charts/PositionChart';
import { DriverSelector } from '@/components/DriverSelector';
import { EnhancedRaceResults } from '@/components/EnhancedRaceResults';
import { TrackMap } from '@/components/TrackMap';
import { CountryFlag } from '@/components/CountryFlag';
import { SectionHeader } from '@/components/SectionHeader';

export default function RaceDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const year = parseInt(params.year as string);
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

  const [selectedDrivers, setSelectedDrivers] = useState<string[]>([]);

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
    <div className="space-y-8">
      {/* Back Button */}
      <Button
        variant="ghost"
        onClick={() => router.push('/schedule')}
        className="mb-4"
      >
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Schedule
      </Button>

      {/* Enhanced Race Header with Flag Background */}
      <Card className="overflow-hidden border-2 shadow-xl">
        <div className="relative">
          {/* Background Overlay */}
          <div className="absolute inset-0 bg-gradient-to-br from-[var(--f1-dark)] via-[var(--f1-dark-gray)] to-[var(--f1-dark)] opacity-95" />

          {/* Country Flag Background (subtle) */}
          {raceData?.country && (
            <div className="absolute right-0 top-0 bottom-0 w-1/3 opacity-5 overflow-hidden">
              <CountryFlag
                countryName={raceData.country}
                size="xl"
                className="absolute -right-32 top-1/2 -translate-y-1/2 text-[40rem]"
              />
            </div>
          )}

          {/* Content */}
          <div className="relative grid grid-cols-1 lg:grid-cols-3 gap-8 p-8">
            {/* Left: Race Information */}
            <div className="lg:col-span-2 space-y-6 text-white">
              {/* Year and Round */}
              <div className="flex items-center gap-3">
                <CountryFlag
                  countryName={raceData?.country || ''}
                  size="lg"
                  className="shadow-lg"
                />
                <div className="text-sm font-bold text-white/70 uppercase tracking-wider">
                  {year} Formula 1 • Round {round}
                </div>
              </div>

              {/* Race Title */}
              <div>
                <h1 className="text-4xl md:text-6xl font-black tracking-tight text-white drop-shadow-2xl mb-2">
                  {raceData?.event_name || 'Loading...'}
                </h1>
              </div>

              {/* Location and Date */}
              <div className="flex flex-wrap gap-6 text-base">
                {raceData?.circuit && raceData?.country && (
                  <div className="flex items-center gap-2 text-white/90">
                    <MapPin className="h-5 w-5 text-[var(--f1-coral)]" />
                    <span className="font-semibold">{raceData.circuit}, {raceData.country}</span>
                  </div>
                )}
                {formattedDate && (
                  <div className="flex items-center gap-2 text-white/90">
                    <Calendar className="h-5 w-5 text-[var(--f1-coral)]" />
                    <span className="font-semibold">{formattedDate}</span>
                  </div>
                )}
              </div>

              {/* Race Stats */}
              {raceData?.results && raceData.results.length > 0 && (
                <div className="grid grid-cols-3 gap-6 pt-6 border-t border-white/20">
                  <div>
                    <div className="text-xs text-white/60 font-bold uppercase tracking-wider mb-1">
                      Winner
                    </div>
                    <div className="flex items-center gap-2">
                      <Trophy className="h-5 w-5 text-[var(--gold)]" />
                      <span className="text-2xl font-black text-white">
                        {raceData.results[0]?.Abbreviation || 'N/A'}
                      </span>
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-white/60 font-bold uppercase tracking-wider mb-1">
                      Laps
                    </div>
                    <div className="text-2xl font-black text-white">
                      {raceData.results[0]?.Laps || 'N/A'}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-white/60 font-bold uppercase tracking-wider mb-1">
                      Pole Position
                    </div>
                    <div className="text-2xl font-black text-white">
                      {qualifyingData?.results?.[0]?.Abbreviation || 'N/A'}
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Right: Track Map */}
            <div className="flex items-center justify-center lg:justify-end">
              <div className="w-full max-w-sm aspect-square bg-white/10 backdrop-blur-sm rounded-xl p-6 border border-white/20">
                <TrackMap
                  circuitInfo={raceData?.circuit_info || null}
                  className="w-full h-full"
                />
              </div>
            </div>
          </div>
        </div>
      </Card>

      {/* Race Results and Qualifying Tabs */}
      <Tabs defaultValue="race" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2 h-12">
          <TabsTrigger value="race" className="text-base font-bold">
            <Flag className="h-4 w-4 mr-2" />
            Race Results
          </TabsTrigger>
          <TabsTrigger value="qualifying" className="text-base font-bold">
            <Timer className="h-4 w-4 mr-2" />
            Qualifying
          </TabsTrigger>
        </TabsList>

        <TabsContent value="race" className="mt-8 space-y-8">
          {/* Race Results */}
          <div>
            <SectionHeader title="Race Results" subtitle="Final classification and points scored" icon={Flag} />
            {raceLoading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4, 5].map((i) => (
                  <Skeleton key={i} className="h-24 w-full" />
                ))}
              </div>
            ) : raceError ? (
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center py-8 text-muted-foreground">
                    Failed to load race results. This race may not have data available yet.
                  </div>
                </CardContent>
              </Card>
            ) : raceData?.results ? (
              <EnhancedRaceResults results={raceData.results} lapData={raceLapData} />
            ) : (
              <Card>
                <CardContent className="pt-6">
                  <div className="text-center py-8 text-muted-foreground">
                    No race results available
                  </div>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Lap Analysis */}
          {raceLapData?.laps && raceLapData.laps.length > 0 && (
            <div className="space-y-8">
              <SectionHeader
                title="Lap Analysis"
                subtitle="Compare lap times and race positions"
              />

              {allDrivers.length > 0 && (
                <DriverSelector
                  drivers={allDrivers}
                  selectedDrivers={selectedDrivers}
                  onDriverToggle={handleDriverToggle}
                  maxSelection={10}
                />
              )}

              {selectedDrivers.length > 0 && (
                <>
                  <PositionChart
                    laps={raceLapData.laps}
                    drivers={selectedDrivers}
                    title={`Position Changes - ${selectedDrivers.length} Driver${selectedDrivers.length > 1 ? 's' : ''}`}
                  />

                  <LapTimeChart
                    laps={raceLapData.laps}
                    drivers={selectedDrivers}
                    title={`Lap Time Comparison - ${selectedDrivers.length} Driver${selectedDrivers.length > 1 ? 's' : ''}`}
                  />
                </>
              )}
            </div>
          )}
        </TabsContent>

        <TabsContent value="qualifying" className="mt-8">
          <SectionHeader title="Qualifying Results" subtitle="Grid positions and session times" icon={Timer} />
          {qualifyingLoading ? (
            <div className="space-y-3">
              {[1, 2, 3, 4, 5].map((i) => (
                <Skeleton key={i} className="h-20 w-full" />
              ))}
            </div>
          ) : qualifyingError ? (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8 text-muted-foreground">
                  Failed to load qualifying results. This session may not have data available yet.
                </div>
              </CardContent>
            </Card>
          ) : qualifyingData?.results ? (
            <Card>
              <CardContent className="pt-6">
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-20">Pos</TableHead>
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
                          <TableCell>
                            <Badge
                              variant={position <= 3 ? 'default' : 'outline'}
                              className={`w-12 h-12 flex items-center justify-center text-lg font-bold ${
                                position === 1
                                  ? 'podium-1 text-white'
                                  : position === 2
                                  ? 'podium-2 text-white'
                                  : position === 3
                                  ? 'podium-3 text-white'
                                  : ''
                              }`}
                            >
                              {position}
                            </Badge>
                          </TableCell>
                          <TableCell className="font-bold text-lg">
                            {result.Abbreviation || result.Driver}
                          </TableCell>
                          <TableCell className="text-muted-foreground">
                            {result.TeamName || result.Team}
                          </TableCell>
                          <TableCell className="text-right font-mono font-semibold">
                            {result.Q1 || '-'}
                          </TableCell>
                          <TableCell className="text-right font-mono font-semibold">
                            {result.Q2 || '-'}
                          </TableCell>
                          <TableCell className="text-right font-mono font-semibold">
                            {result.Q3 || '-'}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardContent className="pt-6">
                <div className="text-center py-8 text-muted-foreground">
                  No qualifying results available
                </div>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
