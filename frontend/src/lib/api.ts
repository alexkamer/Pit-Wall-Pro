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
  return fetchAPI(`/espn/standings/${year}?type=constructor`);
}

export async function getSchedule(year: number) {
  return fetchAPI(`/fastf1/schedule/${year}`);
}
