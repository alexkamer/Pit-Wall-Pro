from fastapi import APIRouter, HTTPException, Query
from ..services.fastf1_service import fastf1_service
from ..services.cache_service import cache_service

router = APIRouter()


@router.get("/session/{year}/{race}/{session_type}/results")
async def get_session_results(
    year: int,
    race: str,
    session_type: str
):
    """
    Get session results (finishing order, times, etc.) with SQLite caching

    Args:
        year: Season year (e.g., 2024, 2025)
        race: Race name or round number (e.g., 'Monaco', 'Bahrain', 1, 2)
        session_type: Session type - FP1, FP2, FP3, Q, S, R
    """
    try:
        # Temporarily bypass cache due to DB permissions issue
        # TODO: Fix database permissions and re-enable caching
        results = fastf1_service.get_session_results(year, race, session_type)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch session results: {str(e)}")


@router.get("/session/{year}/{race}/{session_type}/laps")
async def get_lap_times(
    year: int,
    race: str,
    session_type: str,
    driver: str | None = Query(None, description="Driver abbreviation (e.g., VER, HAM)")
):
    """
    Get lap times for a session with SQLite caching

    Args:
        year: Season year
        race: Race name or round number
        session_type: Session type - FP1, FP2, FP3, Q, S, R
        driver: Optional driver abbreviation to filter
    """
    try:
        # Try to get from cache first
        cached_laps = cache_service.get_lap_times(year, race, session_type, driver)
        if cached_laps:
            return cached_laps

        # If not in cache, fetch from FastF1
        laps = fastf1_service.get_lap_times(year, race, session_type, driver)

        # Store in cache
        cache_service.set_lap_times(year, race, session_type, laps)

        return laps
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch lap times: {str(e)}")


@router.get("/session/{year}/{race}/{session_type}/fastest")
async def get_fastest_lap(year: int, race: str, session_type: str):
    """
    Get the fastest lap of the session

    Args:
        year: Season year
        race: Race name or round number
        session_type: Session type - FP1, FP2, FP3, Q, S, R
    """
    try:
        fastest = fastf1_service.get_fastest_lap(year, race, session_type)
        return fastest
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch fastest lap: {str(e)}")


@router.get("/session/{year}/{race}/{session_type}/telemetry")
async def get_telemetry(
    year: int,
    race: str,
    session_type: str,
    driver: str = Query(..., description="Driver abbreviation (e.g., VER, HAM)"),
    lap: int = Query(..., description="Lap number")
):
    """
    Get telemetry data for a specific lap with SQLite caching

    Returns speed, RPM, gear, throttle, brake, and DRS data

    Args:
        year: Season year
        race: Race name or round number
        session_type: Session type - FP1, FP2, FP3, Q, S, R
        driver: Driver abbreviation
        lap: Lap number
    """
    try:
        # Try to get from cache first
        cached_telemetry = cache_service.get_telemetry(year, race, session_type, driver, lap)
        if cached_telemetry:
            return cached_telemetry

        # If not in cache, fetch from FastF1
        telemetry = fastf1_service.get_telemetry(year, race, session_type, driver, lap)

        # Store in cache
        cache_service.set_telemetry(year, race, session_type, telemetry)

        return telemetry
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch telemetry: {str(e)}")


@router.get("/session/{year}/{race}/{session_type}/race-control")
async def get_race_control_messages(year: int, race: str, session_type: str):
    """
    Get race control messages (flags, incidents, etc.) for a session

    Returns messages about yellow flags, red flags, safety car, VSC, etc.

    Args:
        year: Season year
        race: Race name or round number
        session_type: Session type - FP1, FP2, FP3, Q, S, R
    """
    try:
        messages = fastf1_service.get_race_control_messages(year, race, session_type)
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch race control messages: {str(e)}")


@router.get("/session/{year}/{race}/{session_type}/track-status")
async def get_track_status(year: int, race: str, session_type: str):
    """
    Get track status data (yellow flags, safety car, VSC, etc.)

    Status codes:
    1 = AllClear (green flag)
    2 = Yellow
    4 = SafetyCar
    5 = Red Flag
    6 = VSC Deployed
    7 = VSC Ending

    Args:
        year: Season year
        race: Race name or round number
        session_type: Session type - FP1, FP2, FP3, Q, S, R
    """
    try:
        track_status = fastf1_service.get_track_status(year, race, session_type)
        return track_status
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch track status: {str(e)}")


@router.get("/session/{year}/{race}/{session_type}/weather")
async def get_weather_data(year: int, race: str, session_type: str):
    """
    Get weather data for a session

    Includes air temp, humidity, pressure, rainfall, track temp, wind direction, wind speed

    Args:
        year: Season year
        race: Race name or round number
        session_type: Session type - FP1, FP2, FP3, Q, S, R
    """
    try:
        weather = fastf1_service.get_weather_data(year, race, session_type)
        return weather
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch weather data: {str(e)}")
