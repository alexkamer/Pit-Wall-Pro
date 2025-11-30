#!/usr/bin/env python3
"""Final ESPN population - uses ESPN IDs, no generated IDs, with multithreading."""

import sys
import logging
from pathlib import Path
import argparse
from datetime import datetime
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f1_webapp.db.database import initialize_database, get_db_connection
from f1_webapp.espn.client import ESPNClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Thread-safe counter
class Counter:
    def __init__(self):
        self.value = 0
        self.lock = threading.Lock()

    def increment(self):
        with self.lock:
            self.value += 1
            return self.value


def populate_season(year: int, espn: ESPNClient, db_path: str, db_lock: threading.Lock):
    """Populate ALL data for a season using ESPN IDs.

    Args:
        year: Season year
        espn: ESPN API client
        db_path: Path to SQLite database
        db_lock: Thread lock for database access

    Returns:
        Success message or error
    """
    conn = get_db_connection(db_path)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout = 60000")  # 60 second timeout
    cursor = conn.cursor()

    try:
        # Insert season
        cursor.execute(
            "INSERT OR REPLACE INTO seasons (year, updated_at) VALUES (?, ?)",
            (year, datetime.now())
        )

        # === DRIVER STANDINGS ===
        try:
            standings_data = espn.get_driver_standings(year)

            for standing in standings_data.get('standings', []):
                driver_ref = standing.get('athlete', {}).get('$ref', '')
                if not driver_ref:
                    continue

                driver_id = driver_ref.split('/')[-1].split('?')[0]

                try:
                    driver = espn.get_driver(driver_id)
                    driver_abbr = driver.get('abbreviation', driver_id)
                    first_name = driver.get('firstName', '')
                    last_name = driver.get('lastName', '')
                    full_name = driver.get('displayName') or driver.get('fullName', '')

                    cursor.execute("""
                        INSERT OR REPLACE INTO drivers
                        (id, abbreviation, first_name, last_name, full_name,
                         number, nationality, headshot_url, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        driver_id, driver_abbr,
                        first_name if first_name else None,
                        last_name if last_name else None,
                        full_name if full_name else None,
                        driver.get('vehicles', [{}])[0].get('number') if driver.get('vehicles') else None,
                        driver.get('flag', {}).get('alt'),
                        driver.get('headshot', {}).get('href'),
                        datetime.now()
                    ))

                    stats = standing.get('records', [{}])[0].get('stats', [])
                    stats_dict = {s['name']: s['value'] for s in stats}

                    cursor.execute("""
                        INSERT OR REPLACE INTO driver_standings
                        (year, driver_id, position, points, wins, poles, dnfs, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        year, driver_id,
                        int(stats_dict.get('rank', 0)),
                        float(stats_dict.get('championshipPts', 0) or stats_dict.get('points', 0)),
                        int(stats_dict.get('wins', 0)),
                        int(stats_dict.get('poles', 0)),
                        int(stats_dict.get('dnf', 0)),
                        datetime.now()
                    ))

                except Exception as e:
                    logger.debug(f"Error processing driver {driver_id}: {e}")

        except Exception as e:
            logger.debug(f"No driver standings for {year}: {e}")

        # === CONSTRUCTOR STANDINGS ===
        try:
            constructor_data = espn.get_constructor_standings(year)

            for standing in constructor_data.get('standings', []):
                manufacturer_ref = standing.get('manufacturer', {}).get('$ref', '')
                if not manufacturer_ref:
                    continue

                try:
                    manufacturer = requests.get(manufacturer_ref).json()
                    team_name = manufacturer.get('displayName') or manufacturer.get('name')
                    if not team_name:
                        continue

                    team_id = team_name.replace(' ', '_').lower()

                    cursor.execute("""
                        INSERT OR REPLACE INTO teams
                        (id, name, display_name, logo_url, updated_at)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        team_id, team_name, team_name,
                        manufacturer.get('logos', [{}])[0].get('href') if manufacturer.get('logos') else None,
                        datetime.now()
                    ))

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
                    logger.debug(f"Error processing constructor: {e}")

        except Exception as e:
            logger.debug(f"No constructor standings for {year}: {e}")

        # === RACES AND EVENTS ===
        try:
            events_data = espn.get_events(year, limit=50)

            round_num = 0
            for event_item in events_data.get('items', []):
                try:
                    event_ref = event_item.get('$ref')
                    event = requests.get(event_ref).json()

                    event_id = event.get('id')
                    event_name = event.get('name', 'Unknown')
                    event_date = event.get('date')

                    round_num += 1  # Sequential round numbering

                    # Find the Race competition (not practice or qualifying)
                    race_competition_id = None
                    for comp_item in event.get('competitions', []):
                        comp_ref = comp_item.get('$ref')
                        comp_detail = requests.get(comp_ref).json()
                        comp_type = comp_detail.get('type', {}).get('text', '')

                        # Look for the main "Race" competition
                        if 'Race' in comp_type and 'Practice' not in comp_type:
                            race_competition_id = comp_detail.get('id')
                            break

                    # Insert race with ESPN IDs
                    cursor.execute("""
                        INSERT OR REPLACE INTO races
                        (year, round_number, event_name, country, event_date, espn_event_id, espn_competition_id, updated_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        year, round_num, event_name,
                        event.get('location', 'Unknown'),
                        event_date,
                        event_id,
                        race_competition_id,
                        datetime.now()
                    ))

                    race_id = cursor.lastrowid if cursor.lastrowid else cursor.execute(
                        "SELECT id FROM races WHERE year = ? AND round_number = ?",
                        (year, round_num)
                    ).fetchone()[0]

                    # Get race results from the Race competition
                    if race_competition_id:
                        try:
                            race_comp_url = f"http://sports.core.api.espn.com/v2/sports/racing/leagues/f1/events/{event_id}/competitions/{race_competition_id}"
                            race_comp = requests.get(race_comp_url, params={'lang': 'en', 'region': 'us'}).json()

                            for competitor in race_comp.get('competitors', []):
                                try:
                                    athlete_ref = competitor.get('athlete', {}).get('$ref', '')
                                    if not athlete_ref:
                                        continue

                                    driver_id = athlete_ref.split('/')[-1].split('?')[0]
                                    position = competitor.get('order')
                                    winner = competitor.get('winner', False)

                                    # Get team
                                    team_id = None
                                    team_ref = competitor.get('team', {}).get('$ref', '')
                                    if team_ref:
                                        try:
                                            team = requests.get(team_ref).json()
                                            team_name = team.get('displayName') or team.get('name')
                                            if team_name:
                                                team_id = team_name.replace(' ', '_').lower()
                                                cursor.execute("""
                                                    INSERT OR IGNORE INTO teams
                                                    (id, name, display_name, updated_at)
                                                    VALUES (?, ?, ?, ?)
                                                """, (team_id, team_name, team_name, datetime.now()))
                                        except:
                                            pass

                                    # Fetch statistics
                                    points = 0.0
                                    laps_completed = None
                                    status = None
                                    grid_position = None

                                    if competitor.get('statistics'):
                                        try:
                                            stats_ref = competitor['statistics'].get('$ref')
                                            stats_data = requests.get(stats_ref).json()

                                            if stats_data.get('splits', {}).get('categories'):
                                                for category in stats_data['splits']['categories']:
                                                    for stat in category.get('stats', []):
                                                        stat_name = stat.get('name')
                                                        stat_value = stat.get('value')

                                                        if stat_name == 'championshipPts':
                                                            points = float(stat_value) if stat_value else 0.0
                                                        elif stat_name == 'lapsCompleted':
                                                            laps_completed = int(stat_value) if stat_value else None
                                                        elif stat_name == 'status':
                                                            status = stat.get('displayValue')
                                                        elif stat_name == 'gridPosition':
                                                            grid_position = int(stat_value) if stat_value else None
                                        except Exception as e:
                                            logger.debug(f"Error fetching statistics: {e}")

                                    if position or winner:
                                        cursor.execute("""
                                            INSERT OR REPLACE INTO race_results
                                            (race_id, driver_id, team_id, position, grid_position, points,
                                             laps_completed, status, updated_at)
                                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                        """, (
                                            race_id, driver_id, team_id,
                                            1 if winner else position,
                                            grid_position,
                                            points,
                                            laps_completed,
                                            status,
                                            datetime.now()
                                        ))

                                except Exception as e:
                                    logger.debug(f"Error processing competitor: {e}")

                        except Exception as e:
                            logger.debug(f"Error processing race competition: {e}")

                    time.sleep(0.02)  # Rate limiting

                except Exception as e:
                    logger.debug(f"Error processing event: {e}")
                    continue

        except Exception as e:
            logger.debug(f"No events for {year}: {e}")

        # Commit with lock
        with db_lock:
            conn.commit()
        return f"✓ {year}"

    except Exception as e:
        logger.error(f"Error processing {year}: {e}")
        return f"✗ {year}"
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='Final ESPN population with correct IDs')
    parser.add_argument('--db-path', type=str, help='Path to SQLite database file')
    parser.add_argument('--init', action='store_true', help='Initialize database schema first')
    parser.add_argument('--start-year', type=int, default=1950, help='Start year')
    parser.add_argument('--end-year', type=int, default=2025, help='End year')
    parser.add_argument('--max-workers', type=int, default=25, help='Max concurrent workers')

    args = parser.parse_args()

    if args.init:
        logger.info("Initializing database schema...")
        initialize_database(args.db_path)

    espn = ESPNClient()

    # Get all seasons
    url = "http://sports.core.api.espn.com/v2/sports/racing/leagues/f1/seasons?limit=100"
    response = requests.get(url)
    data = response.json()

    years = []
    for item in data.get('items', []):
        ref = item.get('$ref', '')
        year = ref.split('/seasons/')[-1].split('?')[0]
        if year.isdigit():
            year_int = int(year)
            if args.start_year <= year_int <= args.end_year:
                years.append(year_int)

    years.sort()
    logger.info(f"Processing {len(years)} seasons from {min(years)}-{max(years)} with {args.max_workers} workers")

    counter = Counter()
    db_lock = threading.Lock()
    total = len(years)

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {
            executor.submit(populate_season, year, espn, args.db_path, db_lock): year
            for year in years
        }

        for future in as_completed(futures):
            year = futures[future]
            count = counter.increment()
            try:
                result = future.result()
                logger.info(f"[{count}/{total}] {result}")
            except Exception as e:
                logger.error(f"[{count}/{total}] ✗ {year}: {e}")

    logger.info(f"\n{'='*60}")
    logger.info(f"✓ Complete! Processed {total} seasons")
    logger.info(f"{'='*60}")


if __name__ == '__main__':
    main()
