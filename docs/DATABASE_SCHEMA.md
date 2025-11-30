# F1 Database Schema Documentation

## Overview

This database stores Formula 1 historical data from 1950 to present, sourced from the ESPN F1 API. The schema is designed around ESPN's data structure with their IDs as primary keys for efficient lookups and updates.

## Table Structure

### Core Tables

#### 1. `seasons`
Stores F1 championship seasons and metadata.

**Primary Key:** `year`

| Column | Type | Description |
|--------|------|-------------|
| year | INTEGER | Season year (e.g., 2024) |
| start_date | TEXT | Season start date |
| end_date | TEXT | Season end date |
| display_name | TEXT | Season display name |
| season_type_id | TEXT | ESPN season type ID |
| season_type_name | TEXT | Season type name |
| has_standings | BOOLEAN | Whether standings are available |
| standings_url | TEXT | ESPN API URL for standings |
| athletes_url | TEXT | ESPN API URL for drivers |
| updated_at | TIMESTAMP | Last update timestamp |

**Populated by:** `scripts/populate_seasons.py`

---

#### 2. `drivers`
Stores driver information across all seasons.

**Primary Key:** `id` (ESPN driver ID)

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | ESPN driver ID (e.g., "4510") |
| abbreviation | TEXT | 3-letter driver code (e.g., "VER") |
| first_name | TEXT | Driver's first name |
| last_name | TEXT | Driver's last name |
| full_name | TEXT | Full name |
| display_name | TEXT | Display name |
| short_name | TEXT | Short name format |
| date_of_birth | TEXT | Birth date (ISO format) |
| birth_place | TEXT | City of birth |
| headshot_url | TEXT | URL to driver photo |
| flag_url | TEXT | URL to nationality flag |
| nationality | TEXT | Driver nationality |
| active | BOOLEAN | Currently active in F1 |
| status | TEXT | Current status |
| updated_at | TIMESTAMP | Last update timestamp |

**Populated by:** `scripts/populate_drivers.py`

---

#### 3. `driver_seasons`
Junction table tracking which drivers participated in which seasons.

**Composite Primary Key:** `(driver_id, year)`

| Column | Type | Description |
|--------|------|-------------|
| driver_id | TEXT | References drivers.id |
| year | INTEGER | References seasons.year |

**Foreign Keys:**
- `driver_id` → `drivers.id`
- `year` → `seasons.year`

**Populated by:** `scripts/populate_drivers.py`

---

#### 4. `teams`
Stores team/constructor information.

**Primary Key:** `id` (normalized team name)

| Column | Type | Description |
|--------|------|-------------|
| id | TEXT | Normalized ID (e.g., "mclaren") |
| name | TEXT | Official team name |
| display_name | TEXT | Display name |
| updated_at | TIMESTAMP | Last update timestamp |

**Note:** Team IDs are generated from manufacturer names by lowercasing and replacing spaces with underscores.

**Populated by:** `scripts/populate_all_races.py`

---

#### 5. `races`
Stores race weekend/event information.

