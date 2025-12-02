# F1 Data API - Endpoint Examples

Complete guide to all available API endpoints with working examples.

**Base URL:** `http://localhost:8000`

## Table of Contents

- [Root Endpoint](#root-endpoint)
- [ESPN API Endpoints](#espn-api-endpoints)
  - [Standings](#standings)
  - [Drivers](#drivers)
  - [Events](#events)
- [FastF1 API Endpoints](#fastf1-api-endpoints)
  - [Schedule](#schedule)
  - [Session Info](#session-info)
  - [Fastest Lap](#fastest-lap)
  - [Telemetry](#telemetry)
  - [Driver Comparison](#driver-comparison)

---

## Root Endpoint

Get API information and available endpoints.

### GET `/`

**Example:**
```bash
curl http://localhost:8000/
```

**Response:**
```json
{
  "name": "F1 Data API",
  "version": "0.1.0",
  "endpoints": {
    "espn": {
      "standings": "/espn/standings/{year}",
      "driver": "/espn/drivers/{driver_id}",
      "events": "/espn/events?season={year}&limit={limit}"
    },
    "fastf1": {
      "session": "/fastf1/session/{year}/{gp}/{session_type}",
      "fastest_lap": "/fastf1/fastest-lap/{year}/{gp}/{session_type}",
      "telemetry": "/fastf1/telemetry/{year}/{gp}/{session_type}/{driver}"
    }
  }
}
```

---

## ESPN API Endpoints

### Standings

Get championship standings for drivers or constructors.

#### GET `/espn/standings/{year}`

**Parameters:**
- `year` (path): Championship year (e.g., 2024)
- `type` (query): Either `driver` or `constructor` (default: `driver`)

**Example - Driver Standings:**
```bash
curl 'http://localhost:8000/espn/standings/2024?type=driver'
```

**Response Summary:**
```json
{
  "id": "0",
  "name": "Driver",
  "displayName": "Driver Standings",
  "standings": [
    {
      "records": [
        {
          "stats": [
            {"name": "wins", "value": 9.0},
            {"name": "championshipPts", "value": 437.0},
            {"name": "rank", "value": 1.0}
          ]
        }
      ],
      "athlete": {
        "$ref": "http://sports.core.api.espn.com/v2/sports/racing/leagues/f1/seasons/2024/athletes/4665"
      }
    }
  ]
}
```

**Example - Constructor Standings:**
```bash
curl 'http://localhost:8000/espn/standings/2024?type=constructor'
```

**Response Summary:**
```json
{
  "id": "1",
  "name": "constructor",
  "displayName": "Constructor Standings",
  "standings": [
    {
      "records": [
        {
          "stats": [
            {"name": "points", "value": 666.0},
            {"name": "wins", "value": 6.0},
            {"name": "rank", "value": 1.0}
          ]
        }
      ],
      "manufacturer": {
        "$ref": "http://sports.core.api.espn.com/v2/sports/racing/leagues/f1/seasons/2024/manufacturers/106892"
      }
    }
  ]
}
```

---

### Drivers

Get detailed driver profile information.

#### GET `/espn/drivers/{driver_id}`

**Parameters:**
- `driver_id` (path): ESPN driver ID (e.g., `4665` for Verstappen)

**Common Driver IDs:**
- Max Verstappen: `4665`
- Charles Leclerc: `5579`
- Lando Norris: `5498`
- Lewis Hamilton: `4686`
- Carlos Sainz: `5503`

**Example:**
```bash
curl http://localhost:8000/espn/drivers/4665
```

**Response Summary:**
```json
{
  "id": "4665",
  "firstName": "Max",
  "lastName": "Verstappen",
  "fullName": "Max Verstappen",
  "displayName": "Max Verstappen",
  "dateOfBirth": "1997-09-30T07:00Z",
  "birthPlace": {
    "city": "Hasselt"
  },
  "abbreviation": "VER",
  "vehicles": [
    {
      "number": "1",
      "manufacturer": "Renault",
      "team": "Red Bull Racing Team"
    }
  ],
  "headshot": {
    "href": "https://a.espncdn.com/i/headshots/rpm/players/full/4665.png"
  },
  "flag": {
    "href": "https://a.espncdn.com/i/teamlogos/countries/500/ned.png",
    "alt": "Netherlands"
  }
}
```

---

### Events

Get F1 race events/calendar.

#### GET `/espn/events`

**Parameters:**
- `season` (query, optional): Season year to filter events
- `limit` (query, optional): Maximum number of events to return (default: 100)

**Example:**
```bash
curl 'http://localhost:8000/espn/events?season=2024&limit=5'
```

**Response:**
```json
{
  "count": 24,
  "pageIndex": 1,
  "pageSize": 5,
  "pageCount": 5,
  "items": [
    {"$ref": "http://sports.core.api.espn.com/v2/sports/racing/leagues/f1/events/600041133"},
    {"$ref": "http://sports.core.api.espn.com/v2/sports/racing/leagues/f1/events/600041134"},
    {"$ref": "http://sports.core.api.espn.com/v2/sports/racing/leagues/f1/events/600041135"},
    {"$ref": "http://sports.core.api.espn.com/v2/sports/racing/leagues/f1/events/600041136"},
    {"$ref": "http://sports.core.api.espn.com/v2/sports/racing/leagues/f1/events/600041137"}
  ]
}
```

---

## FastF1 API Endpoints

### Schedule

Get the complete season schedule.

#### GET `/fastf1/schedule/{year}`

**Parameters:**
- `year` (path): Championship year (e.g., 2024)

**Example:**
```bash
curl http://localhost:8000/fastf1/schedule/2024
```

**Response Summary:**
```json
[
  {
    "RoundNumber": 1,
    "Country": "Bahrain",
    "Location": "Sakhir",
    "OfficialEventName": "FORMULA 1 GULF AIR BAHRAIN GRAND PRIX 2024",
    "EventDate": "2024-03-02T00:00:00",
    "EventName": "Bahrain Grand Prix",
    "EventFormat": "conventional",
    "Session1": "Practice 1",
    "Session1Date": "2024-02-29T14:30:00+03:00",
    "Session4": "Qualifying",
    "Session5": "Race"
  },
  {
    "RoundNumber": 8,
    "Country": "Monaco",
    "Location": "Monaco",
    "EventName": "Monaco Grand Prix",
    "EventDate": "2024-05-26T00:00:00"
  }
]
```

---

### Session Info

Get detailed information about a specific session including results.

#### GET `/fastf1/session/{year}/{gp}/{session_type}`

**Parameters:**
- `year` (path): Championship year
- `gp` (path): Grand Prix name or round number (e.g., `Monaco` or `8`)
- `session_type` (path): Session type - `FP1`, `FP2`, `FP3`, `Q`, `S` (Sprint), `R` (Race)

**Example:**
```bash
curl http://localhost:8000/fastf1/session/2024/Monaco/Q
```

**Response Summary:**
```json
{
  "name": "Qualifying",
  "date": "2024-05-25T14:00:00",
  "event": {
    "EventName": "Monaco Grand Prix",
    "EventDate": "2024-05-26T00:00:00",
    "Location": "Monaco",
    "Country": "Monaco",
    "RoundNumber": 8
  },
  "results": [
    {
      "DriverNumber": "16",
      "Abbreviation": "LEC",
      "FullName": "Charles Leclerc",
      "TeamName": "Ferrari",
      "Position": 1.0,
      "Q1": "0 days 00:01:11.584000",
      "Q2": "0 days 00:01:10.825000",
      "Q3": "0 days 00:01:10.270000"
    },
    {
      "DriverNumber": "1",
      "Abbreviation": "VER",
      "FullName": "Max Verstappen",
      "TeamName": "Red Bull Racing",
      "Position": 6.0,
      "Q3": "0 days 00:01:10.567000"
    }
  ]
}
```

---

### Fastest Lap

Get the fastest lap from a session, optionally filtered by driver.

#### GET `/fastf1/fastest-lap/{year}/{gp}/{session_type}`

**Parameters:**
- `year` (path): Championship year
- `gp` (path): Grand Prix name or round number
- `session_type` (path): Session type
- `driver` (query, optional): Driver abbreviation (e.g., `VER`, `LEC`)

**Example - Overall Fastest:**
```bash
curl http://localhost:8000/fastf1/fastest-lap/2024/Monaco/Q
```

**Response:**
```json
{
  "driver": "LEC",
  "lap_time": "0 days 00:01:10.270000",
  "lap_number": 25,
  "compound": "SOFT",
  "team": "Ferrari"
}
```

**Example - Driver-Specific:**
```bash
curl 'http://localhost:8000/fastf1/fastest-lap/2024/Monaco/Q?driver=VER'
```

**Response:**
```json
{
  "driver": "VER",
  "lap_time": "0 days 00:01:10.567000",
  "lap_number": 24,
  "compound": "SOFT",
  "team": "Red Bull Racing"
}
```

---

### Telemetry

Get detailed telemetry data for a driver's lap.

#### GET `/fastf1/telemetry/{year}/{gp}/{session_type}/{driver}`

**Parameters:**
- `year` (path): Championship year
- `gp` (path): Grand Prix name or round number
- `session_type` (path): Session type
- `driver` (path): Driver abbreviation (e.g., `VER`, `LEC`, `HAM`)
- `lap_type` (query, optional): `fastest` (default) or specific lap number

**Example:**
```bash
curl http://localhost:8000/fastf1/telemetry/2024/Monaco/Q/LEC
```

**Response Summary:**
```json
{
  "driver": "LEC",
  "lap_number": 25,
  "lap_time": "0 days 00:01:10.270000",
  "telemetry": {
    "distance": [0.027, 15.501, 19.171, ...],
    "speed": [276.486, 279.329, 280.0, ...],
    "throttle": [99.0, 99.0, 99.0, ...],
    "brake": [false, false, false, ...],
    "gear": [7, 7, 7, ...]
  }
}
```

**Telemetry Data:**
- `distance`: Distance along track (meters)
- `speed`: Car speed (km/h)
- `throttle`: Throttle position (0-100%)
- `brake`: Brake applied (boolean)
- `gear`: Current gear (1-8)

---

### Driver Comparison

Compare telemetry data between two drivers' fastest laps.

#### GET `/fastf1/compare/{year}/{gp}/{session_type}`

**Parameters:**
- `year` (path): Championship year
- `gp` (path): Grand Prix name or round number
- `session_type` (path): Session type
- `driver1` (query): First driver abbreviation
- `driver2` (query): Second driver abbreviation

**Example:**
```bash
curl 'http://localhost:8000/fastf1/compare/2024/Monaco/Q?driver1=LEC&driver2=VER'
```

**Response Summary:**
```json
{
  "driver1": {
    "name": "LEC",
    "time": "0 days 00:01:10.270000",
    "telemetry": {
      "distance": [0.027, 15.501, ...],
      "speed": [276.486, 279.329, ...],
      "throttle": [99.0, 99.0, ...]
    }
  },
  "driver2": {
    "name": "VER",
    "time": "0 days 00:01:10.567000",
    "telemetry": {
      "distance": [0.021, 8.928, ...],
      "speed": [276.850, 278.0, ...],
      "throttle": [99.0, 99.0, ...]
    }
  }
}
```

---

## Common Usage Patterns

### Get Current Championship Leader

```bash
# 1. Get driver standings
curl 'http://localhost:8000/espn/standings/2024?type=driver' | jq '.standings[0]'

# 2. Get leader's profile (extract athlete ID from standings)
curl http://localhost:8000/espn/drivers/4665
```

### Analyze Qualifying Performance

```bash
# 1. Get session results
curl http://localhost:8000/fastf1/session/2024/Monaco/Q

# 2. Get fastest lap telemetry for pole sitter
curl http://localhost:8000/fastf1/telemetry/2024/Monaco/Q/LEC

# 3. Compare with another driver
curl 'http://localhost:8000/fastf1/compare/2024/Monaco/Q?driver1=LEC&driver2=VER'
```

### Get Full Season Schedule

```bash
curl http://localhost:8000/fastf1/schedule/2024 | jq '.[] | {round: .RoundNumber, name: .EventName, date: .EventDate}'
```

---

## Error Handling

All endpoints return standard HTTP status codes:

- `200 OK`: Successful request
- `400 Bad Request`: Invalid parameters
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server error

**Example Error Response:**
```json
{
  "detail": "Session Monaco 2024 Q not found"
}
```

---

## Session Type Reference

| Code | Session Name         | Description                    |
|------|---------------------|--------------------------------|
| FP1  | Free Practice 1     | First practice session         |
| FP2  | Free Practice 2     | Second practice session        |
| FP3  | Free Practice 3     | Third practice session         |
| Q    | Qualifying          | Qualifying session             |
| S    | Sprint              | Sprint race                    |
| SQ   | Sprint Qualifying   | Sprint qualifying/shootout     |
| R    | Race                | Main race                      |

---

## Driver Abbreviations

Common 3-letter driver codes:

| Code | Driver Name          | Team              |
|------|---------------------|-------------------|
| VER  | Max Verstappen      | Red Bull Racing   |
| PER  | Sergio Perez        | Red Bull Racing   |
| LEC  | Charles Leclerc     | Ferrari           |
| SAI  | Carlos Sainz        | Ferrari           |
| HAM  | Lewis Hamilton      | Mercedes          |
| RUS  | George Russell      | Mercedes          |
| NOR  | Lando Norris        | McLaren           |
| PIA  | Oscar Piastri       | McLaren           |
| ALO  | Fernando Alonso     | Aston Martin      |
| STR  | Lance Stroll        | Aston Martin      |

---

## Notes

- FastF1 endpoints may take longer to respond on first request (loading and caching data)
- Cached data is stored in `./f1_cache` directory
- Telemetry data is available from 2018 onwards
- Historical results and schedules available from 1950 onwards
- All times are returned as timedelta strings (e.g., "0 days 00:01:10.270000")

---

## Interactive API Documentation

For interactive API documentation with request/response examples, visit:

**Swagger UI:** `http://localhost:8000/docs`
**ReDoc:** `http://localhost:8000/redoc`
