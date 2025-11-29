'use client';

import { useRouter } from 'next/navigation';
import { useSchedule } from '@/hooks/use-schedule';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Calendar, MapPin, Clock, Flag, ChevronRight } from 'lucide-react';
import { format, parseISO, isFuture, isPast } from 'date-fns';

export default function SchedulePage() {
  const router = useRouter();
  const { data, isLoading, error } = useSchedule(2025);

  if (isLoading) {
    return (
      <div className="space-y-6">
        <h1 className="text-4xl font-bold">2025 Race Schedule</h1>
        <div className="space-y-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-32 w-full" />
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

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-4xl font-bold tracking-tight flex items-center gap-3">
          <Calendar className="h-10 w-10 text-red-600" />
          2025 Race Schedule
        </h1>
        <p className="text-muted-foreground mt-2">
          Complete Formula 1 calendar with all sessions
        </p>
      </div>

      <div className="space-y-4">
        {events.map((event: any) => {
          const eventDate = event.EventDate ? parseISO(event.EventDate) : null;
          const isUpcoming = eventDate && isFuture(eventDate);
          const isPastEvent = eventDate && isPast(eventDate);

          return (
            <Card
              key={event.RoundNumber}
              className={
                isUpcoming
                  ? 'border-red-600 border-2'
                  : isPastEvent
                  ? 'opacity-60'
                  : ''
              }
            >
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Badge
                        variant={isUpcoming ? 'destructive' : isPastEvent ? 'secondary' : 'default'}
                        className="text-sm"
                      >
                        Round {event.RoundNumber}
                      </Badge>
                      {isUpcoming && (
                        <Badge variant="outline" className="text-green-600 border-green-600">
                          Upcoming
                        </Badge>
                      )}
                      {isPastEvent && (
                        <Badge variant="outline" className="text-gray-500">
                          Completed
                        </Badge>
                      )}
                    </div>
                    <CardTitle className="text-2xl">
                      {event.OfficialEventName || event.EventName}
                    </CardTitle>
                    <CardDescription className="text-base mt-1">
                      <span className="flex items-center gap-2 mt-2">
                        <MapPin className="h-4 w-4" />
                        {event.Location}, {event.Country}
                      </span>
                    </CardDescription>
                  </div>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {eventDate && (
                    <div className="flex items-center gap-2">
                      <Calendar className="h-5 w-5 text-muted-foreground" />
                      <span className="font-semibold">
                        {format(eventDate, 'EEEE, MMMM d, yyyy')}
                      </span>
                    </div>
                  )}

                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3 mt-4">
                    {event.Session1 && event.Session1Date && (
                      <div className="p-3 rounded-lg bg-muted">
                        <div className="font-semibold text-sm">{event.Session1}</div>
                        <div className="text-xs text-muted-foreground mt-1">
                          <Clock className="h-3 w-3 inline mr-1" />
                          {format(parseISO(event.Session1Date), 'MMM d, p')}
                        </div>
                      </div>
                    )}
                    {event.Session2 && event.Session2Date && (
                      <div className="p-3 rounded-lg bg-muted">
                        <div className="font-semibold text-sm">{event.Session2}</div>
                        <div className="text-xs text-muted-foreground mt-1">
                          <Clock className="h-3 w-3 inline mr-1" />
                          {format(parseISO(event.Session2Date), 'MMM d, p')}
                        </div>
                      </div>
                    )}
                    {event.Session3 && event.Session3Date && (
                      <div className="p-3 rounded-lg bg-muted">
                        <div className="font-semibold text-sm">{event.Session3}</div>
                        <div className="text-xs text-muted-foreground mt-1">
                          <Clock className="h-3 w-3 inline mr-1" />
                          {format(parseISO(event.Session3Date), 'MMM d, p')}
                        </div>
                      </div>
                    )}
                    {event.Session4 && event.Session4Date && (
                      <div className="p-3 rounded-lg bg-muted">
                        <div className="font-semibold text-sm">{event.Session4}</div>
                        <div className="text-xs text-muted-foreground mt-1">
                          <Clock className="h-3 w-3 inline mr-1" />
                          {format(parseISO(event.Session4Date), 'MMM d, p')}
                        </div>
                      </div>
                    )}
                    {event.Session5 && event.Session5Date && (
                      <div className="p-3 rounded-lg bg-red-100 dark:bg-red-950 border border-red-600">
                        <div className="font-semibold text-sm flex items-center gap-1">
                          <Flag className="h-3 w-3" />
                          {event.Session5}
                        </div>
                        <div className="text-xs text-muted-foreground mt-1">
                          <Clock className="h-3 w-3 inline mr-1" />
                          {format(parseISO(event.Session5Date), 'MMM d, p')}
                        </div>
                      </div>
                    )}
                  </div>

                  {isPastEvent && (
                    <div className="mt-4 pt-4 border-t">
                      <Button
                        onClick={() => router.push(`/race/2025/${event.EventName.replace(/ /g, '_')}`)}
                        variant="outline"
                        className="w-full"
                      >
                        View Race Results
                        <ChevronRight className="ml-2 h-4 w-4" />
                      </Button>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
