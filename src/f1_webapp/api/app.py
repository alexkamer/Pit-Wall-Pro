"""FastAPI application combining ESPN and FastF1 APIs."""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional, Any
import logging
import pandas as pd
import numpy as np
import json

from ..espn.client import ESPNClient
from ..fastf1.client import FastF1Client

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NaNEncoder(json.JSONEncoder):
    """Custom JSON encoder that converts NaN/inf to None."""
    def default(self, obj):
        if isinstance(obj, float):
            if np.isnan(obj) or np.isinf(obj):
                return None
        return super().default(obj)


def json_safe(data: Any) -> Any:
    """Recursively convert NaN/inf values to None in nested structures."""
    if isinstance(data, dict):
        return {k: json_safe(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [json_safe(item) for item in data]
    elif isinstance(data, float):
        if np.isnan(data) or np.isinf(data):
            return None
        return data
    elif isinstance(data, pd.Timestamp):
        return data.isoformat()
    elif pd.isna(data):
        return None
    return data


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


def create_app(cache_dir: str = "./f1_cache") -> FastAPI:
    """Create and configure FastAPI application.

    Args:
        cache_dir: Directory for FastF1 cache

    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title="F1 Data API",
        description="Comprehensive F1 data API combining ESPN and FastF1",
        version="0.1.0",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize clients
    espn = ESPNClient()
    ff1 = FastF1Client(cache_dir=cache_dir)

    # ESPN Endpoints

    @app.get("/")
    def root():
        """Root endpoint."""
        return {
            "name": "F1 Data API",
            "version": "0.1.0",
            "endpoints": {
                "espn": {
                    "standings": "/espn/standings/{year}",
                    "driver": "/espn/drivers/{driver_id}",
                    "events": "/espn/events?season={year}&limit={limit}",
                },
                "fastf1": {
                    "session": "/fastf1/session/{year}/{gp}/{session_type}",
                    "fastest_lap": "/fastf1/fastest-lap/{year}/{gp}/{session_type}",
                    "telemetry": "/fastf1/telemetry/{year}/{gp}/{session_type}/{driver}",
                },
            },
        }

    @app.get("/espn/standings/{year}")
    def get_standings(year: int, type: str = "driver"):
        """Get championship standings.

        Args:
            year: Season year
            type: 'driver' or 'constructor'
        """
        try:
            if type == "driver":
                data = espn.get_driver_standings(year)
            elif type == "constructor":
                data = espn.get_constructor_standings(year)
            else:
                raise HTTPException(400, "Type must be 'driver' or 'constructor'")

            return data
        except Exception as e:
            logger.error(f"Error fetching standings: {e}")
            raise HTTPException(500, str(e))

    @app.get("/espn/drivers/{driver_id}")
    def get_driver(driver_id: str):
        """Get driver profile.

        Args:
            driver_id: ESPN driver ID (e.g., '4665')
        """
        try:
            return espn.get_driver(driver_id)
        except Exception as e:
            logger.error(f"Error fetching driver: {e}")
            raise HTTPException(404, f"Driver {driver_id} not found")

    @app.get("/espn/events")
    def get_events(season: Optional[int] = None, limit: int = 100):
        """Get F1 events.

        Args:
            season: Optional season year to get all events for that season
            limit: Maximum number of events to return (default: 100)
        """
        try:
            return espn.get_events(season=season, limit=limit)
        except Exception as e:
            logger.error(f"Error fetching events: {e}")
            raise HTTPException(500, str(e))

    @app.get("/espn/event/{event_id}")
    def get_event(event_id: str):
        """Get event details.

        Args:
            event_id: ESPN event ID
        """
        try:
            return espn.get_event(event_id)
        except Exception as e:
            logger.error(f"Error fetching event: {e}")
            raise HTTPException(404, f"Event {event_id} not found")

    # FastF1 Endpoints

    @app.get("/fastf1/schedule/{year}")
    def get_schedule(year: int):
        """Get season schedule.

        Args:
            year: Championship year
        """
        try:
            schedule = ff1.get_event_schedule(year)
            return dataframe_to_json_safe(schedule)
        except Exception as e:
            logger.error(f"Error fetching schedule: {e}")
            raise HTTPException(500, str(e))

    @app.get("/fastf1/session/{year}/{gp}/{session_type}")
    def get_session_info(year: int, gp: str, session_type: str):
        """Get session information and results.

        Args:
            year: Championship year
            gp: Grand Prix name or round number
            session_type: 'FP1', 'FP2', 'FP3', 'Q', 'S', 'R'
        """
        try:
            session = ff1.load_session(
                year, gp, session_type,
                telemetry=False,  # Don't load heavy telemetry
                weather=False,
                messages=False
            )

            data = {
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
            return json_safe(data)
        except Exception as e:
            logger.error(f"Error loading session: {e}")
            raise HTTPException(500, str(e))

    @app.get("/fastf1/fastest-lap/{year}/{gp}/{session_type}")
    def get_fastest_lap_info(
        year: int,
        gp: str,
        session_type: str,
        driver: Optional[str] = None
    ):
        """Get fastest lap information.

        Args:
            year: Championship year
            gp: Grand Prix name or round number
            session_type: Session type
            driver: Optional driver abbreviation filter
        """
        try:
            session = ff1.load_session(year, gp, session_type, telemetry=False)
            fastest = ff1.get_fastest_lap(session, driver)

            return {
                "driver": fastest["Driver"],
                "lap_time": str(fastest["LapTime"]),
                "lap_number": int(fastest["LapNumber"]),
                "compound": fastest["Compound"],
                "team": fastest["Team"],
            }
        except Exception as e:
            logger.error(f"Error getting fastest lap: {e}")
            raise HTTPException(500, str(e))

    @app.get("/fastf1/telemetry/{year}/{gp}/{session_type}/{driver}")
    def get_driver_telemetry(
        year: int,
        gp: str,
        session_type: str,
        driver: str,
        lap_type: str = "fastest"
    ):
        """Get driver telemetry for a lap.

        Args:
            year: Championship year
            gp: Grand Prix name
            session_type: Session type
            driver: Driver abbreviation (e.g., 'VER')
            lap_type: 'fastest' or lap number
        """
        try:
            session = ff1.load_session(year, gp, session_type)

            if lap_type == "fastest":
                lap = ff1.get_fastest_lap(session, driver)
            else:
                laps = ff1.get_driver_laps(session, driver)
                lap = laps[laps["LapNumber"] == int(lap_type)].iloc[0]

            telemetry = ff1.get_lap_telemetry(lap)

            return json_safe({
                "driver": driver,
                "lap_number": int(lap["LapNumber"]),
                "lap_time": str(lap["LapTime"]),
                "telemetry": {
                    "distance": telemetry["Distance"].tolist(),
                    "speed": telemetry["Speed"].tolist(),
                    "throttle": telemetry["Throttle"].tolist(),
                    "brake": telemetry["Brake"].tolist(),
                    "gear": telemetry["nGear"].tolist(),
                },
            })
        except Exception as e:
            logger.error(f"Error getting telemetry: {e}")
            raise HTTPException(500, str(e))

    @app.get("/fastf1/compare/{year}/{gp}/{session_type}")
    def compare_drivers(
        year: int,
        gp: str,
        session_type: str,
        driver1: str,
        driver2: str
    ):
        """Compare two drivers' fastest laps.

        Args:
            year: Championship year
            gp: Grand Prix name
            session_type: Session type
            driver1: First driver abbreviation
            driver2: Second driver abbreviation
        """
        try:
            session = ff1.load_session(year, gp, session_type)

            lap1 = ff1.get_fastest_lap(session, driver1)
            lap2 = ff1.get_fastest_lap(session, driver2)

            comparison = ff1.compare_laps(lap1, lap2)

            return json_safe({
                "driver1": {
                    "name": comparison["lap1"]["driver"],
                    "time": str(comparison["lap1"]["time"]),
                    "telemetry": {
                        "distance": comparison["lap1"]["telemetry"]["Distance"].tolist(),
                        "speed": comparison["lap1"]["telemetry"]["Speed"].tolist(),
                        "throttle": comparison["lap1"]["telemetry"]["Throttle"].tolist(),
                    },
                },
                "driver2": {
                    "name": comparison["lap2"]["driver"],
                    "time": str(comparison["lap2"]["time"]),
                    "telemetry": {
                        "distance": comparison["lap2"]["telemetry"]["Distance"].tolist(),
                        "speed": comparison["lap2"]["telemetry"]["Speed"].tolist(),
                        "throttle": comparison["lap2"]["telemetry"]["Throttle"].tolist(),
                    },
                },
            })
        except Exception as e:
            logger.error(f"Error comparing drivers: {e}")
            raise HTTPException(500, str(e))

    return app


# For running with uvicorn
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
