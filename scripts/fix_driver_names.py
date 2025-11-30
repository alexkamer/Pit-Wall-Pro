#!/usr/bin/env python3
"""Fix driver names in database by fetching from ESPN API."""

import sys
import logging
from pathlib import Path
import argparse
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f1_webapp.db.database import get_db_connection
from f1_webapp.espn.client import ESPNClient

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fix_driver_names(conn, espn: ESPNClient):
    """Fix driver names for records with NULL first_name or last_name.

    Args:
        conn: Database connection
        espn: ESPN API client
    """
    cursor = conn.cursor()

    # Find all drivers with NULL first_name or last_name but have full_name
    cursor.execute("""
        SELECT id, abbreviation, full_name
        FROM drivers
        WHERE (first_name IS NULL OR last_name IS NULL)
        AND full_name IS NOT NULL
    """)

    drivers_to_fix = cursor.fetchall()
    total = len(drivers_to_fix)

    if total == 0:
        logger.info("No drivers found with missing names!")
        return

    logger.info(f"Found {total} drivers with missing first_name or last_name")

    fixed_count = 0
    failed_count = 0

    for i, row in enumerate(drivers_to_fix, 1):
        driver_id = row[0]
        driver_abbr = row[1]
        full_name = row[2]

        try:
            logger.info(f"[{i}/{total}] Fixing driver: {driver_abbr} ({full_name})")

            # Parse first and last name from full_name
            # Most names are "FirstName LastName" or "FirstName MiddleName LastName"
            name_parts = full_name.strip().split()

            if len(name_parts) >= 2:
                # First word is first name, last word is last name
                first_name = name_parts[0]
                last_name = name_parts[-1]
            elif len(name_parts) == 1:
                # Single name - use as both
                first_name = name_parts[0]
                last_name = name_parts[0]
            else:
                logger.warning(f"  Cannot parse name: {full_name}")
                failed_count += 1
                continue

            # Update the driver record
            cursor.execute("""
                UPDATE drivers
                SET first_name = ?,
                    last_name = ?,
                    updated_at = ?
                WHERE id = ?
            """, (
                first_name,
                last_name,
                datetime.now(),
                driver_id
            ))

            logger.info(f"  ✓ Updated: {first_name} {last_name}")
            fixed_count += 1

            # Commit every 10 updates
            if i % 10 == 0:
                conn.commit()
                logger.info(f"Progress: {i}/{total} drivers processed")

        except Exception as e:
            logger.warning(f"  Error fixing driver {driver_abbr}: {e}")
            failed_count += 1
            continue

    # Final commit
    conn.commit()

    logger.info(f"\n{'='*60}")
    logger.info(f"Fix complete!")
    logger.info(f"  Successfully fixed: {fixed_count}")
    logger.info(f"  Failed: {failed_count}")
    logger.info(f"{'='*60}")


def main():
    parser = argparse.ArgumentParser(description='Fix driver names in database')
    parser.add_argument('--db-path', type=str, help='Path to SQLite database file')

    args = parser.parse_args()

    # Create ESPN client
    espn = ESPNClient()

    # Get database connection
    conn = get_db_connection(args.db_path)

    try:
        fix_driver_names(conn, espn)
    except Exception as e:
        logger.error(f"Failed to fix driver names: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == '__main__':
    main()