**Primary Key:** `espn_event_id` (ESPN's event/weekend ID)

| Column | Type | Description |
|--------|------|-------------|
| espn_event_id | TEXT | ESPN event ID (e.g., "600041133") |
| year | INTEGER | Season year |
| round_number | INTEGER | Round number in season (1-24) |
| event_name | TEXT | Full event name |
| official_event_name | TEXT | Official short name |
| country | TEXT | Country hosting the race |
| location | TEXT | City/location |
| circuit_name | TEXT | Full circuit name |
| event_date | TEXT | Event date (ISO format) |
| event_format | TEXT | Race format (default: "conventional") |
| has_sprint | BOOLEAN | Whether event has sprint race |
| updated_at | TIMESTAMP | Last update timestamp |

**Unique Constraint:** `(year, round_number)`

**Foreign Keys:**
- `year` → `seasons.year`

**Populated by:** `scripts/populate_all_races.py`

---

#### 6. `race_sessions`
Stores individual sessions within a race weekend (Practice, Qualifying, Sprint, Race).

**Primary Key:** `espn_competition_id` (ESPN's session/competition ID)

| Column | Type | Description |
|--------|------|-------------|
| espn_competition_id | TEXT | ESPN competition ID (e.g., "401622102") |
| race_espn_event_id | TEXT | References races.espn_event_id |
| session_type | TEXT | Session type (e.g., "Free Practice", "Qualifying", "Race") |
| session_number | INTEGER | Session number within event |
| session_date | TEXT | Session date (ISO format) |
| updated_at | TEXT | Last update timestamp |

**Foreign Keys:**
- `race_espn_event_id` → `races.espn_event_id`

**Session Types:**
- "Free Practice" (FP1, FP2, FP3)
- "Qualifying"
- "Sprint Shootout" (sprint qualifying)
- "Sprint Race"
- "Race"

**Populated by:** `scripts/populate_all_races.py`

---

#### 7. `session_results`
Stores driver performance results for each session.

**Primary Key:** Auto-increment `id`

| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Auto-increment primary key |
| session_espn_competition_id | TEXT | References race_sessions.espn_competition_id |
| driver_id | TEXT | References drivers.id |
| team_id | TEXT | References teams.id |
| position | INTEGER | Finishing position in session |
| grid_position | INTEGER | Starting grid position (for races) |
| winner | BOOLEAN | Whether driver won the session |
| fastest_lap | BOOLEAN | Whether driver had fastest lap |
| points | REAL | Points earned (for races) |
| laps_completed | INTEGER | Number of laps completed |
| status | TEXT | Session status (finished, DNF, etc.) |
| espn_statistics_url | TEXT | ESPN API URL for detailed stats |
| updated_at | TEXT | Last update timestamp |

**Unique Constraint:** `(session_espn_competition_id, driver_id)`

**Foreign Keys:**
- `session_espn_competition_id` → `race_sessions.espn_competition_id`
- `driver_id` → `drivers.id`
- `team_id` → `teams.id`

**Populated by:** `scripts/populate_all_races.py`

---

## Entity Relationships

```
seasons (year)
    ├── races (year FK)
    │   └── race_sessions (race_espn_event_id FK)
    │       └── session_results (session_espn_competition_id FK)
    │           ├── drivers (driver_id FK)
    │           └── teams (team_id FK)
    └── driver_seasons (year FK)
        └── drivers (driver_id FK)
```

## Data Hierarchy

1. **Season** → Multiple **Races** (round 1, 2, 3, ...)
2. **Race** → Multiple **Sessions** (FP1, FP2, FP3, Qualifying, Race)
3. **Session** → Multiple **Results** (one per driver)
4. **Result** → Links to **Driver** and **Team**

## ESPN ID Structure

ESPN uses a two-level hierarchy for F1 data:

### Event Level (Race Weekend)
- **ESPN Event ID** (e.g., `600041133`)
- Represents the entire race weekend
- Stored in: `races.espn_event_id`
- Used to group all sessions for a weekend

### Competition Level (Individual Session)
- **ESPN Competition ID** (e.g., `401622102`)
- Represents a single session (practice, qualifying, race)
- Stored in: `race_sessions.espn_competition_id`
- Used to link results to specific sessions

## Data Availability Notes

### Historical Data Limitations

ESPN's F1 API has different data availability based on era:

#### Pre-2009 (1950 - April 19, 2009)
- **Available:** Race results only
- **Not Available:** Practice sessions, qualifying sessions
- Reason: ESPN only tracked race results historically

#### Post-2009 (April 26, 2009 - Present)
- **Available:** All session data
  - 3× Free Practice sessions
  - Qualifying session
  - Race session
  - Sprint Shootout (sprint weekends)
  - Sprint Race (sprint weekends)

**Cutoff Date:** April 26, 2009 (Bahrain Grand Prix) - first race with full session data

### Sprint Weekend Format

Sprint weekends (introduced 2021) have a different session structure:
- Free Practice (1 session only, instead of 3)
- Sprint Shootout (qualifying for sprint)
- Sprint Race (short race on Saturday)
- Qualifying (for main race)
- Race (Sunday)

Detection: `races.has_sprint = 1`

## Current Data Statistics

As of last population:
- **Seasons:** 76 (1950-2025)
- **Races:** 1,127
- **Race Sessions:** 2,412
- **Session Results:** 53,869
- **Drivers:** ~850 unique drivers
- **Teams:** 170 (including historical constructors)

## Population Scripts

### Initial Setup
```bash
# 1. Populate seasons
python scripts/populate_seasons.py

# 2. Populate drivers
python scripts/populate_drivers.py

# 3. Populate races, sessions, and results
python scripts/populate_all_races.py --max-workers 10
```

### Incremental Updates
```bash
# Update specific year
python scripts/populate_races.py --year 2024

# Update multiple years
python scripts/populate_all_races.py --start-year 2023 --end-year 2024
```

## Query Examples

### Get all sessions for a race
```sql
SELECT rs.session_type, rs.session_date
FROM races r
JOIN race_sessions rs ON r.espn_event_id = rs.race_espn_event_id
WHERE r.year = 2024 AND r.round_number = 1
ORDER BY rs.session_date;
```

### Get race results with driver and team info
```sql
SELECT
    sr.position,
    d.display_name as driver,
    t.display_name as team,
    sr.points
FROM session_results sr
JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
JOIN races r ON rs.race_espn_event_id = r.espn_event_id
JOIN drivers d ON sr.driver_id = d.id
JOIN teams t ON sr.team_id = t.id
WHERE r.year = 2024
  AND r.round_number = 1
  AND rs.session_type = 'Race'
ORDER BY sr.position;
```

### Get all drivers who raced in a specific year
```sql
SELECT DISTINCT d.display_name, d.nationality
FROM drivers d
JOIN driver_seasons ds ON d.id = ds.driver_id
WHERE ds.year = 2024
ORDER BY d.last_name;
```

### Get sprint race weekends in a season
```sql
SELECT
    r.round_number,
    r.event_name,
    r.location,
    r.event_date
FROM races r
WHERE r.year = 2024 AND r.has_sprint = 1
ORDER BY r.round_number;
```

## Index Recommendations

Current primary keys provide efficient lookups:
- Event lookups by ESPN ID: `races.espn_event_id`
- Session lookups by ESPN ID: `race_sessions.espn_competition_id`
- Driver lookups by ESPN ID: `drivers.id`

Additional indexes may be beneficial for:
```sql
CREATE INDEX idx_races_year_round ON races(year, round_number);
CREATE INDEX idx_race_sessions_race_id ON race_sessions(race_espn_event_id);
CREATE INDEX idx_session_results_session ON session_results(session_espn_competition_id);
CREATE INDEX idx_session_results_driver ON session_results(driver_id);
```

## Notes

- All timestamps use `CURRENT_TIMESTAMP` as default
- Text fields use UTF-8 encoding
- Boolean fields stored as INTEGER (0/1)
- Dates stored as TEXT in ISO 8601 format (YYYY-MM-DD)
- ESPN IDs are stable and used for `INSERT OR REPLACE` upserts
