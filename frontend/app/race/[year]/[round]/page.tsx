'use client';

import { useState, useMemo } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
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
import { RaceEvents } from '@/components/RaceEvents';

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

  const formatQualifyingTime = (time: string | undefined): string => {
    if (!time) return '-';

    const timeStr = String(time);

    // If already formatted (contains colon), return as-is
    if (timeStr.includes(':')) {
      return timeStr;
    }

    // Parse as seconds
    const totalSeconds = parseFloat(timeStr);
    if (isNaN(totalSeconds)) {
      return timeStr;
    }

    // Format as MM:SS.mmm
    const minutes = Math.floor(totalSeconds / 60);
    const seconds = Math.floor(totalSeconds % 60);
    const milliseconds = Math.floor((totalSeconds % 1) * 1000);

    return `${minutes}:${String(seconds).padStart(2, '0')}.${String(milliseconds).padStart(3, '0')}`;
  };

  const getDriverPhoto = (result: any): string => {
    if (result.HeadshotUrl) {
      return result.HeadshotUrl;
    }
    const abbr = result.Abbreviation || result.Driver || 'DRV';
    return `https://ui-avatars.com/api/?name=${abbr}&background=random&size=128`;
  };

  const getTeamLogo = (teamName: string): string => {
    const teamMap: Record<string, string> = {
      'Red Bull Racing': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/red-bull-racing-logo.png',
      'Ferrari': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/ferrari-logo.png',
      'Mercedes': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/mercedes-logo.png',
      'McLaren': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/mclaren-logo.png',
      'Aston Martin': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/aston-martin-logo.png',
      'Alpine': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/alpine-logo.png',
      'Williams': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/williams-logo.png',
      'RB': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/rb-logo.png',
      'Racing Bulls': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/rb-logo.png',
      'Kick Sauber': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/kick-sauber-logo.png',
      'Haas F1 Team': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/haas-f1-team-logo.png',
    };
    return teamMap[teamName] || '';
  };

  const getTeamColor = (teamName: string): string => {
    // Official F1 team colors
    const teamColors: Record<string, string> = {
      'Red Bull Racing': '#3671C6',      // Red Bull Blue
      'Ferrari': '#E8002D',               // Ferrari Red
      'Mercedes': '#27F4D2',              // Mercedes Teal/Turquoise
      'McLaren': '#FF8000',               // McLaren Orange
      'Aston Martin': '#229971',          // Aston Martin Green
      'Alpine': '#FF87BC',                // Alpine Pink
      'Williams': '#64C4FF',              // Williams Blue
      'RB': '#6692FF',                    // RB/AlphaTauri Blue
      'Racing Bulls': '#6692FF',          // Racing Bulls Blue
      'Kick Sauber': '#52E252',           // Sauber Green
      'Haas F1 Team': '#B6BABD',          // Haas Grey/White
    };
    return teamColors[teamName] || '#888888';
  };

  const parseTimeToSeconds = (time: string | undefined): number | null => {
    if (!time || time === 'NaT' || time === '-') return null;
    const timeStr = String(time);

    // If already in MM:SS.mmm format
    if (timeStr.includes(':')) {
      const parts = timeStr.split(':');
      const minutes = parseInt(parts[0]);
      const seconds = parseFloat(parts[1]);
      return minutes * 60 + seconds;
    }

    // If in seconds
    const totalSeconds = parseFloat(timeStr);
    return isNaN(totalSeconds) ? null : totalSeconds;
  };

  const getGapToPole = (time: string | undefined, poleTime: string | undefined): string => {
    const currentSeconds = parseTimeToSeconds(time);
    const poleSeconds = parseTimeToSeconds(poleTime);

    if (!currentSeconds || !poleSeconds) return '';
    if (currentSeconds === poleSeconds) return '';

    const gap = currentSeconds - poleSeconds;
    return `+${gap.toFixed(3)}`;
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
          {/* Race Events (Flags & Weather) */}
          {!raceLoading && !raceError && raceData?.results && (
            <RaceEvents year={year} race={round} />
          )}

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
                      const driverPhoto = getDriverPhoto(result);
                      const teamName = result.TeamName || result.Team || '';
                      const teamLogo = getTeamLogo(teamName);
                      const teamColor = getTeamColor(teamName);

                      // Determine fastest times for highlighting
                      const fastestQ1 = qualifyingData.results[0]?.Q1;
                      const fastestQ2 = qualifyingData.results.filter((r: any) => r.Q2 && r.Q2 !== 'NaT').sort((a: any, b: any) => parseTimeToSeconds(a.Q2)! - parseTimeToSeconds(b.Q2)!)[0]?.Q2;
                      const fastestQ3 = qualifyingData.results.filter((r: any) => r.Q3 && r.Q3 !== 'NaT').sort((a: any, b: any) => parseTimeToSeconds(a.Q3)! - parseTimeToSeconds(b.Q3)!)[0]?.Q3;

                      const isQ1Fastest = result.Q1 === fastestQ1 && result.Q1 && result.Q1 !== 'NaT';
                      const isQ2Fastest = result.Q2 === fastestQ2 && result.Q2 && result.Q2 !== 'NaT';
                      const isQ3Fastest = result.Q3 === fastestQ3 && result.Q3 && result.Q3 !== 'NaT';

                      // Determine elimination session
                      const eliminatedInQ1 = position > 15;
                      const eliminatedInQ2 = position > 10 && position <= 15;

                      return (
                        <TableRow
                          key={result.DriverNumber || index}
                          className={eliminatedInQ1 ? 'opacity-60' : eliminatedInQ2 ? 'opacity-75' : ''}
                        >
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
                          <TableCell>
                            <div className="flex items-center gap-3">
                              <Avatar className="h-12 w-12 border-2">
                                <AvatarImage src={driverPhoto} alt={result.Abbreviation} />
                                <AvatarFallback>{result.Abbreviation}</AvatarFallback>
                              </Avatar>
                              <div>
                                <div className="font-bold text-lg">{result.Abbreviation || result.Driver}</div>
                                <div className="text-sm text-muted-foreground">{result.FullName || result.Driver}</div>
                              </div>
                            </div>
                          </TableCell>
                          <TableCell>
                            <div className="flex items-center gap-2">
                              {teamLogo && (
                                <div
                                  className="h-8 w-8 rounded flex items-center justify-center p-1"
                                  style={{ backgroundColor: teamColor }}
                                >
                                  <img
                                    src={teamLogo}
                                    alt={teamName}
                                    className="h-full w-full object-contain brightness-0 invert"
                                  />
                                </div>
                              )}
                              <span className="text-muted-foreground">{teamName}</span>
                            </div>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="font-mono font-semibold">
                              <div className={isQ1Fastest ? 'text-purple-600 font-bold' : ''}>
                                {formatQualifyingTime(result.Q1)}
                              </div>
                              {position === 1 && result.Q1 && result.Q1 !== 'NaT' && (
                                <div className="text-xs text-muted-foreground">Pole</div>
                              )}
                              {position > 1 && result.Q1 && result.Q1 !== 'NaT' && (
                                <div className="text-xs text-muted-foreground">{getGapToPole(result.Q1, fastestQ1)}</div>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="font-mono font-semibold">
                              <div className={isQ2Fastest ? 'text-purple-600 font-bold' : ''}>
                                {formatQualifyingTime(result.Q2)}
                              </div>
                              {position <= 15 && result.Q2 && result.Q2 !== 'NaT' && (
                                <div className="text-xs text-muted-foreground">{getGapToPole(result.Q2, fastestQ2)}</div>
                              )}
                            </div>
                          </TableCell>
                          <TableCell className="text-right">
                            <div className="font-mono font-semibold">
                              <div className={isQ3Fastest ? 'text-purple-600 font-bold' : ''}>
                                {formatQualifyingTime(result.Q3)}
                              </div>
                              {position <= 10 && result.Q3 && result.Q3 !== 'NaT' && (
                                <div className="text-xs text-muted-foreground">{getGapToPole(result.Q3, fastestQ3)}</div>
                              )}
                            </div>
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
