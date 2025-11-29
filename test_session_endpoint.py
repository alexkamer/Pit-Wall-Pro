"""Test script to verify session endpoint works with JSON serialization."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from f1_webapp.fastf1.client import FastF1Client
import pandas as pd
import numpy as np
import json


def dataframe_to_json_safe(df):
    """Convert DataFrame to JSON-safe dictionary, handling all pandas special types."""
    df = df.copy()

    # Convert all timedelta columns to strings
    for col in df.columns:
        if pd.api.types.is_timedelta64_dtype(df[col]):
            df[col] = df[col].apply(lambda x: str(x) if pd.notna(x) else None)
        elif pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].apply(lambda x: x.isoformat() if pd.notna(x) else None)

    # Replace all NaN, inf, -inf with None
    df = df.replace([np.inf, -np.inf], None)
    df = df.where(pd.notna(df), None)

    return df.to_dict(orient="records")


def test_session_endpoint():
    """Test that session data can be converted to JSON."""
    print("Testing FastF1 session endpoint JSON serialization...")
    print("=" * 60)

    # Initialize client
    client = FastF1Client(cache_dir="./f1_cache")

    # Load Monaco 2024 Qualifying
    print("\n1. Loading Monaco 2024 Qualifying session...")
    session = client.load_session(
        2024, "Monaco", "Q",
        telemetry=False,
        weather=False,
        messages=False
    )
    print("✓ Session loaded")

    # Create response structure
    print("\n2. Creating response structure...")
    response = {
        "name": session.name,
        "date": session.date.isoformat(),
        "event": {
            "EventName": session.event["EventName"],
            "EventDate": session.event["EventDate"].isoformat(),
            "Location": session.event["Location"],
            "Country": session.event["Country"],
            "RoundNumber": int(session.event["RoundNumber"]),
        },
        "results": dataframe_to_json_safe(session.results),
    }
    print("✓ Response structure created")

    # Try to serialize to JSON
    print("\n3. Testing JSON serialization...")
    try:
        json_str = json.dumps(response, indent=2)
        print("✓ JSON serialization successful!")
        print(f"\n   Response size: {len(json_str)} characters")
        print(f"   Number of drivers: {len(response['results'])}")

        # Show first driver result
        if response['results']:
            print("\n4. Sample result (first driver):")
            first_driver = response['results'][0]
            print(f"   Position: {first_driver.get('Position')}")
            print(f"   Abbreviation: {first_driver.get('Abbreviation')}")
            print(f"   Q1: {first_driver.get('Q1')}")
            print(f"   Q2: {first_driver.get('Q2')}")
            print(f"   Q3: {first_driver.get('Q3')}")

        print("\n" + "=" * 60)
        print("✅ TEST PASSED - Session endpoint will work!")
        return True

    except Exception as e:
        print(f"✗ JSON serialization failed: {e}")
        print("\n" + "=" * 60)
        print("❌ TEST FAILED")
        return False


if __name__ == "__main__":
    success = test_session_endpoint()
    sys.exit(0 if success else 1)
