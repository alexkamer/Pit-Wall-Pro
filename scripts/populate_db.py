#!/usr/bin/env python3
"""Populate the F1 database with ESPN and FastF1 data."""

import sys
import logging
from pathlib import Path
import argparse
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f1_webapp.db.database import initialize_database, get_db_connection
from f1_webapp.espn.client import ESPNClient
from f1_webapp.fastf1.client import FastF1Client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def populate_season_data(year: int, espn: ESPNClient, ff1: FastF1Client, conn):
    """Populate all data for a given season.

    Args:
        year: Season year
        espn: ESPN API client
        ff1: FastF1 API client
        conn: Database connection
    """
    cursor = conn.cursor()

    logger.info(f"Populating data for {year} season")

    # Insert season
    cursor.execute(
        "INSERT OR REPLACE INTO seasons (year, updated_at) VALUES (?, ?)",
        (year, datetime.now())
    )

    # Get schedule from FastF1
    try:
        logger.info("Fetching schedule...")
        schedule = ff1.get_event_schedule(year)

        for _, race in schedule.iterrows():
            round_num = int(race['RoundNumber'])
            event_format = race.get('EventFormat', 'conventional')
            has_sprint = event_format == 'sprint_qualifying'

            cursor.execute("""
                INSERT OR REPLACE INTO races
                (year, round_number, event_name, official_event_name, country, location,
                 circuit_name, event_date, event_format, has_sprint, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                year, round_num,
                race.get('EventName'),
                race.get('OfficialEventName'),
                race.get('Country'),
                race.get('Location'),
                race.get('EventName'),  # Using EventName as circuit for now
                str(race.get('EventDate')),
                event_format,
                1 if has_sprint else 0,
                datetime.now()
            ))

            race_id = cursor.lastrowid if cursor.lastrowid else cursor.execute(
                "SELECT id FROM races WHERE year = ? AND round_number = ?",
                (year, round_num)
            ).fetchone()[0]

            # Try to get race results
            try:
                logger.info(f"Fetching race results for round {round_num}...")
                race_session = ff1.load_session(year, round_num, 'R', telemetry=False, weather=False, messages=False)
                results = ff1.get_session_results(race_session)

                for _, result in results.iterrows():
                    driver_abbr = result.get('Abbreviation')
                    team_name = result.get('TeamName')

                    # Store driver info
                    cursor.execute("""
                        INSERT OR IGNORE INTO drivers
                        (id, abbreviation, full_name, number, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        driver_abbr, driver_abbr,
                        result.get('FullName'),
                        str(result.get('DriverNumber')),
                        datetime.now()
                    ))

                    # Store team info
                    if team_name:
                        cursor.execute("""
                            INSERT OR IGNORE INTO teams
                            (id, name, display_name, color, updated_at)
                            VALUES (?, ?, ?, ?, ?)
                        """, (
                            team_name.replace(' ', '_').lower(),
                            team_name, team_name,
                            result.get('TeamColor'),
                            datetime.now()
                        ))

                    # Store race result
                    cursor.execute("""
                        INSERT OR REPLACE INTO race_results
                        (race_id, driver_id, team_id, position, grid_position, points,
                         laps_completed, status, time, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        race_id, driver_abbr,
                        team_name.replace(' ', '_').lower() if team_name else None,
                        int(result.get('Position')) if result.get('Position') else None,
                        int(result.get('GridPosition')) if result.get('GridPosition') else None,
                        float(result.get('Points', 0)),
                        int(result.get('Laps', 0)),
                        result.get('Status'),
                        str(result.get('Time')) if result.get('Time') else None,
                        datetime.now()
                    ))
            except Exception as e:
                logger.warning(f"Could not fetch race results for round {round_num}: {e}")

            # Try to get qualifying results
            try:
                logger.info(f"Fetching qualifying results for round {round_num}...")
                quali_session = ff1.load_session(year, round_num, 'Q', telemetry=False, weather=False, messages=False)
                results = ff1.get_session_results(quali_session)

                for _, result in results.iterrows():
                    driver_abbr = result.get('Abbreviation')
                    team_name = result.get('TeamName')

                    cursor.execute("""
                        INSERT OR REPLACE INTO qualifying_results
                        (race_id, driver_id, team_id, position, q1_time, q2_time, q3_time, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        race_id, driver_abbr,
                        team_name.replace(' ', '_').lower() if team_name else None,
                        int(result.get('Position')) if result.get('Position') else None,
                        str(result.get('Q1')) if result.get('Q1') else None,
                        str(result.get('Q2')) if result.get('Q2') else None,
                        str(result.get('Q3')) if result.get('Q3') else None,
                        datetime.now()
                    ))
            except Exception as e:
                logger.warning(f"Could not fetch qualifying results for round {round_num}: {e}")

            # Try to get sprint results if applicable
            if has_sprint:
                try:
                    logger.info(f"Fetching sprint results for round {round_num}...")
                    sprint_session = ff1.load_session(year, round_num, 'S', telemetry=False, weather=False, messages=False)
                    results = ff1.get_session_results(sprint_session)

                    for _, result in results.iterrows():
                        driver_abbr = result.get('Abbreviation')
                        team_name = result.get('TeamName')

                        cursor.execute("""
                            INSERT OR REPLACE INTO sprint_results
                            (race_id, driver_id, team_id, position, grid_position, points,
                             laps_completed, status, updated_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            race_id, driver_abbr,
                            team_name.replace(' ', '_').lower() if team_name else None,
                            int(result.get('Position')) if result.get('Position') else None,
                            int(result.get('GridPosition')) if result.get('GridPosition') else None,
                            float(result.get('Points', 0)),
                            int(result.get('Laps', 0)),
                            result.get('Status'),
                            datetime.now()
                        ))
                except Exception as e:
                    logger.warning(f"Could not fetch sprint results for round {round_num}: {e}")

        conn.commit()
        logger.info(f"Successfully populated race data for {year}")

    except Exception as e:
        logger.error(f"Error populating season data: {e}")
        conn.rollback()
        raise

    # Get driver standings from ESPN
    try:
        logger.info("Fetching driver standings from ESPN...")
        standings_data = espn.get_standings(year, "driver")

        for standing in standings_data.get('standings', []):
            driver_ref = standing.get('athlete', {}).get('$ref', '')
            driver_id = driver_ref.split('/')[-1].split('?')[0]

            # Get driver details
            try:
                driver = espn.get_driver(driver_id)
                driver_abbr = driver.get('abbreviation')

                # Get driver details - firstName and lastName are at top level
                first_name = driver.get('firstName', '')
                last_name = driver.get('lastName', '')
                full_name = driver.get('displayName') or driver.get('fullName', '')

                cursor.execute("""
                    INSERT OR REPLACE INTO drivers
                    (id, abbreviation, first_name, last_name, full_name,
                     number, nationality, headshot_url, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    driver_id,  # Use ESPN numeric ID as primary key
                    driver_abbr,
                    first_name if first_name else None,
                    last_name if last_name else None,
                    full_name if full_name else None,
                    driver.get('vehicles', [{}])[0].get('number') if driver.get('vehicles') else None,
                    driver.get('flag', {}).get('alt'),
                    driver.get('headshot', {}).get('href'),
                    datetime.now()
                ))

                # Get stats
                stats = standing.get('records', [{}])[0].get('stats', [])
                stats_dict = {s['name']: s['value'] for s in stats}

                cursor.execute("""
                    INSERT OR REPLACE INTO driver_standings
                    (year, driver_id, position, points, wins, poles, dnfs, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    year, driver_id,  # Use ESPN numeric ID
                    int(stats_dict.get('rank', 0)),
                    float(stats_dict.get('championshipPts', 0)),
                    int(stats_dict.get('wins', 0)),
                    int(stats_dict.get('poles', 0)),
                    int(stats_dict.get('dnf', 0)),
                    datetime.now()
                ))

            except Exception as e:
                logger.warning(f"Error processing driver {driver_id}: {e}")

        conn.commit()
        logger.info(f"Successfully populated driver standings for {year}")

    except Exception as e:
        logger.error(f"Error fetching driver standings: {e}")

    # Get constructor standings from ESPN
    try:
        logger.info("Fetching constructor standings from ESPN...")
        standings_data = espn.get_standings(year, "constructor")

        for standing in standings_data.get('standings', []):
            manufacturer_ref = standing.get('manufacturer', {}).get('$ref', '')

            try:
                # Fetch manufacturer details
                import requests
                manufacturer = requests.get(manufacturer_ref).json()
                team_name = manufacturer.get('displayName') or manufacturer.get('name')
                team_id = team_name.replace(' ', '_').lower()

                cursor.execute("""
                    INSERT OR REPLACE INTO teams
                    (id, name, display_name, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    team_id, team_name, team_name,
                    datetime.now()
                ))

                # Get stats
                stats = standing.get('records', [{}])[0].get('stats', [])
                stats_dict = {s['name']: s['value'] for s in stats}

                cursor.execute("""
                    INSERT OR REPLACE INTO constructor_standings
                    (year, team_id, position, points, wins, poles, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    year, team_id,
                    int(stats_dict.get('rank', 0)),
                    float(stats_dict.get('points', 0)),
                    int(stats_dict.get('wins', 0)),
                    int(stats_dict.get('poles', 0)),
                    datetime.now()
                ))

            except Exception as e:
                logger.warning(f"Error processing constructor: {e}")

        conn.commit()
        logger.info(f"Successfully populated constructor standings for {year}")

    except Exception as e:
        logger.error(f"Error fetching constructor standings: {e}")


def main():
    parser = argparse.ArgumentParser(description='Populate F1 database with ESPN and FastF1 data')
    parser.add_argument('--year', type=int, help='Single season year to populate')
    parser.add_argument('--start-year', type=int, default=2018, help='Start year for range (default: 2018)')
    parser.add_argument('--end-year', type=int, default=2024, help='End year for range (default: 2024)')
    parser.add_argument('--all-seasons', action='store_true', help='Populate all available seasons (2018-2024)')
    parser.add_argument('--db-path', type=str, help='Path to SQLite database file')
    parser.add_argument('--init', action='store_true', help='Initialize database schema first')

    args = parser.parse_args()

    # Initialize database if requested
    if args.init:
        logger.info("Initializing database schema...")
        initialize_database(args.db_path)

    # Create API clients
    espn = ESPNClient()
    ff1 = FastF1Client()

    # Get database connection
    conn = get_db_connection(args.db_path)

    try:
        # Determine which years to populate
        if args.year:
            # Single year
            years = [args.year]
        elif args.all_seasons:
            # All seasons from 2018 to 2024
            years = list(range(2018, 2025))
        else:
            # Range of years
            years = list(range(args.start_year, args.end_year + 1))

        logger.info(f"Populating seasons: {years}")

        for year in years:
            logger.info(f"\n{'='*60}")
            logger.info(f"Processing season {year}")
            logger.info(f"{'='*60}\n")
            try:
                populate_season_data(year, espn, ff1, conn)
            except Exception as e:
                logger.error(f"Failed to populate {year} season: {e}")
                # Continue with next season instead of failing completely
                continue

        logger.info("\n" + "="*60)
        logger.info("Database population complete!")
        logger.info("="*60)
    except Exception as e:
        logger.error(f"Failed to populate database: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
