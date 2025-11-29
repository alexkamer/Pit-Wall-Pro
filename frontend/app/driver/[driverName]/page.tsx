'use client';

import { useParams, useRouter } from 'next/navigation';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { ArrowLeft, Trophy, TrendingUp, TrendingDown, Minus } from 'lucide-react';
import { useDriverDetails } from '@/hooks/use-driver-details';

export default function DriverPage() {
  const params = useParams();
  const router = useRouter();
  const driverName = params.driverName as string;

  const { data, isLoading, error } = useDriverDetails(driverName, 2024);

  if (isLoading) {
    return (
      <div className="space-y-8">
        <Skeleton className="h-12 w-64" />
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-96" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="space-y-8">
        <Button variant="ghost" onClick={() => router.push('/standings')}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Standings
        </Button>
        <Card>
          <CardContent className="pt-6">
            <div className="text-center py-8 text-muted-foreground">
              Failed to load driver data. Driver may not be found or data is unavailable.
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  const { driver, season_stats, race_results } = data;

  // Calculate qualifying vs race performance indicator
  const getPerformanceIndicator = () => {
    if (season_stats.avg_qualifying_position && season_stats.avg_race_position) {
      const diff = season_stats.avg_race_position - season_stats.avg_qualifying_position;
      if (diff < -0.5) {
        return { icon: TrendingUp, text: 'Strong race pace', color: 'text-green-600' };
      } else if (diff > 0.5) {
        return { icon: TrendingDown, text: 'Loses positions in races', color: 'text-red-600' };
      } else {
        return { icon: Minus, text: 'Consistent performance', color: 'text-blue-600' };
      }
    }
    return null;
  };

  const performanceIndicator = getPerformanceIndicator();

  return (
    <div className="space-y-8">
      {/* Back Button */}
      <Button variant="ghost" onClick={() => router.push('/standings')}>
        <ArrowLeft className="mr-2 h-4 w-4" />
        Back to Standings
      </Button>

      {/* Driver Header */}
      <div className="flex items-center gap-6">
        <div className="flex-1">
          <h1 className="text-4xl font-black tracking-tight mb-2">
            {driver.name}
          </h1>
          <div className="flex items-center gap-4 text-muted-foreground">
            <span className="text-lg font-semibold">{driver.team}</span>
            <span className="text-lg">#{driver.number}</span>
            <Badge variant="outline" className="text-lg px-3 py-1">{driver.abbreviation}</Badge>
          </div>
        </div>
      </div>

      {/* Season Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Championship Position</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {season_stats.championship_position ? `P${season_stats.championship_position}` : 'N/A'}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Total Points</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{season_stats.points}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {season_stats.races_completed} races
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Wins / Podiums</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">
              {season_stats.wins} / {season_stats.podiums}
            </div>
            <p className="text-xs text-muted-foreground mt-1">
              {((season_stats.podiums / season_stats.races_completed) * 100).toFixed(0)}% podium rate
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">Avg Positions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              Q: {season_stats.avg_qualifying_position || 'N/A'} / R: {season_stats.avg_race_position || 'N/A'}
            </div>
            {performanceIndicator && (
              <div className={`flex items-center gap-1 mt-1 text-xs ${performanceIndicator.color}`}>
                <performanceIndicator.icon className="h-3 w-3" />
                <span>{performanceIndicator.text}</span>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Race Results Table */}
      <Card>
        <CardHeader>
          <CardTitle>2024 Season Results</CardTitle>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-16">Rd</TableHead>
                <TableHead>Race</TableHead>
                <TableHead>Circuit</TableHead>
                <TableHead>Date</TableHead>
                <TableHead className="text-center">Grid</TableHead>
                <TableHead className="text-center">Finish</TableHead>
                <TableHead className="text-center">Positions</TableHead>
                <TableHead className="text-right">Points</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {race_results.map((result: any) => {
                const positionsGained = result.grid_position && result.finish_position
                  ? result.grid_position - result.finish_position
                  : null;

                return (
                  <TableRow key={result.round}>
                    <TableCell className="font-medium">{result.round}</TableCell>
                    <TableCell className="font-semibold">{result.race_name}</TableCell>
                    <TableCell className="text-muted-foreground">{result.circuit}</TableCell>
                    <TableCell className="text-muted-foreground text-sm">{result.date}</TableCell>
                    <TableCell className="text-center">
                      <Badge variant="outline">{result.grid_position || 'N/A'}</Badge>
                    </TableCell>
                    <TableCell className="text-center">
                      <Badge
                        variant={result.finish_position === 1 ? 'default' : 'outline'}
                        className={
                          result.finish_position === 1 ? 'bg-[var(--gold)] text-black hover:bg-[var(--gold)]' :
                          result.finish_position === 2 ? 'bg-[var(--silver)] text-black hover:bg-[var(--silver)]' :
                          result.finish_position === 3 ? 'bg-[var(--bronze)] text-black hover:bg-[var(--bronze)]' :
                          ''
                        }
                      >
                        {result.finish_position || 'DNF'}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-center">
                      {positionsGained !== null && (
                        <span className={
                          positionsGained > 0 ? 'text-green-600 font-semibold' :
                          positionsGained < 0 ? 'text-red-600 font-semibold' :
                          'text-muted-foreground'
                        }>
                          {positionsGained > 0 ? `+${positionsGained}` : positionsGained}
                        </span>
                      )}
                    </TableCell>
                    <TableCell className="text-right font-semibold">{result.points}</TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  );
}
