#!/usr/bin/env python3
"""Populate races, race_sessions, and session_results from ESPN API."""

import sys
import requests
from pathlib import Path
from datetime import datetime
import time

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f1_webapp.db.database import get_db_connection

def populate_races(db_path: str = "f1_data.db", year: int = 2024):
    """Populate races and session results for a given year.

    Args:
        db_path: Path to database
        year: Season year to populate
    """

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Get events for the year
    events_url = f"http://sports.core.api.espn.com/v2/sports/racing/leagues/f1/events/?dates={year}&limit=100"
    print(f"\nFetching events for {year}...")
    response = requests.get(events_url)
    events_data = response.json()

    event_count = events_data.get('count', 0)
    print(f"Found {event_count} race weekends")

    races_added = 0
    sessions_added = 0
    results_added = 0

    for idx, event_item in enumerate(events_data.get('items', []), 1):
        event_url = event_item.get('$ref', '')

        # Fetch individual event
        print(f"\n[{idx}/{event_count}] Fetching event...")
        event_response = requests.get(event_url)
        event = event_response.json()

        event_id = event.get('id')
        event_name = event.get('name', 'Unknown')
        official_event_name = event.get('shortName', event_name)
        event_date = event.get('date')

        # Get venue details for location/country
        country = None
        location = None
        circuit_name = None

        if event.get('venues'):
            venue_ref = event['venues'][0].get('$ref')
            if venue_ref:
                try:
                    venue_response = requests.get(venue_ref)
                    venue = venue_response.json()
                    circuit_name = venue.get('fullName')
                    if venue.get('address'):
                        location = venue['address'].get('city')
                        country = venue['address'].get('country')
                except Exception as e:
                    print(f"    Warning: Could not fetch venue: {e}")

        print(f"  {event_name}")

        # Fetch all competitions and detect sprint weekend
        has_sprint = 0
        competitions_data = []

        for comp_item in event.get('competitions', []):
            comp_response = requests.get(comp_item.get('$ref', ''))
            comp = comp_response.json()
            competitions_data.append(comp)

            comp_type = comp.get('type', {}).get('text', '')
            if 'Sprint' in comp_type:
                has_sprint = 1

        # Insert race (event-level data only)
        cursor.execute("""
            INSERT OR REPLACE INTO races
            (espn_event_id, year, round_number, event_name, official_event_name, country, location,
             circuit_name, event_date, has_sprint, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event_id, year, idx, event_name, official_event_name, country, location,
            circuit_name, event_date, has_sprint, datetime.now()
        ))

        # Use the espn_event_id as the race identifier
        race_espn_event_id = event_id
        races_added += 1

        # Process each competition (session)
        print(f"  Processing {len(competitions_data)} sessions...")

        for competition in competitions_data:

            comp_id = competition.get('id')
            comp_type = competition.get('type', {}).get('text', 'Unknown')
            comp_date = competition.get('date')
            session_num = competition.get('session', 1)

            # Insert session
            cursor.execute("""
                INSERT OR REPLACE INTO race_sessions
                (espn_competition_id, race_espn_event_id, session_type, session_number, session_date, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                comp_id, race_espn_event_id, comp_type, session_num, comp_date, datetime.now()
            ))

            # Use the espn_competition_id as the session identifier
            session_espn_competition_id = comp_id
            sessions_added += 1

            # Process competitors (results)
            competitors = competition.get('competitors', [])
            print(f"    {comp_type}: {len(competitors)} competitors")

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

                    # Insert team if not exists
                    cursor.execute("""
                        INSERT OR IGNORE INTO teams
                        (id, name, display_name, updated_at)
                        VALUES (?, ?, ?, ?)
                    """, (team_id, team_name, team_name, datetime.now()))

                # Position and status
                position = competitor.get('order')
                start_position = competitor.get('startOrder')
                winner = 1 if competitor.get('winner') else 0

                # Get statistics URL for detailed data
                stats_url = None
                if competitor.get('statistics'):
                    stats_url = competitor['statistics'].get('$ref')

                # Insert session result
                cursor.execute("""
                    INSERT OR REPLACE INTO session_results
                    (session_espn_competition_id, driver_id, team_id, position, grid_position, winner,
                     espn_statistics_url, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    session_espn_competition_id, driver_id, team_id, position, start_position,
                    winner, stats_url, datetime.now()
                ))
                results_added += 1

            # Small delay to avoid overwhelming API
            time.sleep(0.05)

        conn.commit()
        print(f"  ✓ Saved {event_name}")

    conn.close()

    print(f"\n{'='*60}")
    print(f"✓ Successfully processed {year}!")
    print(f"  Races added: {races_added}")
    print(f"  Sessions added: {sessions_added}")
    print(f"  Results added: {results_added}")
    print(f"{'='*60}")

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Populate races and results from ESPN API')
    parser.add_argument('--year', type=int, default=2024, help='Season year to populate')
    parser.add_argument('--db-path', type=str, default='f1_data.db', help='Database path')

    args = parser.parse_args()

    populate_races(args.db_path, args.year)
