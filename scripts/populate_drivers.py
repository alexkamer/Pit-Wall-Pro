#!/usr/bin/env python3
"""Populate drivers table from ESPN API for all seasons."""

import sys
import requests
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f1_webapp.db.database import get_db_connection

def populate_drivers(db_path: str = "f1_data.db"):
    """Populate all F1 drivers from all seasons."""

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    # Get all seasons
    cursor.execute("SELECT year, athletes_url FROM seasons ORDER BY year DESC")
    seasons = cursor.fetchall()

    print(f"Processing {len(seasons)} seasons for driver data...")

    drivers_added = 0
    driver_seasons_added = 0

    for year, athletes_url in seasons:
        print(f"\nProcessing {year}...")

        # Add limit parameter to athletes URL
        if '?' in athletes_url:
            athletes_url_with_limit = f"{athletes_url}&limit=500"
        else:
            athletes_url_with_limit = f"{athletes_url}?limit=500"

        # Get list of athletes for this season
        response = requests.get(athletes_url_with_limit)
        athletes_data = response.json()

        athlete_count = athletes_data.get('count', 0)
        print(f"  Found {athlete_count} drivers")

        for item in athletes_data.get('items', []):
            athlete_url = item.get('$ref', '')

            # Fetch individual athlete data
            athlete_response = requests.get(athlete_url)
            athlete = athlete_response.json()

            driver_id = athlete.get('id')
            abbreviation = athlete.get('abbreviation', driver_id)
            first_name = athlete.get('firstName')
            last_name = athlete.get('lastName')
            full_name = athlete.get('fullName')
            display_name = athlete.get('displayName')
            short_name = athlete.get('shortName')
            date_of_birth = athlete.get('dateOfBirth')

            # Birth place
            birth_place = None
            if athlete.get('birthPlace'):
                birth_place = athlete['birthPlace'].get('city')

            # Headshot URL
            headshot_url = None
            if athlete.get('headshot'):
                headshot_url = athlete['headshot'].get('href')

            # Flag URL and nationality
            flag_url = None
            nationality = None
            if athlete.get('flag'):
                flag_url = athlete['flag'].get('href')
                nationality = athlete['flag'].get('alt')

            # Active status
            active = 1 if athlete.get('active') else 0

            # Status
            status = None
            if athlete.get('status'):
                status = athlete['status'].get('name')

            # Insert or update driver
            cursor.execute("""
                INSERT OR REPLACE INTO drivers
                (id, abbreviation, first_name, last_name, full_name, display_name,
                 short_name, date_of_birth, birth_place, headshot_url, flag_url,
                 nationality, active, status, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                driver_id, abbreviation, first_name, last_name, full_name, display_name,
                short_name, date_of_birth, birth_place, headshot_url, flag_url,
                nationality, active, status, datetime.now()
            ))

            # Track which season this driver participated in
            cursor.execute("""
                INSERT OR IGNORE INTO driver_seasons (driver_id, year)
                VALUES (?, ?)
            """, (driver_id, year))

            if cursor.rowcount > 0:
                driver_seasons_added += 1

        conn.commit()

    # Count total unique drivers
    cursor.execute("SELECT COUNT(*) FROM drivers")
    total_drivers = cursor.fetchone()[0]

    conn.close()

    print(f"\n✓ Successfully processed all seasons!")
    print(f"  Total unique drivers: {total_drivers}")
    print(f"  Driver-season records: {driver_seasons_added}")

if __name__ == '__main__':
    populate_drivers()
