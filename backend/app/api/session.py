from fastapi import APIRouter, HTTPException, Query
from ..services.fastf1_service import fastf1_service

router = APIRouter()


@router.get("/session/{year}/{race}/{session_type}/results")
async def get_session_results(
    year: int,
    race: str,
    session_type: str
):
    """
    Get session results (finishing order, times, etc.)

    Args:
        year: Season year (e.g., 2024, 2025)
        race: Race name or round number (e.g., 'Monaco', 'Bahrain', 1, 2)
        session_type: Session type - FP1, FP2, FP3, Q, S, R
    """
    try:
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
    Get lap times for a session

    Args:
        year: Season year
        race: Race name or round number
        session_type: Session type - FP1, FP2, FP3, Q, S, R
        driver: Optional driver abbreviation to filter
    """
    try:
        laps = fastf1_service.get_lap_times(year, race, session_type, driver)
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
    Get telemetry data for a specific lap

    Returns speed, RPM, gear, throttle, brake, and DRS data

    Args:
        year: Season year
        race: Race name or round number
        session_type: Session type - FP1, FP2, FP3, Q, S, R
        driver: Driver abbreviation
        lap: Lap number
    """
    try:
        telemetry = fastf1_service.get_telemetry(year, race, session_type, driver, lap)
        return telemetry
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch telemetry: {str(e)}")
