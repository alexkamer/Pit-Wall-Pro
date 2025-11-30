#!/usr/bin/env python3
"""Populate races, race_sessions, and session_results for all seasons using multithreading."""

import sys
import requests
from pathlib import Path
from datetime import datetime
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue
import threading
import logging

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f1_webapp.db.database import get_db_connection

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Thread-safe queue for database operations
db_queue = Queue()
db_lock = threading.Lock()


def fetch_year_data(year: int):
    """Fetch all race data for a given year from ESPN API."""
    try:
        events_url = f"http://sports.core.api.espn.com/v2/sports/racing/leagues/f1/events/?dates={year}&limit=100"
        response = requests.get(events_url, timeout=30)
        events_data = response.json()

        races_data = []
        sessions_data = []
        results_data = []
        teams_data = set()

        event_count = events_data.get('count', 0)
        logger.info(f"[{year}] Found {event_count} race weekends")

        for idx, event_item in enumerate(events_data.get('items', []), 1):
            event_url = event_item.get('$ref', '')

            # Fetch individual event
            event_response = requests.get(event_url, timeout=30)
            event = event_response.json()

            event_id = event.get('id')
            event_name = event.get('name', 'Unknown')
            official_event_name = event.get('shortName', event_name)
            event_date = event.get('date')

            # Get venue details
            country = None
            location = None
            circuit_name = None

            if event.get('venues'):
                venue_ref = event['venues'][0].get('$ref')
                if venue_ref:
                    try:
                        venue_response = requests.get(venue_ref, timeout=30)
                        venue = venue_response.json()
                        circuit_name = venue.get('fullName')
                        if venue.get('address'):
                            location = venue['address'].get('city')
                            country = venue['address'].get('country')
                    except Exception as e:
                        logger.warning(f"[{year}] Could not fetch venue for {event_name}: {e}")

            # Fetch all competitions and detect sprint weekend
            has_sprint = 0
            competitions_data = []

            for comp_item in event.get('competitions', []):
                comp_response = requests.get(comp_item.get('$ref', ''), timeout=30)
                comp = comp_response.json()
                competitions_data.append(comp)

                comp_type = comp.get('type', {}).get('text', '')
                if 'Sprint' in comp_type:
                    has_sprint = 1

            # Add race data
            races_data.append({
                'espn_event_id': event_id,
                'year': year,
                'round_number': idx,
                'event_name': event_name,
                'official_event_name': official_event_name,
                'country': country,
                'location': location,
                'circuit_name': circuit_name,
                'event_date': event_date,
                'has_sprint': has_sprint
            })

            # Process each competition (session)
            for competition in competitions_data:
                comp_id = competition.get('id')
                comp_type = competition.get('type', {}).get('text', 'Unknown')
                comp_date = competition.get('date')
                session_num = competition.get('session', 1)

                sessions_data.append({
                    'espn_competition_id': comp_id,
                    'race_espn_event_id': event_id,
                    'session_type': comp_type,
                    'session_number': session_num,
                    'session_date': comp_date
                })

                # Process competitors (results)
                competitors = competition.get('competitors', [])

                for competitor in competitors:
                    # Get driver ID
                    athlete_ref = competitor.get('athlete', {}).get('$ref', '')
                    if not athlete_ref:
                        continue

                    driver_id = athlete_ref.split('/')[-1].split('?')[0]

                    # Get team from vehicle manufacturer
                    team_id = None
                    vehicle = competitor.get('vehicle', {})
                    team_name = vehicle.get('manufacturer')

                    if team_name:
                        team_id = team_name.replace(' ', '_').lower()
                        teams_data.add((team_id, team_name))

                    # Position and status
                    position = competitor.get('order')
                    start_position = competitor.get('startOrder')
                    winner = 1 if competitor.get('winner') else 0

                    # Get statistics URL
                    stats_url = None
                    if competitor.get('statistics'):
                        stats_url = competitor['statistics'].get('$ref')

                    results_data.append({
                        'session_espn_competition_id': comp_id,
                        'driver_id': driver_id,
                        'team_id': team_id,
                        'position': position,
                        'grid_position': start_position,
                        'winner': winner,
                        'espn_statistics_url': stats_url
                    })

            time.sleep(0.05)  # Small delay between events

        logger.info(f"[{year}] ✓ Fetched {len(races_data)} races, {len(sessions_data)} sessions, {len(results_data)} results")
        return {
            'year': year,
            'races': races_data,
            'sessions': sessions_data,
            'results': results_data,
            'teams': list(teams_data)
        }

    except Exception as e:
        logger.error(f"[{year}] ✗ Error: {e}")
        return None


