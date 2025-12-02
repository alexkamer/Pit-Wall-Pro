# F1 Database Scripts

These scripts manage the local SQLite database for caching F1 data from ESPN and FastF1 APIs.

## Overview

The scripts in this directory help you:
- Initialize and populate the database with historical F1 data
- Update existing data with new race results
- Manage team logos and driver information
- Migrate data formats

**Quick Start:** For new installations, run:
```bash
uv run python scripts/populate_espn_final.py
```

## Main Scripts

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

## Additional Scripts

### populate_espn_final.py
**Recommended for initial setup.** Comprehensive population script that loads all historical data from ESPN API.

```bash
uv run python scripts/populate_espn_final.py
```

Populates:
- All seasons from 1950 to present
- All race results and standings
- Driver and constructor information
- Sprint race data (where applicable)

### populate_team_logos.py
Downloads and caches team logos from Formula1.com.

```bash
uv run python scripts/populate_team_logos.py
```

### populate_drivers.py
Updates driver information and profiles.

```bash
uv run python scripts/populate_drivers.py
```

### populate_races.py
Populates race calendar and results for specific seasons.

```bash
uv run python scripts/populate_races.py
```

### migrate_to_espn_ids.py
Migration script to convert from abbreviation-based IDs to ESPN numeric IDs.

```bash
uv run python scripts/migrate_to_espn_ids.py
```

## Performance

- **Initial Population**: ~2-5 minutes for all seasons (1950-present)
- **Incremental Update**: ~30 seconds for recent changes
- **Query Speed**: <10ms for most queries (vs 20-30 seconds from APIs)

## Maintenance

### Regular Updates
For production deployments, schedule regular updates:

```bash
# Update current season data
uv run python scripts/update_db.py --year 2024

# Update only standings (faster)
uv run python scripts/update_db.py --year 2024 --standings-only
```

### Backup Database
Before major updates:

```bash
cp f1_data.db f1_data_backup_$(date +%Y%m%d).db
```

### Clear and Rebuild
To start fresh:

```bash
rm f1_data.db
uv run python scripts/populate_espn_final.py
```

## Troubleshooting

**Database locked error:**
- Close all connections to the database
- Ensure only one script is running at a time

**Missing data:**
- Re-run the populate script for that season
- Check ESPN API availability

**Slow performance:**
- Ensure database file is on local disk (not network drive)
- Check SQLite version: `sqlite3 --version`
- Rebuild database if fragmented: `sqlite3 f1_data.db "VACUUM;"`
