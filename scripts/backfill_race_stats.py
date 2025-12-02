#!/usr/bin/env python3
"""Backfill race statistics (laps_completed, status) from ESPN API."""

import sqlite3
import sys
import time
import requests
from pathlib import Path
from datetime import datetime
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def fetch_statistics(stats_url: str) -> dict:
    """Fetch statistics from ESPN API URL."""
    try:
        response = requests.get(stats_url, timeout=10)
        if response.status_code != 200:
            return {}

        data = response.json()
        splits = data.get('splits', {})
        categories = splits.get('categories', [])

        if not categories:
            return {}

        stats_list = categories[0].get('stats', [])

        # Extract relevant statistics
        stats = {}
        for stat in stats_list:
            name = stat.get('name')
            value = stat.get('value')

            if name == 'lapsCompleted':
                stats['laps_completed'] = int(value) if value else None
            elif name == 'lapsBehind':
                stats['laps_behind'] = int(value) if value else None
            elif name == 'finishPos':
                stats['finish_position'] = int(value) if value else None

        return stats

    except Exception as e:
        logger.debug(f"Error fetching statistics: {e}")
        return {}


def determine_status(position: int, laps_completed: int, total_laps: int, laps_behind: int) -> str:
    """Determine race status based on position and laps."""

    # If they completed all laps or within reasonable distance, they finished
    if laps_behind is not None and laps_behind <= 1:
        return 'Finished'

    # If laps completed is very close to total (within 1), they finished
    if laps_completed and total_laps and abs(laps_completed - total_laps) <= 1:
        return 'Finished'

    # If they're way behind, they likely DNF'd
    if laps_behind and laps_behind > 5:
        return 'DNF'

    # If they completed significantly fewer laps, DNF
    if laps_completed and total_laps and laps_completed < (total_laps - 5):
        return 'DNF'

    # Default to Finished if they have a position
    if position:
        return 'Finished'

    return 'Unknown'


def backfill_statistics():
    """Backfill laps_completed and status from ESPN statistics API."""

    # Connect to database
    db_path = Path(__file__).parent.parent / 'f1_data.db'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all race session results that have a statistics URL but NULL laps_completed
    cursor.execute("""
        SELECT
            sr.id,
            sr.session_espn_competition_id,
            sr.driver_id,
            sr.position,
            sr.espn_statistics_url,
            sr.laps_completed,
            sr.status,
            r.year,
            r.round_number,
            r.event_name,
            d.display_name as driver_name
        FROM session_results sr
        JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
        JOIN races r ON rs.race_espn_event_id = r.espn_event_id
        JOIN drivers d ON sr.driver_id = d.id
        WHERE rs.session_type = 'Race'
        AND sr.espn_statistics_url IS NOT NULL
        AND sr.laps_completed IS NULL
        ORDER BY r.year DESC, r.round_number DESC
    """)

    results_to_update = cursor.fetchall()
    logger.info(f"Found {len(results_to_update)} results to backfill")

    updates_made = 0
    errors = 0

    # Track total laps per race for status determination
    race_total_laps = {}

    for idx, row in enumerate(results_to_update, 1):
        result_id = row['id']
        stats_url = row['espn_statistics_url']
        driver_name = row['driver_name']
        year = row['year']
        round_num = row['round_number']
        event_name = row['event_name']
        position = row['position']
        session_id = row['session_espn_competition_id']

        # Rate limiting
        if idx % 10 == 0:
            logger.info(f"Progress: {idx}/{len(results_to_update)} ({100*idx//len(results_to_update)}%)")
            time.sleep(0.5)
        else:
            time.sleep(0.1)

        try:
            # Fetch statistics
            stats = fetch_statistics(stats_url)

            if not stats:
                logger.debug(f"  [{year} R{round_num}] No stats for {driver_name}")
                continue

            laps_completed = stats.get('laps_completed')
            laps_behind = stats.get('laps_behind')

            # Track max laps for this race to determine total laps
            if session_id not in race_total_laps:
                race_total_laps[session_id] = 0

            if laps_completed:
                race_total_laps[session_id] = max(race_total_laps[session_id], laps_completed)

            # Determine status
            total_laps = race_total_laps.get(session_id, 0)
            status = determine_status(position, laps_completed, total_laps, laps_behind)

            # Update database
            cursor.execute("""
                UPDATE session_results
                SET laps_completed = ?,
                    status = ?,
                    updated_at = ?
                WHERE id = ?
            """, (laps_completed, status, datetime.now(), result_id))

            updates_made += 1

            if idx % 50 == 0:
                conn.commit()
                logger.info(f"  ✓ Committed {updates_made} updates")

        except Exception as e:
            logger.error(f"  [{year} R{round_num}] Error for {driver_name}: {e}")
            errors += 1
            continue

    # Second pass: Update statuses based on actual total laps
    logger.info("\nSecond pass: Refining statuses based on race totals...")

    cursor.execute("""
        SELECT
            sr.id,
            sr.session_espn_competition_id,
            sr.position,
            sr.laps_completed,
            sr.status
        FROM session_results sr
        JOIN race_sessions rs ON sr.session_espn_competition_id = rs.espn_competition_id
        WHERE rs.session_type = 'Race'
        AND sr.laps_completed IS NOT NULL
    """)

    all_results = cursor.fetchall()

    for row in all_results:
        result_id = row['id']
        session_id = row['session_espn_competition_id']
        position = row['position']
        laps_completed = row['laps_completed']
        current_status = row['status']

        total_laps = race_total_laps.get(session_id, 0)

        if total_laps == 0:
            continue

        # Recalculate status with accurate total laps
        new_status = determine_status(position, laps_completed, total_laps,
                                     total_laps - laps_completed if laps_completed else None)

        if new_status != current_status:
            cursor.execute("""
                UPDATE session_results
                SET status = ?,
                    updated_at = ?
                WHERE id = ?
            """, (new_status, datetime.now(), result_id))

    # Final commit
    conn.commit()
    conn.close()

    logger.info(f"\n{'='*60}")
    logger.info(f"Backfill complete!")
    logger.info(f"Updated: {updates_made} results")
    logger.info(f"Errors: {errors}")
    logger.info(f"{'='*60}")


if __name__ == "__main__":
    backfill_statistics()
