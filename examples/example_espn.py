"""Example: Using ESPN F1 API client."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f1_webapp.espn.client import ESPNClient


def main():
    """Demonstrate ESPN F1 API usage."""
    print("=" * 60)
    print("ESPN F1 API Example")
    print("=" * 60)

    # Initialize client
    client = ESPNClient()

    # Get current season
    current_season = client.get_current_season()
    print(f"\n📅 Current Season: {current_season}")

    # Get driver standings
    print(f"\n🏆 {current_season} Driver Standings (Top 10):")
    print("-" * 60)

    standings = client.get_driver_standings(current_season)

    # Parse standings
    for entry in standings.get("standings", [{}])[0].get("standings", [])[:10]:
        records = entry.get("records", [{}])[0]
        stats = {s["name"]: s for s in records.get("stats", [])}

        position = int(stats.get("rank", {}).get("value", 0))
        points = stats.get("championshipPts", {}).get("value", 0)
        wins = int(stats.get("wins", {}).get("value", 0))

        # Get driver reference (would need another call to get name)
        driver_ref = entry.get("athlete", {}).get("$ref", "")
        driver_id = driver_ref.split("/")[-1] if driver_ref else "Unknown"

        print(f"{position:2d}. Driver ID {driver_id:6s} - {points:3.0f} pts ({wins} wins)")

    # Get a specific driver (Max Verstappen)
    print("\n👤 Driver Profile: Max Verstappen")
    print("-" * 60)

    driver = client.get_driver("4665")
    print(f"Name: {driver.get('fullName')}")
    print(f"Abbreviation: {driver.get('abbreviation')}")
    print(f"Number: {driver.get('vehicles', [{}])[0].get('number', 'N/A')}")
    print(f"Team: {driver.get('vehicles', [{}])[0].get('team', 'N/A')}")
    print(f"Nationality: {driver.get('flag', {}).get('alt', 'N/A')}")

    # Get recent events
    print("\n📍 Recent F1 Events:")
    print("-" * 60)

    events = client.get_events()
    for event_ref in events.get("items", [])[:3]:
        event_url = event_ref.get("$ref", "")
        event_id = event_url.split("/")[-1]

        # Fetch event details
        event = client.get_event(event_id)
        print(f"• {event.get('name', 'Unknown')} - {event.get('date', 'TBD')}")

    print("\n✅ Example completed successfully!")


if __name__ == "__main__":
    main()
