const API_BASE_URL = 'http://localhost:8000';

async function fetchAPI<T>(endpoint: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${endpoint}`);
  if (!response.ok) throw new Error(`API error: ${response.statusText}`);
  return response.json();
}

export async function getDriverStandings(year: number) {
  const standings = await fetchAPI<any>(`/espn/standings/${year}?type=driver`);

  // Get current team data from FastF1 schedule
  let teamMap: Record<string, string> = {};
  try {
    const schedule = await fetchAPI<any>(`/fastf1/schedule/${year}`);
    // Get the most recent race to get current team assignments
    if (schedule.length > 0) {
      const latestRound = schedule[schedule.length - 1].RoundNumber;
      try {
        const session = await fetchAPI<any>(`/fastf1/session/${year}/${latestRound}/R`);
        // Build a map of driver abbreviations to teams
        session.results?.forEach((result: any) => {
          if (result.Abbreviation && result.TeamName) {
            teamMap[result.Abbreviation] = result.TeamName;
          }
        });
      } catch (e) {
        // If race results aren't available, try qualifying
        try {
          const session = await fetchAPI<any>(`/fastf1/session/${year}/${latestRound}/Q`);
          session.results?.forEach((result: any) => {
            if (result.Abbreviation && result.TeamName) {
              teamMap[result.Abbreviation] = result.TeamName;
            }
          });
        } catch (e2) {
          // Fallback to no team map
        }
      }
    }
  } catch (e) {
    // If FastF1 fails, continue without team map
  }

  // Fetch driver details for each standing
  const standingsWithDetails = await Promise.all(
    standings.standings.map(async (standing: any) => {
      const athleteRef = standing.athlete.$ref;
      const driverId = athleteRef.split('/').pop().split('?')[0];

      try {
        const driver = await fetchAPI<any>(`/espn/drivers/${driverId}`);
        const abbreviation = driver.abbreviation;

        return {
          ...standing,
          driverDetails: {
            name: driver.displayName || driver.fullName,
            firstName: driver.firstName,
            lastName: driver.lastName,
            abbreviation: abbreviation,
            // Use FastF1 team data if available, otherwise fall back to ESPN data
            team: teamMap[abbreviation] || driver.vehicles?.[0]?.team || 'Unknown Team',
            number: driver.vehicles?.[0]?.number,
            headshot: driver.headshot?.href,
          }
        };
      } catch (e) {
        return standing;
      }
    })
  );

  return {
    ...standings,
    standings: standingsWithDetails
  };
}

export async function getConstructorStandings(year: number) {
  const standings = await fetchAPI<any>(`/espn/standings/${year}?type=constructor`);

  // Fetch manufacturer details for each standing
  const standingsWithNames = await Promise.all(
    standings.standings.map(async (standing: any) => {
      const manufacturerRef = standing.manufacturer?.$ref || '';

      try {
        // Fetch manufacturer details directly from ESPN API
        const manufacturer = await fetch(manufacturerRef).then(r => r.json());

        return {
          ...standing,
          teamName: manufacturer.displayName || manufacturer.name || 'Unknown Team'
        };
      } catch (e) {
        const manufacturerId = manufacturerRef.split('/').filter((s: string) => s).pop()?.split('?')[0];
        return {
          ...standing,
          teamName: `Constructor ${manufacturerId}`
        };
      }
    })
  );

  return {
    ...standings,
    standings: standingsWithNames
  };
}

export async function getAvailableSeasons() {
  return fetchAPI<{ seasons: number[] }>(`/fastf1/seasons`);
}

export async function getSchedule(year: number) {
  return fetchAPI(`/fastf1/schedule/${year}`);
}

export async function getRaceResults(year: number, roundNumber: number) {
  return fetchAPI(`/fastf1/race-results/${year}/${roundNumber}`);
}

// Get race metadata (winners, pole position) for each round from backend
export async function getRaceMetadata(year: number) {
  const data = await fetchAPI<any>(`/standings/complete/${year}`);
  return data.raceMetadata;
}

// New optimized function that gets all standings data in one call
export async function getCompleteStandings(year: number) {
  return fetchAPI<any>(`/standings/complete/${year}`);
}

// Team logo mapping - Using official F1 team logos
const TEAM_LOGOS: Record<string, string> = {
  'McLaren': 'https://media.formula1.com/content/dam/fom-website/teams/2025/mclaren-logo.png',
  'Mercedes': 'https://media.formula1.com/content/dam/fom-website/teams/2025/mercedes-logo.png',
  'Red Bull': 'https://media.formula1.com/content/dam/fom-website/teams/2025/red-bull-racing-logo.png',
  'Ferrari': 'https://media.formula1.com/content/dam/fom-website/teams/2025/ferrari-logo.png',
  'Aston Martin': 'https://media.formula1.com/content/dam/fom-website/teams/2025/aston-martin-logo.png',
  'Alpine': 'https://media.formula1.com/content/dam/fom-website/teams/2025/alpine-logo.png',
  'Williams': 'https://media.formula1.com/content/dam/fom-website/teams/2025/williams-logo.png',
  'Racing Bulls': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/rb-logo.png',
  'Sauber': 'https://media.formula1.com/content/dam/fom-website/teams/2025/kick-sauber-logo.png',
  'Haas': 'https://media.formula1.com/d_team_car_fallback_image.png/content/dam/fom-website/teams/2024/haas-f1-team-logo.png'
};

export async function getDriverRaceResults(year: number) {
  const standings = await fetchAPI<any>(`/espn/standings/${year}?type=driver`);

  // Get all race events for the season from FastF1 schedule
  const schedule = await getSchedule(year);

  // Create a map of race names and countries by round number for fallback
  const scheduleMap: Record<string, { name: string; country: string }> = {};
  schedule.forEach((race: any) => {
    scheduleMap[race.RoundNumber.toString()] = {
      name: race.EventName,
      country: race.Country
    };
  });

  // Fetch race-by-race data for each driver
  const driverData = await Promise.all(
    standings.standings.map(async (standing: any) => {
      const athleteRef = standing.athlete?.$ref || '';

      try {
        // Fetch driver details
        const athlete = await fetch(athleteRef).then(r => r.json());
        const driverName = athlete.displayName || athlete.fullName;
        const driverAbbreviation = athlete.abbreviation;

        // Fetch team name from FastF1
        let teamName = 'Unknown Team';
        try {
          const latestRace = schedule.filter((r: any) => r.RoundNumber > 0).pop();
          if (latestRace) {
            const session = await fetchAPI<any>(`/fastf1/session/${year}/${latestRace.RoundNumber}/R`);
            const driverResult = session.results?.find((r: any) => r.Abbreviation === driverAbbreviation);
            if (driverResult) {
              teamName = driverResult.TeamName;
            }
          }
        } catch (e) {
          // Fallback to unknown
        }

        // Fetch eventlog with race-by-race statistics
        const eventLogUrl = athlete.eventLog.$ref;
        const eventLog = await fetch(eventLogUrl).then(r => r.json());

        // Fetch points for each race
        const raceResults = await Promise.all(
          eventLog.events.items.map(async (item: any, index: number) => {
            try {
              const statsUrl = item.statistics.$ref;
              const stats = await fetch(statsUrl).then(r => r.json());

              let eventName = 'Unknown';
              let country = 'Unknown';
              try {
                const eventUrl = item.event.$ref;
                const event = await fetch(eventUrl).then(r => r.json());
                eventName = event.shortName || event.name;
              } catch (e) {
                // If event fetch fails, use schedule as fallback
                const roundNumber = (index + 1).toString();
                const scheduleData = scheduleMap[roundNumber];
                eventName = scheduleData?.name || `Round ${roundNumber}`;
                country = scheduleData?.country || 'Unknown';
              }

              // Always try to get country from schedule map since ESPN doesn't provide it
              const roundNumber = (index + 1).toString();
              country = scheduleMap[roundNumber]?.country || 'Unknown';

              const pointsStat = stats.splits.categories[0]?.stats?.find((s: any) => s.name === 'championshipPts');
              const points = pointsStat?.value || 0;

              return {
                eventId: item.eventId,
                eventName: eventName,
                country: country,
                points: points
              };
            } catch (e) {
              // Fallback to schedule name
              const roundNumber = (index + 1).toString();
              const scheduleData = scheduleMap[roundNumber];
              return {
                eventId: item.eventId,
                eventName: scheduleData?.name || `Round ${roundNumber}`,
                country: scheduleData?.country || 'Unknown',
                points: 0
              };
            }
          })
        );

        // Get total points
        const totalPoints = standing.records[0]?.stats?.find((s: any) => s.name === 'championshipPts')?.value || 0;

        return {
          driverName,
          driverAbbreviation,
          teamName,
          totalPoints,
          raceResults
        };
      } catch (e) {
        return {
          driverName: 'Unknown Driver',
          driverAbbreviation: '???',
          teamName: 'Unknown Team',
          totalPoints: 0,
          raceResults: []
        };
      }
    })
  );

  return driverData;
}

// Search for drivers across all seasons
export async function searchDrivers(query: string = '', limit: number = 50) {
  const params = new URLSearchParams();
  if (query) params.append('query', query);
  params.append('limit', limit.toString());
  return fetchAPI<any>(`/drivers?${params.toString()}`);
}

// Get drivers list for a specific season
export async function getDriversBySeason(year: number, sort: string = 'points') {
  return fetchAPI<any>(`/drivers/season/${year}?sort=${sort}`);
}

// Get individual driver profile with career stats
export async function getDriverProfile(driverId: string) {
  return fetchAPI<any>(`/drivers/profile/${driverId}`);
}

// Get detailed driver profile from backend
export async function getDriverProfileDetailed(driverId: string) {
  return fetchAPI<any>(`/drivers/profile/${driverId}`);
}

export async function getConstructorRaceResults(year: number) {
  const standings = await fetchAPI<any>(`/espn/standings/${year}?type=constructor`);

  // Get all race events for the season from FastF1 schedule
  const schedule = await getSchedule(year);

  // Create a map of race names and countries by round number for fallback
  const scheduleMap: Record<string, { name: string; country: string }> = {};
  schedule.forEach((race: any) => {
    scheduleMap[race.RoundNumber.toString()] = {
      name: race.EventName,
      country: race.Country
    };
  });

  // Fetch race-by-race data for each constructor
  const constructorData = await Promise.all(
    standings.standings.map(async (standing: any) => {
      const manufacturerRef = standing.manufacturer?.$ref || '';

      try {
        // Fetch manufacturer details
        const manufacturer = await fetch(manufacturerRef).then(r => r.json());
        const teamName = manufacturer.displayName || manufacturer.name;

        // Fetch eventlog with race-by-race statistics
        const eventLogUrl = manufacturer.eventLog.$ref;
        const eventLog = await fetch(eventLogUrl).then(r => r.json());

        // Fetch points for each race
        const raceResults = await Promise.all(
          eventLog.events.items.map(async (item: any, index: number) => {
            try {
              const statsUrl = item.statistics.$ref;
              const stats = await fetch(statsUrl).then(r => r.json());

              let eventName = 'Unknown';
              let country = 'Unknown';
              try {
                const eventUrl = item.event.$ref;
                const event = await fetch(eventUrl).then(r => r.json());
                eventName = event.shortName || event.name;
              } catch (e) {
                // If event fetch fails, use schedule as fallback
                const roundNumber = (index + 1).toString();
                const scheduleData = scheduleMap[roundNumber];
                eventName = scheduleData?.name || `Round ${roundNumber}`;
                country = scheduleData?.country || 'Unknown';
              }

              // Always try to get country from schedule map since ESPN doesn't provide it
              const roundNumber = (index + 1).toString();
              country = scheduleMap[roundNumber]?.country || 'Unknown';

              const pointsStat = stats.splits.categories[0]?.stats?.find((s: any) => s.name === 'points');
              const points = pointsStat?.value || 0;

              return {
                eventId: item.eventId,
                eventName: eventName,
                country: country,
                points: points
              };
            } catch (e) {
              // Fallback to schedule name
              const roundNumber = (index + 1).toString();
              const scheduleData = scheduleMap[roundNumber];
              return {
                eventId: item.eventId,
                eventName: scheduleData?.name || `Round ${roundNumber}`,
                country: scheduleData?.country || 'Unknown',
                points: 0
              };
            }
          })
        );

        // Get total points
        const totalPoints = standing.records[0]?.stats?.find((s: any) => s.name === 'points')?.value || 0;

        return {
          teamName,
          teamLogo: TEAM_LOGOS[teamName] || '',
          totalPoints,
          raceResults
        };
      } catch (e) {
        return {
          teamName: 'Unknown Team',
          teamLogo: '',
          totalPoints: 0,
          raceResults: []
        };
      }
    })
  );

  return constructorData;
}

// Get qualifying results (Q1, Q2, Q3)
export async function getQualifyingResults(year: number, roundNumber: number) {
  return fetchAPI(`/fastf1/qualifying/${year}/${roundNumber}`);
}

// Get practice session results (FP1, FP2, FP3)
export async function getPracticeResults(year: number, roundNumber: number) {
  return fetchAPI(`/fastf1/practice/${year}/${roundNumber}`);
}

// Get sprint race results
export async function getSprintResults(year: number, roundNumber: number) {
  return fetchAPI(`/fastf1/sprint/${year}/${roundNumber}`);
}

// Get advanced session data (weather, track status, messages, lap times)
export async function getSessionData(year: number, roundNumber: number, sessionType: string) {
  return fetchAPI(`/fastf1/session-data/${year}/${roundNumber}/${sessionType}`);
}
