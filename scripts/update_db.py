#!/usr/bin/env python3
"""Update the F1 database with latest data (incremental updates only)."""

import sys
import logging
from pathlib import Path
import argparse
from datetime import datetime, timedelta

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f1_webapp.db.database import get_db_connection
from f1_webapp.espn.client import ESPNClient
from f1_webapp.fastf1.client import FastF1Client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def update_race_data(year: int, round_num: int, ff1: FastF1Client, conn):
    """Update race data for a specific round.

    Only updates if data has changed or doesn't exist.

    Args:
        year: Season year
        round_num: Round number
        ff1: FastF1 API client
        conn: Database connection
    """
    cursor = conn.cursor()

    # Get race_id
    cursor.execute(
        "SELECT id FROM races WHERE year = ? AND round_number = ?",
        (year, round_num)
    )
    race_row = cursor.fetchone()
    if not race_row:
        logger.warning(f"Race not found for {year} round {round_num}")
        return

    race_id = race_row[0]

    # Check when race results were last updated
    cursor.execute(
        "SELECT updated_at FROM race_results WHERE race_id = ? ORDER BY updated_at DESC LIMIT 1",
        (race_id,)
    )
    last_update = cursor.fetchone()

    # Only update if not updated in last hour
    if last_update:
        last_update_time = datetime.fromisoformat(last_update[0])
        if datetime.now() - last_update_time < timedelta(hours=1):
            logger.info(f"Race {round_num} data recently updated, skipping")
            return

    # Fetch and update race results
    try:
        logger.info(f"Updating race results for round {round_num}...")
        race_session = ff1.load_session(year, round_num, 'R', telemetry=False, weather=False, messages=False)
        results = ff1.get_session_results(race_session)

        for _, result in results.iterrows():
            driver_abbr = result.get('Abbreviation')
            team_name = result.get('TeamName')

            # Update driver info
            cursor.execute("""
                INSERT OR REPLACE INTO drivers
                (id, abbreviation, full_name, number, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (
                driver_abbr, driver_abbr,
                result.get('FullName'),
                str(result.get('DriverNumber')),
                datetime.now()
            ))

            # Update team info
            if team_name:
                cursor.execute("""
                    INSERT OR REPLACE INTO teams
                    (id, name, display_name, color, updated_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    team_name.replace(' ', '_').lower(),
                    team_name, team_name,
                    result.get('TeamColor'),
                    datetime.now()
                ))

            # Update race result
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

        conn.commit()
        logger.info(f"Updated race results for round {round_num}")

    except Exception as e:
        logger.warning(f"Could not update race results for round {round_num}: {e}")

    # Update qualifying if needed
    try:
        logger.info(f"Updating qualifying results for round {round_num}...")
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

        conn.commit()
        logger.info(f"Updated qualifying results for round {round_num}")

    except Exception as e:
        logger.warning(f"Could not update qualifying results for round {round_num}: {e}")


def update_standings(year: int, espn: ESPNClient, conn):
    """Update driver and constructor standings.

    Args:
        year: Season year
        espn: ESPN API client
        conn: Database connection
    """
    cursor = conn.cursor()

    # Update driver standings
    try:
        logger.info("Updating driver standings...")
        standings_data = espn.get_standings(year, "driver")

        for standing in standings_data.get('standings', []):
            driver_ref = standing.get('athlete', {}).get('$ref', '')
            driver_id = driver_ref.split('/')[-1].split('?')[0]

            try:
                driver = espn.get_driver(driver_id)
                driver_abbr = driver.get('abbreviation')

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
                    driver_abbr, driver_abbr,
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
                    year, driver_abbr,
                    int(stats_dict.get('rank', 0)),
                    float(stats_dict.get('championshipPts', 0)),
                    int(stats_dict.get('wins', 0)),
                    int(stats_dict.get('poles', 0)),
                    int(stats_dict.get('dnf', 0)),
                    datetime.now()
                ))

            except Exception as e:
                logger.warning(f"Error updating driver {driver_id}: {e}")

        conn.commit()
        logger.info("Updated driver standings")

    except Exception as e:
        logger.error(f"Error updating driver standings: {e}")

    # Update constructor standings
    try:
        logger.info("Updating constructor standings...")
        standings_data = espn.get_standings(year, "constructor")

        for standing in standings_data.get('standings', []):
            manufacturer_ref = standing.get('manufacturer', {}).get('$ref', '')

            try:
                import requests
                manufacturer = requests.get(manufacturer_ref).json()
                team_name = manufacturer.get('displayName') or manufacturer.get('name')
                team_id = team_name.replace(' ', '_').lower()

                # Update team info
                cursor.execute("""
                    INSERT OR REPLACE INTO teams
                    (id, name, display_name, updated_at)
                    VALUES (?, ?, ?, ?)
                """, (
                    team_id, team_name, team_name,
                    datetime.now()
                ))

                # Update standings
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
                logger.warning(f"Error updating constructor: {e}")

        conn.commit()
        logger.info("Updated constructor standings")

    except Exception as e:
        logger.error(f"Error updating constructor standings: {e}")


def main():
    parser = argparse.ArgumentParser(description='Update F1 database incrementally')
    parser.add_argument('--year', type=int, default=2024, help='Season year to update')
    parser.add_argument('--round', type=int, help='Specific round to update (default: all rounds)')
    parser.add_argument('--db-path', type=str, help='Path to SQLite database file')
    parser.add_argument('--standings-only', action='store_true', help='Only update standings, not race data')

    args = parser.parse_args()

    # Create API clients
    espn = ESPNClient()
    ff1 = FastF1Client()

    # Get database connection
    conn = get_db_connection(args.db_path)

    try:
        # Update standings
        update_standings(args.year, espn, conn)

        if not args.standings_only:
            # Get all rounds from database
            cursor = conn.cursor()
            cursor.execute(
                "SELECT round_number FROM races WHERE year = ? ORDER BY round_number",
                (args.year,)
            )
            rounds = [row[0] for row in cursor.fetchall()]

            if args.round:
                # Update specific round
                if args.round in rounds:
                    update_race_data(args.year, args.round, ff1, conn)
                else:
                    logger.warning(f"Round {args.round} not found in database")
            else:
                # Update all rounds
                for round_num in rounds:
                    update_race_data(args.year, round_num, ff1, conn)

        logger.info("Database update complete!")

    except Exception as e:
        logger.error(f"Failed to update database: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
