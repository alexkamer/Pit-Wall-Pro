#!/usr/bin/env python3
"""Populate team logos from ESPN constructor standings API."""

import sys
import logging
from pathlib import Path
from datetime import datetime
import requests

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f1_webapp.db.database import get_db_connection
from f1_webapp.espn.client import ESPNClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def populate_team_logos(db_path: str = "f1_data.db", start_year: int = 1950, end_year: int = 2025):
    """Populate team logos from ESPN constructor standings.

    Args:
        db_path: Path to SQLite database
        start_year: Start year
        end_year: End year
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()
    espn = ESPNClient()

    # Track teams we've updated
    updated_teams = set()

    logger.info(f"Fetching team logos from {start_year}-{end_year} constructor standings...")

    for year in range(start_year, end_year + 1):
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
                    logo_url = manufacturer.get('logos', [{}])[0].get('href') if manufacturer.get('logos') else None

                    # Only update if we have a logo URL and haven't updated this team yet
                    if logo_url and team_id not in updated_teams:
                        cursor.execute("""
                            UPDATE teams
                            SET logo_url = ?, updated_at = ?
                            WHERE id = ?
                        """, (logo_url, datetime.now(), team_id))

                        if cursor.rowcount > 0:
                            updated_teams.add(team_id)
                            logger.info(f"✓ Updated logo for {team_name}")

                except Exception as e:
                    logger.debug(f"Error processing manufacturer: {e}")

        except Exception as e:
            logger.debug(f"No constructor standings for {year}: {e}")

    conn.commit()
    conn.close()

    logger.info(f"\n{'='*60}")
    logger.info(f"✓ Complete! Updated logos for {len(updated_teams)} teams")
    logger.info(f"{'='*60}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Populate team logos from ESPN API')
    parser.add_argument('--db-path', type=str, default='f1_data.db', help='Database path')
    parser.add_argument('--start-year', type=int, default=1950, help='Start year')
    parser.add_argument('--end-year', type=int, default=2025, help='End year')

    args = parser.parse_args()

    populate_team_logos(args.db_path, args.start_year, args.end_year)
