'use client';

import { useRouter } from 'next/navigation';
import { useSchedule } from '@/hooks/use-schedule';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Skeleton } from '@/components/ui/skeleton';
import { Button } from '@/components/ui/button';
import { Calendar, MapPin, Clock, Flag, ChevronRight } from 'lucide-react';
import { format, parseISO, isFuture, isPast } from 'date-fns';
import { CountryFlag } from '@/components/CountryFlag';
import { SectionHeader } from '@/components/SectionHeader';

export default function SchedulePage() {
  const router = useRouter();
  const { data, isLoading, error } = useSchedule(2025);

  if (isLoading) {
    return (
      <div className="space-y-8">
        <div>
          <h1 className="text-5xl font-black tracking-tight mb-3">
            2025 Race Schedule
          </h1>
          <p className="text-lg text-muted-foreground">
            Complete Formula 1 calendar with all sessions
          </p>
        </div>
        <div className="space-y-4">
          {[1, 2, 3, 4, 5, 6].map((i) => (
            <Skeleton key={i} className="h-40 w-full" />
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

  // Separate upcoming and past events
  const upcomingEvents = events.filter((event: any) => {
    const eventDate = event.EventDate ? parseISO(event.EventDate) : null;
    return eventDate && isFuture(eventDate);
  });

  const pastEvents = events.filter((event: any) => {
    const eventDate = event.EventDate ? parseISO(event.EventDate) : null;
    return eventDate && isPast(eventDate);
  });

  const RaceCard = ({ event, isUpcoming }: { event: any; isUpcoming: boolean }) => {
    const eventDate = event.EventDate ? parseISO(event.EventDate) : null;
    const isPastEvent = eventDate && isPast(eventDate);

    return (
      <Card
        className={`
          transition-all hover:shadow-xl
          ${isUpcoming ? 'border-[var(--f1-red)] border-2 shadow-lg' : ''}
          ${isPastEvent && !isUpcoming ? 'opacity-70' : ''}
        `}
      >
        <CardHeader className="pb-4">
          <div className="flex items-start justify-between gap-4">
            {/* Left: Flag and Info */}
            <div className="flex gap-4 flex-1">
              {/* Country Flag - Large */}
              <div className="flex-shrink-0">
                <CountryFlag
                  countryName={event.Country || event.Location}
                  size="xl"
                  className="rounded-md shadow-md border-2 border-muted"
                />
              </div>

              {/* Race Info */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-2 flex-wrap">
                  <Badge
                    variant={isUpcoming ? 'destructive' : isPastEvent ? 'secondary' : 'default'}
                    className="text-sm font-bold"
                  >
                    Round {event.RoundNumber}
                  </Badge>
                  {isUpcoming && (
                    <Badge className="bg-[var(--f1-coral)] hover:bg-[var(--f1-coral)] text-white font-bold">
                      Next Race
                    </Badge>
                  )}
                  {isPastEvent && !isUpcoming && (
                    <Badge variant="outline" className="text-muted-foreground">
                      Completed
                    </Badge>
                  )}
                </div>

                <CardTitle className="text-3xl font-black tracking-tight mb-2">
                  {event.OfficialEventName || event.EventName}
                </CardTitle>

                <div className="flex items-center gap-2 text-base text-muted-foreground">
                  <MapPin className="h-4 w-4" />
                  <span className="font-medium">{event.Location}, {event.Country}</span>
                </div>

                {eventDate && (
                  <div className="flex items-center gap-2 mt-2 text-base">
                    <Calendar className="h-4 w-4 text-[var(--f1-red)]" />
                    <span className="font-semibold text-foreground">
                      {format(eventDate, 'EEEE, MMMM d, yyyy')}
                    </span>
                  </div>
                )}
              </div>
            </div>
          </div>
        </CardHeader>

        <CardContent>
          {/* Sessions Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
            {event.Session1 && event.Session1Date && (
              <div className="p-3 rounded-lg bg-muted/50 border">
                <div className="font-semibold text-sm">{event.Session1}</div>
                <div className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {format(parseISO(event.Session1Date), 'MMM d, p')}
                </div>
              </div>
            )}
            {event.Session2 && event.Session2Date && (
              <div className="p-3 rounded-lg bg-muted/50 border">
                <div className="font-semibold text-sm">{event.Session2}</div>
                <div className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {format(parseISO(event.Session2Date), 'MMM d, p')}
                </div>
              </div>
            )}
            {event.Session3 && event.Session3Date && (
              <div className="p-3 rounded-lg bg-muted/50 border">
                <div className="font-semibold text-sm">{event.Session3}</div>
                <div className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {format(parseISO(event.Session3Date), 'MMM d, p')}
                </div>
              </div>
            )}
            {event.Session4 && event.Session4Date && (
              <div className="p-3 rounded-lg bg-muted/50 border">
                <div className="font-semibold text-sm">{event.Session4}</div>
                <div className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {format(parseISO(event.Session4Date), 'MMM d, p')}
                </div>
              </div>
            )}
            {event.Session5 && event.Session5Date && (
              <div className="p-3 rounded-lg bg-[var(--f1-red)]/10 border-2 border-[var(--f1-red)]">
                <div className="font-bold text-sm flex items-center gap-1 text-[var(--f1-red)]">
                  <Flag className="h-3 w-3" />
                  {event.Session5}
                </div>
                <div className="text-xs text-muted-foreground mt-1 flex items-center gap-1">
                  <Clock className="h-3 w-3" />
                  {format(parseISO(event.Session5Date), 'MMM d, p')}
                </div>
              </div>
            )}
          </div>

          {/* View Results Button for Past Races */}
          {isPastEvent && !isUpcoming && (
            <div className="mt-4 pt-4 border-t">
              <Button
                onClick={() => router.push(`/race/2025/${event.EventName.replace(/ /g, '_')}`)}
                variant="outline"
                className="w-full font-semibold hover:bg-[var(--f1-red)] hover:text-white hover:border-[var(--f1-red)]"
              >
                View Race Results
                <ChevronRight className="ml-2 h-4 w-4" />
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div>
        <h1 className="text-5xl md:text-6xl font-black tracking-tight mb-3 flex items-center gap-4">
          <Calendar className="h-12 w-12 text-[var(--f1-red)]" />
          2025 Race Schedule
        </h1>
        <p className="text-lg text-muted-foreground">
          Complete Formula 1 calendar with all sessions and race results
        </p>
      </div>

      {/* Upcoming Races Section */}
      {upcomingEvents.length > 0 && (
        <div>
          <SectionHeader
            title="Upcoming Races"
            subtitle={`${upcomingEvents.length} race${upcomingEvents.length > 1 ? 's' : ''} remaining in the 2025 season`}
          />
          <div className="space-y-6">
            {upcomingEvents.map((event: any) => (
              <RaceCard key={event.RoundNumber} event={event} isUpcoming={true} />
            ))}
          </div>
        </div>
      )}

      {/* Past Races Section */}
      {pastEvents.length > 0 && (
        <div>
          <SectionHeader
            title="Completed Races"
            subtitle={`${pastEvents.length} race${pastEvents.length > 1 ? 's' : ''} completed`}
          />
          <div className="space-y-4">
            {pastEvents.map((event: any) => (
              <RaceCard key={event.RoundNumber} event={event} isUpcoming={false} />
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
