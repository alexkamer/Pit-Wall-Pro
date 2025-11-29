'use client';

import { useSchedule } from '@/hooks/use-schedule';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Calendar, MapPin, Clock } from 'lucide-react';
import { format, parseISO, isFuture, isPast } from 'date-fns';

export default function Home() {
  const { data, isLoading, error } = useSchedule(2025);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-4xl font-bold">F1 2025 Season</h1>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i}>
              <CardHeader>
                <Skeleton className="h-6 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
              </CardHeader>
              <CardContent>
                <Skeleton className="h-20 w-full" />
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Error Loading Schedule</CardTitle>
            <CardDescription>Failed to load race schedule. Please try again later.</CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  const events = data?.events || [];
  const upcomingRaces = events.filter((event: any) =>
    event.EventDate && isFuture(parseISO(event.EventDate))
  ).slice(0, 6);

  const nextRace = upcomingRaces[0];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-4xl font-bold tracking-tight">F1 2025 Season</h1>
        <p className="text-muted-foreground mt-2">
          Live race results, standings, and telemetry analysis
        </p>
      </div>

      {nextRace && (
        <Card className="border-red-600 border-2">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-2xl">Next Race</CardTitle>
                <CardDescription className="text-lg mt-2">
                  {nextRace.OfficialEventName || nextRace.EventName}
                </CardDescription>
              </div>
              <Badge variant="destructive" className="text-lg px-4 py-2">
                Round {nextRace.RoundNumber}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center gap-2 text-lg">
              <MapPin className="h-5 w-5 text-muted-foreground" />
              <span className="font-semibold">{nextRace.Location}, {nextRace.Country}</span>
            </div>
            <div className="flex items-center gap-2">
              <Calendar className="h-5 w-5 text-muted-foreground" />
              <span>{format(parseISO(nextRace.EventDate), 'MMMM d, yyyy')}</span>
            </div>
            {nextRace.Session5Date && (
              <div className="flex items-center gap-2">
                <Clock className="h-5 w-5 text-muted-foreground" />
                <span>Race: {format(parseISO(nextRace.Session5Date), 'PPp')}</span>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      <div>
        <h2 className="text-2xl font-bold mb-4">Upcoming Races</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {upcomingRaces.slice(1).map((event: any) => (
            <Card key={event.RoundNumber} className="hover:shadow-lg transition-shadow">
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <CardTitle className="line-clamp-2">{event.EventName}</CardTitle>
                    <CardDescription className="mt-1">
                      {event.Location}, {event.Country}
                    </CardDescription>
                  </div>
                  <Badge variant="outline">R{event.RoundNumber}</Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center gap-2 text-muted-foreground">
                    <Calendar className="h-4 w-4" />
                    <span>{format(parseISO(event.EventDate), 'MMM d, yyyy')}</span>
                  </div>
                  {event.Session5Date && (
                    <div className="flex items-center gap-2 text-muted-foreground">
                      <Clock className="h-4 w-4" />
                      <span>{format(parseISO(event.Session5Date), 'p')}</span>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>

      <div>
        <h2 className="text-2xl font-bold mb-4">Recent Races</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {events
            .filter((event: any) => event.EventDate && isPast(parseISO(event.EventDate)))
            .slice(-3)
            .reverse()
            .map((event: any) => (
              <Card key={event.RoundNumber} className="opacity-75 hover:opacity-100 transition-opacity">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <CardTitle className="line-clamp-2">{event.EventName}</CardTitle>
                      <CardDescription className="mt-1">
                        {event.Location}, {event.Country}
                      </CardDescription>
                    </div>
                    <Badge variant="secondary">R{event.RoundNumber}</Badge>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Calendar className="h-4 w-4" />
                    <span>{format(parseISO(event.EventDate), 'MMM d, yyyy')}</span>
                  </div>
                </CardContent>
              </Card>
            ))}
        </div>
      </div>
    </div>
  );
}
