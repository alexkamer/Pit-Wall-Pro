"""Backfill race positions from Ergast API to fix classified DNF data."""

import sqlite3
import sys
import time
from pathlib import Path
from fastf1.ergast import Ergast

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

def backfill_positions():
    """Backfill missing classified DNF positions from Ergast API."""

    # Connect to database
    db_path = Path(__file__).parent.parent / 'f1_data.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Initialize Ergast client
    ergast = Ergast()

    # Get all races with session results that have NULL positions
    cursor.execute("""
        SELECT DISTINCT
            r.year,
            r.round_number,
            r.event_name,
            r.country
        FROM races r
        JOIN race_sessions rs ON r.espn_event_id = rs.race_espn_event_id
        JOIN session_results sr ON rs.espn_competition_id = sr.session_espn_competition_id
        WHERE sr.position IS NULL
        AND rs.session_type = 'Race'
        AND r.year >= 1950
        ORDER BY r.year, r.round_number
    """)

    races_to_fix = cursor.fetchall()
    print(f"Found {len(races_to_fix)} races with NULL positions to backfill")

    updates_made = 0

    for race_row in races_to_fix:
        year = race_row['year']
        round_num = race_row['round_number']
        event_name = race_row['event_name']

        print(f"\nProcessing {year} Round {round_num}: {event_name}")

        try:
            # Add delay to respect rate limits (200ms between requests)
            time.sleep(0.2)

            # Get results from Ergast
            results = ergast.get_race_results(season=year, round=round_num)
            if not results.content or len(results.content) == 0:
                print(f"  ⚠️  No results from Ergast")
                continue

            df = results.content[0]

            # Get session ID for this race
            cursor.execute("""
                SELECT rs.espn_competition_id
                FROM race_sessions rs
                JOIN races r ON rs.race_espn_event_id = r.espn_event_id
                WHERE r.year = ? AND r.round_number = ?
                AND rs.session_type = 'Race'
            """, (year, round_num))

            session_row = cursor.fetchone()
            if not session_row:
                print(f"  ⚠️  No session found in database")
                continue

            session_id = session_row['espn_competition_id']

            # For each driver in Ergast results
            for _, row in df.iterrows():
                driver_id = row['driverId']
                position = row['position']

                # Skip if no position (shouldn't happen but just in case)
                if position is None or str(position) == 'nan':
                    continue

                # Try to find this driver in our database by matching various IDs
                # Ergast uses different driver IDs, so we need to match by name
                full_name = f"{row['givenName']} {row['familyName']}"

                # Try to find driver in our database
                cursor.execute("""
                    SELECT id FROM drivers
                    WHERE display_name = ? OR first_name || ' ' || last_name = ?
                    LIMIT 1
                """, (full_name, full_name))

                driver_row = cursor.fetchone()
                if not driver_row:
                    # Try alternative matching by last name only
                    cursor.execute("""
                        SELECT id FROM drivers
                        WHERE last_name = ?
                        LIMIT 1
                    """, (row['familyName'],))
                    driver_row = cursor.fetchone()

                if not driver_row:
                    print(f"  ⚠️  Driver not found: {full_name}")
                    continue

                our_driver_id = driver_row['id']

                # Update position in session_results if currently NULL
                cursor.execute("""
                    UPDATE session_results
                    SET position = ?
                    WHERE session_espn_competition_id = ?
                    AND driver_id = ?
                    AND position IS NULL
                """, (int(position), session_id, our_driver_id))

                if cursor.rowcount > 0:
                    updates_made += 1
                    print(f"  ✓ Updated {full_name}: P{position}")

            # Commit after each race
            conn.commit()

        except Exception as e:
            print(f"  ❌ Error processing race: {e}")
            continue

    print(f"\n{'='*60}")
    print(f"Backfill complete!")
    print(f"Updated {updates_made} driver positions")
    print(f"{'='*60}")

    conn.close()

if __name__ == "__main__":
    backfill_positions()
