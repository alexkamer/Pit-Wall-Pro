#!/usr/bin/env python3
"""Populate database with ALL ESPN F1 data (all 76 seasons from 1950-2025)."""

import sys
import logging
from pathlib import Path
import argparse
from datetime import datetime
import requests
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f1_webapp.db.database import initialize_database, get_db_connection
from f1_webapp.espn.client import ESPNClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_all_espn_seasons():
    """Get all available F1 seasons from ESPN."""
    url = "http://sports.core.api.espn.com/v2/sports/racing/leagues/f1/seasons?limit=100"
    response = requests.get(url)
    data = response.json()

    # Extract years from the refs
    years = []
    for item in data.get('items', []):
        ref = item.get('$ref', '')
        year = ref.split('/seasons/')[-1].split('?')[0]
        if year.isdigit():
            years.append(int(year))

    years.sort()
    logger.info(f"Found {len(years)} seasons from ESPN: {min(years)}-{max(years)}")
    return years


def populate_season_from_espn(year: int, espn: ESPNClient, conn):
    """Populate a season using ESPN API data.

    Args:
        year: Season year
        espn: ESPN API client
        conn: Database connection
    """
    cursor = conn.cursor()
    logger.info(f"Processing {year} season from ESPN")

    # Insert season
    cursor.execute(
        "INSERT OR REPLACE INTO seasons (year, updated_at) VALUES (?, ?)",
        (year, datetime.now())
    )

    try:
        # Get events/races for the season
        logger.info(f"Fetching events for {year}...")
        events_data = espn.get_events(year, limit=50)

        for event in events_data.get('items', []):
            try:
                # Fetch event details
                event_ref = event.get('$ref', '')
                event_detail = requests.get(event_ref).json()

                event_name = event_detail.get('name', 'Unknown')
                event_date = event_detail.get('date')

                # Try to extract round number from event
                round_num = None
                for comp in event_detail.get('competitions', []):
                    try:
                        comp_ref = comp.get('$ref', '')
                        comp_detail = requests.get(comp_ref).json()
                        # Try to get round from competition
                        if 'week' in comp_detail:
                            round_num = comp_detail['week'].get('number')
                        elif 'season' in comp_detail:
                            # Some events have the round in competitors
                            pass
                    except:
                        pass

                if not round_num:
                    # Guess round number from position in list
                    round_num = events_data['items'].index(event) + 1

                logger.info(f"  - Round {round_num}: {event_name}")

                # Insert race
                cursor.execute("""
                    INSERT OR REPLACE INTO races
                    (year, round_number, event_name, country, event_date, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    year, round_num, event_name,
                    event_detail.get('location', 'Unknown'),
                    event_date,
                    datetime.now()
                ))

                race_id = cursor.lastrowid if cursor.lastrowid else cursor.execute(
                    "SELECT id FROM races WHERE year = ? AND round_number = ?",
                    (year, round_num)
                ).fetchone()[0]

                # Try to get race results from competitions
                for comp in event_detail.get('competitions', []):
                    try:
                        comp_ref = comp.get('$ref', '')
                        comp_detail = requests.get(comp_ref).json()

                        # Get competitors (drivers/teams)
                        for competitor in comp_detail.get('competitors', []):
                            try:
                                athlete_ref = competitor.get('athlete', {}).get('$ref', '')
                                if not athlete_ref:
                                    continue

                                # Extract ESPN driver ID from URL
                                driver_id = athlete_ref.split('/')[-1].split('?')[0]

                                athlete = requests.get(athlete_ref).json()
                                driver_abbr = athlete.get('abbreviation', driver_id)

                                # Store driver info
                                cursor.execute("""
                                    INSERT OR IGNORE INTO drivers
                                    (id, abbreviation, first_name, last_name, full_name, updated_at)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (
                                    driver_id,  # Use ESPN numeric ID
                                    driver_abbr,
                                    athlete.get('firstName'),
                                    athlete.get('lastName'),
                                    athlete.get('displayName') or athlete.get('fullName'),
                                    datetime.now()
                                ))

                                # Get team if available
                                team_ref = competitor.get('team', {}).get('$ref', '')
                                team_id = None
                                if team_ref:
                                    try:
                                        team = requests.get(team_ref).json()
                                        team_name = team.get('displayName') or team.get('name')
                                        team_id = team_name.replace(' ', '_').lower() if team_name else None

                                        if team_id:
                                            cursor.execute("""
                                                INSERT OR IGNORE INTO teams
                                                (id, name, display_name, updated_at)
                                                VALUES (?, ?, ?, ?)
                                            """, (team_id, team_name, team_name, datetime.now()))
                                    except:
                                        pass

                                # Store race result if we have position/points
                                position = competitor.get('order')
                                winner = competitor.get('winner', False)

                                if position or winner:
                                    cursor.execute("""
                                        INSERT OR REPLACE INTO race_results
                                        (race_id, driver_id, team_id, position, updated_at)
                                        VALUES (?, ?, ?, ?, ?)
                                    """, (
                                        race_id, driver_id, team_id,  # Use ESPN numeric ID
                                        1 if winner else position,
                                        datetime.now()
                                    ))

                            except Exception as e:
                                logger.debug(f"Error processing competitor: {e}")
                                continue

                    except Exception as e:
                        logger.debug(f"Error processing competition: {e}")
                        continue

                time.sleep(0.1)  # Rate limiting

            except Exception as e:
                logger.warning(f"Error processing event: {e}")
                continue

        conn.commit()

    except Exception as e:
        logger.error(f"Error fetching events for {year}: {e}")
        conn.rollback()

    # Get driver standings
    try:
        logger.info(f"Fetching driver standings for {year}...")
        standings_data = espn.get_standings(year, "driver")

        for standing in standings_data.get('standings', []):
            driver_ref = standing.get('athlete', {}).get('$ref', '')
            if not driver_ref:
                continue

            driver_id = driver_ref.split('/')[-1].split('?')[0]

            try:
                driver = espn.get_driver(driver_id)
                driver_abbr = driver.get('abbreviation', driver_id)

                # Get driver details - firstName and lastName are at top level
                first_name = driver.get('firstName', '')
                last_name = driver.get('lastName', '')
                full_name = driver.get('displayName') or driver.get('fullName', '')

                # Update driver info
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

                # Update standings
                stats = standing.get('records', [{}])[0].get('stats', [])
                stats_dict = {s['name']: s['value'] for s in stats}

                cursor.execute("""
                    INSERT OR REPLACE INTO driver_standings
                    (year, driver_id, position, points, wins, poles, dnfs, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    year, driver_id,  # Use ESPN numeric ID
                    int(stats_dict.get('rank', 0)),
                    float(stats_dict.get('championshipPts', 0) or stats_dict.get('points', 0)),
                    int(stats_dict.get('wins', 0)),
                    int(stats_dict.get('poles', 0)),
                    int(stats_dict.get('dnf', 0)),
                    datetime.now()
                ))

            except Exception as e:
                logger.debug(f"Error processing driver {driver_id}: {e}")

        conn.commit()
        logger.info(f"✓ Completed {year} season")

    except Exception as e:
        logger.warning(f"Error fetching driver standings for {year}: {e}")


def main():
    parser = argparse.ArgumentParser(description='Populate database with ALL ESPN F1 data')
    parser.add_argument('--db-path', type=str, help='Path to SQLite database file')
    parser.add_argument('--init', action='store_true', help='Initialize database schema first')
    parser.add_argument('--start-year', type=int, help='Start from specific year')
    parser.add_argument('--end-year', type=int, help='End at specific year')

    args = parser.parse_args()

    # Initialize database if requested
    if args.init:
        logger.info("Initializing database schema...")
        initialize_database(args.db_path)

    # Create ESPN client
    espn = ESPNClient()

    # Get all available seasons
    all_years = get_all_espn_seasons()

    # Filter by start/end year if specified
    if args.start_year:
        all_years = [y for y in all_years if y >= args.start_year]
    if args.end_year:
        all_years = [y for y in all_years if y <= args.end_year]

    logger.info(f"Will process {len(all_years)} seasons")

    # Get database connection
    conn = get_db_connection(args.db_path)

    try:
        for i, year in enumerate(all_years, 1):
            logger.info(f"\n{'='*60}")
            logger.info(f"Season {i}/{len(all_years)}: {year}")
            logger.info(f"{'='*60}\n")

            try:
                populate_season_from_espn(year, espn, conn)
            except Exception as e:
                logger.error(f"Failed to populate {year}: {e}")
                continue

        logger.info("\n" + "="*60)
        logger.info(f"✓ Database population complete! Processed {len(all_years)} seasons")
        logger.info("="*60)

    except KeyboardInterrupt:
        logger.info("\nInterrupted by user. Committing current data...")
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to populate database: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
