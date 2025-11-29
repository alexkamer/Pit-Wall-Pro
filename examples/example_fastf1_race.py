"""Example: Using FastF1 library wrapper."""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from f1_webapp.fastf1.client import FastF1Client


def main():
    """Demonstrate FastF1 usage."""
    print("=" * 60)
    print("FastF1 Library Example")
    print("=" * 60)

    # Initialize client with cache
    cache_dir = Path(__file__).parent.parent / "f1_cache"
    client = FastF1Client(cache_dir=str(cache_dir))

    # Get 2024 season schedule
    print("\n📅 2024 Season Schedule (First 5 races):")
    print("-" * 60)

    schedule = client.get_event_schedule(2024)
    for _, race in schedule.head(5).iterrows():
        print(f"Round {race['RoundNumber']:2d}: {race['EventName']:<30s} {race['EventDate']}")

    # Load a session (Monaco 2024 Qualifying)
    print("\n🏎️  Loading Monaco 2024 Qualifying...")
    print("-" * 60)

    session = client.load_session(
        2024, "Monaco", "Q",
        telemetry=True,
        weather=False,
        messages=False
    )

    print(f"✓ Session loaded: {session.name}")
    print(f"✓ Date: {session.date}")
    print(f"✓ Drivers: {len(session.drivers)}")

    # Get fastest lap overall
    print("\n⚡ Fastest Lap:")
    print("-" * 60)

    fastest = client.get_fastest_lap(session)
    print(f"Driver: {fastest['Driver']}")
    print(f"Team: {fastest['Team']}")
    print(f"Lap Time: {fastest['LapTime']}")
    print(f"Compound: {fastest['Compound']}")
    print(f"Lap Number: {fastest['LapNumber']}")

    # Get telemetry for fastest lap
    print("\n📊 Telemetry Data (First 5 samples):")
    print("-" * 60)

    telemetry = client.get_lap_telemetry(fastest)
    print(telemetry[["Distance", "Speed", "Throttle", "Brake", "nGear"]].head())

    # Compare two drivers
    print("\n🆚 Comparing Verstappen vs Leclerc:")
    print("-" * 60)

    try:
        ver_fastest = client.get_fastest_lap(session, "VER")
        lec_fastest = client.get_fastest_lap(session, "LEC")

        delta = ver_fastest["LapTime"] - lec_fastest["LapTime"]

        print(f"VER: {ver_fastest['LapTime']}")
        print(f"LEC: {lec_fastest['LapTime']}")
        print(f"Delta: {delta} ({'VER faster' if delta < 0 else 'LEC faster'})")

    except Exception as e:
        print(f"⚠️  Could not compare: {e}")

    # Show session results
    print("\n🏁 Session Results (Top 10):")
    print("-" * 60)

    results = client.get_session_results(session)
    for _, driver in results.head(10).iterrows():
        q3_time = driver.get("Q3", "N/A")
        print(f"{driver['Position']:2.0f}. {driver['Abbreviation']:3s} - {driver['TeamName']:<20s} {q3_time}")

    print("\n✅ Example completed successfully!")
    print(f"💾 Data cached in: {cache_dir}")


if __name__ == "__main__":
    main()
