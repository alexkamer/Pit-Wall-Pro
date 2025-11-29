# ESPN F1 API Comprehensive Mapping

## Base URL
```
https://sports.core.api.espn.com/v2/sports/racing
```

## API Structure Overview

The ESPN F1 API follows a hierarchical structure with extensive hypermedia references ($ref) to related resources.

## Core Endpoints

### 1. Racing Sport Root
**Endpoint:** `/v2/sports/racing`

**Response includes:**
- `leagues` - Reference to all racing leagues (F1, IndyCar, NASCAR, etc.)
- `athletes` - Reference to all racing athletes
- Sport metadata (name, logos, links)

### 2. Leagues List
**Endpoint:** `/v2/sports/racing/leagues`

**Returns 6 racing leagues:**
- `f1` - Formula 1
- `irl` - IndyCar
- `nascar-premier` - NASCAR Cup Series
- `nascar-secondary` - NASCAR Xfinity Series
- `nascar-truck` - NASCAR Truck Series
- `nhra` - NHRA

### 3. F1 League Details
**Endpoint:** `/v2/sports/racing/leagues/f1`

**Response includes:**
- `id`: "2030"
- `name`: "Formula 1"
- `abbreviation`: "F1"
- `season`: Current season details (2025 as of now)
- `seasons`: Reference to all seasons
- `events`: Reference to events
- `calendar`: Reference to calendar
- `logos`: League logos (default and dark theme)
- `links`: Web and app links

### 4. Seasons
**Endpoint:** `/v2/sports/racing/leagues/f1/seasons`

**Features:**
- Paginated results (25 per page)
- Historical data from 1950 to present
- 76 total seasons available

**Individual Season:**
`/v2/sports/racing/leagues/f1/seasons/{year}`

**Season includes:**
- Year
- Start/End dates
- `types`: Season types (Regular Season = type 2)
- `athletes`: Drivers for that season
- Season standings reference

### 5. Events (Races)
**Endpoint:** `/v2/sports/racing/leagues/f1/events`

**Query Parameters:**
- Defaults to current date filtering
- Use season-specific endpoint for full season events

**Individual Event:**
`/v2/sports/racing/leagues/f1/events/{eventId}`

**Event Structure:**
```json
{
  "id": "600052107",
  "name": "Qatar Airways Qatar Grand Prix",
  "shortName": "Qatar Airways Qatar GP",
  "date": "2025-11-28T13:30Z",
  "endDate": "2025-11-30T16:00Z",
  "competitions": [
    // Multiple competitions (sessions) per event
  ],
  "venues": [/* venue references */],
  "circuit": {/* circuit reference */},
  "defendingChampion": {
    "driver": {/* ref */},
    "manufacturer": {/* ref */}
  }
}
```

### 6. Competitions (Sessions)
Each event contains multiple competitions representing different sessions:

**Session Types:**
- `type.id: "1"` - Free Practice (FP1, FP2, FP3)
- `type.id: "2"` - Qualifying
- `type.id: "3"` - Race
- `type.id: "5"` - Sprint Shootout
- `type.id: "6"` - Sprint Race

**Competition Structure:**
```json
{
  "id": "401737850",
  "date": "2025-11-30T16:00Z",
  "type": {
    "id": "3",
    "text": "Race",
    "abbreviation": "Race"
  },
  "competitors": [
    // Array of all drivers with results
  ],
  "status": {/* competition status */},
  "statistics": {/* competition statistics */},
  "broadcasts": {/* TV/streaming info */}
}
```

**Competitor (Driver Result) Structure:**
```json
{
  "id": "5752",
  "type": "athlete",
  "order": 1,  // Finishing position
  "startOrder": 1,  // Starting position (grid)
  "winner": true,
  "athlete": {/* athlete reference */},
  "status": {/* driver status in competition */},
  "statistics": {/* driver stats for this competition */},
  "vehicle": {
    "number": "81",
    "manufacturer": "McLaren",
    "teamColor": "FF8700"
  }
}
```

### 7. Standings
**Endpoint:** `/v2/sports/racing/leagues/f1/seasons/{year}/types/2/standings`

**Returns two standing types:**
- `id: "0"` - Driver Standings
- `id: "1"` - Constructor Standings

**Driver Standings:**
`/v2/sports/racing/leagues/f1/seasons/{year}/types/2/standings/0`

**Standing Entry Structure:**
```json
{
  "athlete": {/* athlete reference */},
  "records": [{
    "id": "0",
    "name": "overall",
    "stats": [
      {
        "name": "wins",
        "value": 9.0,
        "displayValue": "9"
      },
      {
        "name": "championshipPts",
        "abbreviation": "PTS",
        "value": 437.0
      },
      {
        "name": "behind",
        "value": 0.0  // Points behind leader
      },
      {
        "name": "poles",
        "value": 9.0
      },
      {
        "name": "starts",
        "value": 24.0
      },
      {
        "name": "top10",
        "value": 23.0
      },
      {
        "name": "top5",
        "value": 19.0
      },
      {
        "name": "dnf",
        "value": 2.0
      }
      // ... more stats
    ]
  }]
}
```

