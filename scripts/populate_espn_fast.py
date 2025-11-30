#!/usr/bin/env python3
"""Fast multithreaded populate using ESPN API data."""

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


def populate_driver_standings(year: int, espn: ESPNClient, db_path: str):
    """Populate driver standings for a year."""
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

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
                    driver_id,
                    driver_abbr,
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

        conn.commit()
        return f"✓ {year}"

    except Exception as e:
        logger.error(f"Error fetching standings for {year}: {e}")
        return f"✗ {year}"
    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description='Fast multithreaded ESPN population')
    parser.add_argument('--db-path', type=str, help='Path to SQLite database file')
    parser.add_argument('--init', action='store_true', help='Initialize database schema first')
    parser.add_argument('--start-year', type=int, default=1950, help='Start year')
    parser.add_argument('--end-year', type=int, default=2025, help='End year')
    parser.add_argument('--max-workers', type=int, default=25, help='Max concurrent workers')

    args = parser.parse_args()

    db_path = args.db_path

    if args.init:
        logger.info("Initializing database schema...")
        initialize_database(db_path)

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
    total = len(years)

    with ThreadPoolExecutor(max_workers=args.max_workers) as executor:
        futures = {
            executor.submit(populate_driver_standings, year, espn, db_path): year
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
    logger.info(f"✓ Database population complete! Processed {total} seasons")
    logger.info(f"{'='*60}")


if __name__ == '__main__':
    main()
