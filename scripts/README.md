# F1 Database Scripts

These scripts manage the local SQLite database for caching F1 data from ESPN and FastF1 APIs.

## Scripts

### populate_db.py

Initial database population script. Run this once to set up the database and load all historical data for a season.

**Usage:**
```bash
# Initialize database and populate ALL seasons (2018-2024) - RECOMMENDED
cd src && uv run python ../scripts/populate_db.py --init --all-seasons

# Initialize database and populate with 2024 season only
cd src && uv run python ../scripts/populate_db.py --init --year 2024

# Populate a range of years (database must already be initialized)
cd src && uv run python ../scripts/populate_db.py --start-year 2020 --end-year 2023

# Populate a single year
cd src && uv run python ../scripts/populate_db.py --year 2023
```

**Options:**
- `--init`: Initialize the database schema before populating (required for first run)
- `--all-seasons`: Populate all available seasons (2018-2024) - recommended for full historical data
- `--year YEAR`: Single season year to populate
- `--start-year YEAR`: Start year for range (default: 2018)
- `--end-year YEAR`: End year for range (default: 2024)
- `--db-path PATH`: Custom path to database file (default: f1_data.db in project root)

### update_db.py

Incremental update script. Run this regularly to fetch only new/changed data without re-processing everything.

**Usage:**
```bash
# Update all data for current season
cd src && uv run python ../scripts/update_db.py --year 2024

# Update only standings (faster)
cd src && uv run python ../scripts/update_db.py --year 2024 --standings-only

# Update specific round
cd src && uv run python ../scripts/update_db.py --year 2024 --round 5
```

**Options:**
- `--year YEAR`: Season year to update (default: 2024)
- `--round NUM`: Update only a specific round number
- `--standings-only`: Only update championship standings, skip race data
- `--db-path PATH`: Custom path to database file

**Smart Updates:**
- Only updates data that changed or is older than 1 hour
- Uses INSERT OR REPLACE to avoid duplicates
- Much faster than full population

## Database Schema

The database includes tables for:
- **drivers**: Driver information and profiles
  - Uses ESPN numeric IDs as primary keys (e.g., "4665" for Verstappen)
  - Abbreviations stored separately (not unique, as drivers across eras may share them)
- **teams**: Constructor/team information
- **seasons**: Season records
- **races**: Race schedule and event information
- **race_results**: Individual race finishing positions and points
- **qualifying_results**: Qualifying session results
- **sprint_results**: Sprint race results
- **driver_standings**: Championship standings for drivers
- **constructor_standings**: Championship standings for constructors
- **driver_race_points**: Race-by-race points for each driver
- **constructor_race_points**: Race-by-race points for each team

### Driver ID Schema
As of the latest migration, driver IDs use ESPN's numeric athlete IDs instead of abbreviations:
- **Primary Key**: ESPN numeric ID (e.g., "4665", "4667")
- **Abbreviation**: Stored as separate field (e.g., "VER", "HAM")
- **Benefits**: Unique identification across all seasons, handles duplicate abbreviations across eras

## Scheduled Updates

For production, consider scheduling `update_db.py` to run:
- Every hour during race weekends
- Daily during off-season
- Immediately after each session (qualifying, sprint, race)

Example cron job (runs every hour):
```cron
0 * * * * cd /path/to/f1_webapp/src && uv run python ../scripts/update_db.py --year 2024
```

## Performance

- **Initial Population**: ~10-15 minutes for full season (24 races with qualifying and race data)
- **Incremental Update**: ~30 seconds for recent changes
- **Query Speed**: <10ms for most queries (vs 20-30 seconds from APIs)