**Available Stats:**
- `wins` - Race wins
- `championshipPts` - Championship points
- `behind` - Points behind leader
- `poles` - Pole positions
- `starts` - Race starts
- `top10` - Top 10 finishes
- `top5` - Top 5 finishes
- `topfinish` - Best finish position
- `dnf` - Did not finish count
- `penaltyPts` - Penalty points
- `lapsLead` - Laps led
- `currentWeek` - Current race week
- `totalWeeks` - Total race weeks

### 8. Athletes (Drivers)
**Endpoint:** `/v2/sports/racing/athletes/{athleteId}`

**Driver Profile Structure:**
```json
{
  "id": "4665",
  "firstName": "Max",
  "lastName": "Verstappen",
  "fullName": "Max Verstappen",
  "displayName": "Max Verstappen",
  "shortName": "M. Verstappen",
  "dateOfBirth": "1997-09-30T07:00Z",
  "birthPlace": {
    "city": "Hasselt"
  },
  "abbreviation": "VER",
  "headshot": {
    "href": "https://a.espncdn.com/i/headshots/rpm/players/full/4665.png"
  },
  "flag": {
    "href": "https://a.espncdn.com/i/teamlogos/countries/500/ned.png",
    "alt": "Netherlands"
  },
  "status": {
    "id": "1",
    "name": "Active",
    "type": "active"
  },
  "vehicles": [{
    "number": "1",
    "manufacturer": "Renault",
    "chassis": "RB28",
    "engine": "Renault RS27-2012",
    "tire": "Pirelli",
    "sponsor": "ING",
    "team": "Red Bull Racing Team"
  }],
  "links": [
    // Player card, stats, news, bio links
  ]
}
```

### 9. Season Athletes
**Endpoint:** `/v2/sports/racing/leagues/f1/seasons/{year}/athletes`

Returns all drivers for a specific season with their team affiliations.

### 10. Constructor/Team Endpoints
**Endpoint Pattern:** `/v2/sports/racing/leagues/f1/seasons/{year}/manufacturers/{manufacturerId}`

Teams identified by manufacturer ID in vehicle data.

## Data Relationships

```
Sport (racing)
└── Leagues
    └── F1 League
        ├── Seasons (1950-present)
        │   ├── Season Types (Regular Season)
        │   │   └── Standings
        │   │       ├── Driver Standings
        │   │       └── Constructor Standings
        │   └── Athletes (season-specific)
        └── Events (Races)
            ├── Event Metadata
            │   ├── Circuit
            │   ├── Venue
            │   └── Defending Champion
            └── Competitions (Sessions)
                ├── Practice Sessions
                ├── Sprint Shootout
                ├── Sprint Race
                ├── Qualifying
                └── Race
                    └── Competitors (Results)
                        ├── Athlete
                        ├── Vehicle/Team
                        ├── Statistics
                        └── Status
```

## Key Features

### Hypermedia-Driven API
- Extensive use of `$ref` for related resources
- Follow references to get detailed data
- Reduces payload size, enables lazy loading

### Comprehensive Historical Data
- 76 seasons from 1950 to present
- Complete race results
- Driver and constructor standings
- Session-level data for modern seasons

### Real-time Data
- Live timing during races
- Session status updates
- Broadcasting information

### Rich Metadata
- Driver profiles with photos
- Team colors and logos
- Circuit information
- Country flags
- Links to ESPN.com pages

## Query Parameters

Common parameters across endpoints:
- `lang=en` - Language (default: en)
- `region=us` - Region (default: us)
- Pagination: `pageIndex`, `pageSize`

## Response Format

All responses are JSON with consistent structure:
```json
{
  "$ref": "self reference URL",
  "id": "resource ID",
  // ... resource-specific fields
  "links": [/* related web links */]
}
```

## Best Practices

1. **Use $ref Links:** Follow the API's hypermedia structure
2. **Cache Season Data:** Historical data rarely changes
3. **Respect Rate Limits:** No official limits documented, but be reasonable
4. **Use Specific Endpoints:** Don't query all events if you need one season
5. **Handle Missing Data:** Not all historical seasons have complete data

## Limitations

1. **No Authentication:** Public API, no auth required
2. **No Telemetry:** ESPN API provides results, not detailed telemetry
3. **Limited Historical Detail:** Older seasons have less granular data
4. **No Live Timing Details:** Basic status only, not lap-by-lap during race
5. **Documentation:** Unofficial API - no official docs from ESPN

## Comparison with Other APIs

**ESPN F1 API is best for:**
- Race results and standings
- Driver/team profiles
- Historical championship data
- Integration with ESPN content
- Basic race weekend information

**ESPN F1 API lacks:**
- Detailed telemetry data
- Lap-by-lap timing
- Sector times (granular)
- Weather data
- Tire strategy details
- Technical car data

For detailed telemetry and technical data, use FastF1 API (covered in separate document).