def write_to_db(data, conn):
    """Write data to database with a single connection."""
    if not data:
        return

    year = data['year']
    cursor = conn.cursor()

    try:
        # Insert teams
        for team_id, team_name in data['teams']:
            cursor.execute("""
                INSERT OR IGNORE INTO teams
                (id, name, display_name, updated_at)
                VALUES (?, ?, ?, ?)
            """, (team_id, team_name, team_name, datetime.now()))

        # Insert races
        for race in data['races']:
            cursor.execute("""
                INSERT OR REPLACE INTO races
                (espn_event_id, year, round_number, event_name, official_event_name, country, location,
                 circuit_name, event_date, has_sprint, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                race['espn_event_id'], race['year'], race['round_number'], race['event_name'],
                race['official_event_name'], race['country'], race['location'], race['circuit_name'],
                race['event_date'], race['has_sprint'], datetime.now()
            ))

        # Insert sessions
        for session in data['sessions']:
            cursor.execute("""
                INSERT OR REPLACE INTO race_sessions
                (espn_competition_id, race_espn_event_id, session_type, session_number, session_date, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session['espn_competition_id'], session['race_espn_event_id'], session['session_type'],
                session['session_number'], session['session_date'], datetime.now()
            ))

        # Insert results
        for result in data['results']:
            cursor.execute("""
                INSERT OR REPLACE INTO session_results
                (session_espn_competition_id, driver_id, team_id, position, grid_position, winner,
                 espn_statistics_url, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                result['session_espn_competition_id'], result['driver_id'], result['team_id'],
                result['position'], result['grid_position'], result['winner'],
                result['espn_statistics_url'], datetime.now()
            ))

        conn.commit()
        logger.info(f"[{year}] ✓ Saved to database")

    except Exception as e:
        logger.error(f"[{year}] ✗ Database error: {e}")
        conn.rollback()


def populate_all_races(db_path: str = "f1_data.db", start_year: int = 1950, end_year: int = 2024, max_workers: int = 10):
    """Populate races for all years using multithreading."""

    # Get all years from seasons table
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT year FROM seasons WHERE year BETWEEN ? AND ? ORDER BY year", (start_year, end_year))
    years = [row[0] for row in cursor.fetchall()]

    logger.info(f"Processing {len(years)} seasons from {start_year}-{end_year} with {max_workers} workers")

    # Fetch data using thread pool
    results = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_year = {executor.submit(fetch_year_data, year): year for year in years}

        for future in as_completed(future_to_year):
            year = future_to_year[future]
            try:
                data = future.result()
                if data:
                    results.append(data)
            except Exception as e:
                logger.error(f"[{year}] Exception: {e}")

    # Sort results by year
    results.sort(key=lambda x: x['year'])

    # Write all results to database sequentially
    logger.info("Writing all data to database...")
    for data in results:
        write_to_db(data, conn)

    conn.close()

    logger.info(f"\n{'='*60}")
    logger.info(f"✓ Complete! Processed {len(results)} seasons successfully")
    logger.info(f"{'='*60}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Populate races for all seasons')
    parser.add_argument('--start-year', type=int, default=1950, help='Start year')
    parser.add_argument('--end-year', type=int, default=2024, help='End year')
    parser.add_argument('--max-workers', type=int, default=10, help='Number of concurrent workers')
    parser.add_argument('--db-path', type=str, default='f1_data.db', help='Database path')

    args = parser.parse_args()

    populate_all_races(args.db_path, args.start_year, args.end_year, args.max_workers)
