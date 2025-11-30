#!/usr/bin/env python3
"""Populate seasons table from ESPN API."""

import sys
import requests
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f1_webapp.db.database import get_db_connection

def populate_seasons(db_path: str = "f1_data.db"):
    """Populate all F1 seasons from ESPN API."""

    # Get all seasons
    url = "http://sports.core.api.espn.com/v2/sports/racing/leagues/f1/seasons?limit=500"
    response = requests.get(url)
    data = response.json()

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    print(f"Found {data['count']} seasons")

    seasons_added = 0
    for item in data.get('items', []):
        season_url = item.get('$ref', '')

        # Fetch individual season data
        season_response = requests.get(season_url)
        season = season_response.json()

        year = season.get('year')
        start_date = season.get('startDate')
        end_date = season.get('endDate')
        display_name = season.get('displayName')

        # Get type information
        season_type = season.get('type', {})
        season_type_id = season_type.get('id')
        season_type_name = season_type.get('name')
        has_standings = 1 if season_type.get('hasStandings') else 0

        # Get URLs
        standings_ref = season_type.get('standings', {})
        standings_url = standings_ref.get('$ref') if standings_ref else None

        athletes_ref = season.get('athletes', {})
        athletes_url = athletes_ref.get('$ref') if athletes_ref else None

        # Insert into database
        cursor.execute("""
            INSERT OR REPLACE INTO seasons
            (year, start_date, end_date, display_name, season_type_id,
             season_type_name, has_standings, standings_url, athletes_url, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            year, start_date, end_date, display_name, season_type_id,
            season_type_name, has_standings, standings_url, athletes_url,
            datetime.now()
        ))

        seasons_added += 1
        print(f"Added: {year} - {display_name}")

    conn.commit()
    conn.close()

    print(f"\n✓ Successfully added {seasons_added} seasons!")

if __name__ == '__main__':
    populate_seasons()
