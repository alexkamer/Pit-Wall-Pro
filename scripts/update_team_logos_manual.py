#!/usr/bin/env python3
"""Manually update team logos for 2024/2025 F1 teams."""

import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f1_webapp.db.database import get_db_connection

# Manual logo URLs for 2024/2025 F1 teams
TEAM_LOGOS = {
    'mclaren': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/racing/500/106892.png',
    'ferrari': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/racing/500/106921.png',
    'red_bull': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/racing/500/106842.png',
    'mercedes': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/racing/500/106777.png',
    'aston_martin': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/racing/500/106813.png',
    'alpine': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/racing/500/106855.png',
    'haas': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/racing/500/107023.png',
    'racing_bulls': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/racing/500/106811.png',
    'williams': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/racing/500/106863.png',
    'sauber': 'https://a.espncdn.com/combiner/i?img=/i/teamlogos/racing/500/107098.png',
}


def update_team_logos(db_path: str = "f1_data.db"):
    """Update team logos in database.

    Args:
        db_path: Path to SQLite database
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    updated = 0
    for team_id, logo_url in TEAM_LOGOS.items():
        cursor.execute("""
            UPDATE teams
            SET logo_url = ?, updated_at = ?
            WHERE id = ?
        """, (logo_url, datetime.now(), team_id))

        if cursor.rowcount > 0:
            updated += 1
            print(f"✓ Updated logo for {team_id}")
        else:
            print(f"⚠ Team {team_id} not found in database")

    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print(f"✓ Complete! Updated logos for {updated}/{len(TEAM_LOGOS)} teams")
    print(f"{'='*60}")


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Update team logos manually')
    parser.add_argument('--db-path', type=str, default='f1_data.db', help='Database path')

    args = parser.parse_args()

    update_team_logos(args.db_path)
