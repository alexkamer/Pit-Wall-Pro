'use client';

import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft, Trophy, Timer, Flag } from 'lucide-react';
import { useRaceResults, useQualifyingResults } from '@/hooks/use-race-results';

export default function RaceDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const year = parseInt(params.year as string);
  const round = params.round as string;

  const { data: raceData, isLoading: raceLoading, error: raceError } = useRaceResults(year, round);
  const { data: qualifyingData, isLoading: qualifyingLoading, error: qualifyingError } = useQualifyingResults(year, round);

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-4">
        <Button variant="ghost" size="icon" onClick={() => router.push('/schedule')}>
          <ArrowLeft className="h-5 w-5" />
        </Button>
        <div className="flex-1">
          <h1 className="text-4xl font-bold tracking-tight">
            Race Details
          </h1>
          <p className="text-muted-foreground mt-2">
            {year} Season - Round {round}
          </p>
        </div>
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
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : raceError ? (
                <div className="text-center py-8 text-muted-foreground">
                  Failed to load race results. This race may not have data available yet.
                </div>
              ) : raceData?.results ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-16">Pos</TableHead>
                      <TableHead>Driver</TableHead>
                      <TableHead>Team</TableHead>
                      <TableHead className="text-right">Time/Gap</TableHead>
                      <TableHead className="text-right">Points</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {raceData.results.map((result: any, index: number) => {
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
                          <TableCell className="text-right">
                            {result.Time || result.Status || '-'}
                          </TableCell>
                          <TableCell className="text-right font-bold">
                            {result.Points || '0'}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No race results available
                </div>
              )}
            </CardContent>
          </Card>
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
