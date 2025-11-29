"""Quick start example combining both APIs."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f1_webapp.espn.client import ESPNClient
from f1_webapp.fastf1.client import FastF1Client


def main():
    """Quick demonstration of both APIs."""
    print("🏎️  F1 Data API - Quick Start")
    print("=" * 60)

    # Initialize both clients
    espn = ESPNClient()
    ff1 = FastF1Client(cache_dir="./f1_cache")

    print("\n1️⃣  ESPN API: Get Current Championship Leader")
    print("-" * 60)

    try:
        standings = espn.get_driver_standings(2024)
        leader_entry = standings["standings"][0]["standings"][0]
        stats = {s["name"]: s["value"] for s in leader_entry["records"][0]["stats"]}

        driver_id = leader_entry["athlete"]["$ref"].split("/")[-1]
        driver = espn.get_driver(driver_id)

        print(f"🏆 Leader: {driver['fullName']}")
        print(f"   Points: {stats.get('championshipPts', 0):.0f}")
        print(f"   Wins: {stats.get('wins', 0):.0f}")
        print(f"   Team: {driver['vehicles'][0]['team']}")

    except Exception as e:
        print(f"⚠️  Error: {e}")

    print("\n2️⃣  FastF1: Analyze Latest Qualifying")
    print("-" * 60)

    try:
        # Get 2024 schedule
        schedule = ff1.get_event_schedule(2024)

        # Find most recent completed race (or use a known one)
        # For demo, let's use Monaco
        print("Loading Monaco 2024 Qualifying...")

        session = ff1.load_session(
            2024, "Monaco", "Q",
            telemetry=False,
            weather=False,
            messages=False
        )

        fastest = ff1.get_fastest_lap(session)

        print(f"⚡ Fastest Lap: {fastest['Driver']}")
        print(f"   Time: {fastest['LapTime']}")
        print(f"   Compound: {fastest['Compound']}")

        # Show top 3
        print("\n   Top 3:")
        results = session.results.head(3)
        for idx, driver in results.iterrows():
            print(f"   {driver['Position']:.0f}. {driver['Abbreviation']} - {driver.get('Q3', 'N/A')}")

    except Exception as e:
        print(f"⚠️  Error: {e}")
        print("   Note: You may need an internet connection for FastF1 data")

    print("\n3️⃣  Combined: Driver Profile with Recent Performance")
    print("-" * 60)

    try:
        # Get driver from ESPN
        driver = espn.get_driver("4665")  # Verstappen
        print(f"👤 {driver['fullName']}")
        print(f"   Team: {driver['vehicles'][0]['team']}")
        print(f"   Number: {driver['vehicles'][0]['number']}")

        # Get their latest quali lap from FastF1
        session = ff1.load_session(2024, "Monaco", "Q", telemetry=False)
        ver_laps = ff1.get_driver_laps(session, "VER")

        if len(ver_laps) > 0:
            fastest_lap = ver_laps.pick_fastest()
            print(f"\n   Latest Quali Performance (Monaco):")
            print(f"   Fastest Lap: {fastest_lap['LapTime']}")
            print(f"   Lap Number: {fastest_lap['LapNumber']}")

    except Exception as e:
        print(f"⚠️  Error: {e}")

    print("\n" + "=" * 60)
    print("✅ Quick start complete!")
    print("\nNext steps:")
    print("  • Run examples/example_espn.py for ESPN API demo")
    print("  • Run examples/example_fastf1.py for FastF1 demo")
    print("  • Start API server: uv run uvicorn src.f1_webapp.api.app:app")
    print("  • Check API docs: http://localhost:8000/docs")


if __name__ == "__main__":
    main()
