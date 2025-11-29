'use client';

import { useState } from 'react';
import { useDriverStandings, useConstructorStandings } from '@/hooks/use-standings';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Trophy, Calendar } from 'lucide-react';

// Generate years from 1950 (first F1 season) to current year + 1
const currentYear = new Date().getFullYear();
const FIRST_F1_SEASON = 1950;
const AVAILABLE_YEARS = Array.from(
  { length: currentYear + 1 - FIRST_F1_SEASON + 1 },
  (_, i) => currentYear + 1 - i
);

export default function StandingsPage() {
  const [selectedYear, setSelectedYear] = useState<number>(2025);
  const { data: driversData, isLoading: driversLoading } = useDriverStandings(selectedYear);
  const { data: constructorsData, isLoading: constructorsLoading } = useConstructorStandings(selectedYear);

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between">
        <div>
          <h1 className="text-4xl font-bold tracking-tight flex items-center gap-3">
            <Trophy className="h-10 w-10 text-yellow-600" />
            Championship Standings
          </h1>
          <p className="text-muted-foreground mt-2">
            {selectedYear} Formula 1 World Championship standings
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Calendar className="h-5 w-5 text-muted-foreground" />
          <Select value={selectedYear.toString()} onValueChange={(value) => setSelectedYear(parseInt(value))}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Select year" />
            </SelectTrigger>
            <SelectContent className="max-h-[300px] overflow-y-auto">
              {AVAILABLE_YEARS.map((year) => (
                <SelectItem key={year} value={year.toString()}>
                  {year} Season
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <Tabs defaultValue="drivers" className="w-full">
        <TabsList className="grid w-full max-w-md grid-cols-2">
          <TabsTrigger value="drivers">Drivers</TabsTrigger>
          <TabsTrigger value="constructors">Constructors</TabsTrigger>
        </TabsList>

        <TabsContent value="drivers" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Driver Standings</CardTitle>
              <CardDescription>Current championship positions and points</CardDescription>
            </CardHeader>
            <CardContent>
              {driversLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : driversData?.standings ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-16">Pos</TableHead>
                      <TableHead>Driver</TableHead>
                      <TableHead className="text-right">Points</TableHead>
                      <TableHead className="text-right">Wins</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {driversData.standings.map((entry: any, index: number) => {
                      const records = entry.records?.[0];
                      const stats = records?.stats || [];
                      const points = stats.find((s: any) => s.name === 'championshipPts') || {};
                      const wins = stats.find((s: any) => s.name === 'wins') || {};
                      const rank = stats.find((s: any) => s.name === 'rank') || {};
                      const position = parseInt(rank.displayValue || (index + 1).toString());
                      const driverName = entry.athlete?.displayName || entry.athlete?.fullName || `Driver ${position}`;

                      return (
                        <TableRow key={entry.athlete?.$ref || index}>
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
                            {driverName}
                          </TableCell>
                          <TableCell className="text-right font-bold">
                            {points.displayValue || '0'}
                          </TableCell>
                          <TableCell className="text-right">
                            {wins.displayValue || '0'}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No driver standings data available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="constructors" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Constructor Standings</CardTitle>
              <CardDescription>Team championship positions and points</CardDescription>
            </CardHeader>
            <CardContent>
              {constructorsLoading ? (
                <div className="space-y-3">
                  {[1, 2, 3, 4, 5].map((i) => (
                    <Skeleton key={i} className="h-16 w-full" />
                  ))}
                </div>
              ) : constructorsData?.standings ? (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead className="w-16">Pos</TableHead>
                      <TableHead>Team</TableHead>
                      <TableHead className="text-right">Points</TableHead>
                      <TableHead className="text-right">Wins</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {constructorsData.standings.map((entry: any, index: number) => {
                      const records = entry.records?.[0];
                      const stats = records?.stats || [];
                      const points = stats.find((s: any) => s.name === 'points') || {};
                      const wins = stats.find((s: any) => s.name === 'wins') || {};
                      const rank = stats.find((s: any) => s.name === 'rank') || {};
                      const position = parseInt(rank.displayValue || (index + 1).toString());
                      const teamName = entry.manufacturer?.displayName || entry.manufacturer?.name || `Team ${position}`;

                      return (
                        <TableRow key={entry.manufacturer?.$ref || index}>
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
                            {teamName}
                          </TableCell>
                          <TableCell className="text-right font-bold">
                            {points.displayValue || '0'}
                          </TableCell>
                          <TableCell className="text-right">
                            {wins.displayValue || '0'}
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No constructor standings data available
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
