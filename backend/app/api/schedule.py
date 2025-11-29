from fastapi import APIRouter, HTTPException
from ..services.espn_service import espn_service
from ..services.fastf1_service import fastf1_service
from ..services.cache_service import cache_service

router = APIRouter()


@router.get("/schedule")
async def get_schedule(year: int = 2025):
    """
    Get race schedule for the season

    Uses FastF1 for comprehensive schedule information with SQLite caching
    """
    try:
        # Try to get from cache first
        cached_schedule = cache_service.get_event_schedule(year)
        if cached_schedule:
            return cached_schedule

        # If not in cache, fetch from FastF1
        schedule = fastf1_service.get_event_schedule(year)

        # Store in cache
        cache_service.set_event_schedule(year, schedule)

        return schedule
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch schedule: {str(e)}")


@router.get("/schedule/espn")
async def get_espn_schedule(year: int = 2025):
    """
    Get race schedule from ESPN API

    Alternative endpoint using ESPN data
    """
    try:
        events = await espn_service.get_current_season_events(year)
        return events
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch ESPN schedule: {str(e)}")


@router.get("/events/{event_id}")
async def get_event(event_id: str):
    """
    Get detailed information about a specific event from ESPN
    """
    try:
        event = await espn_service.get_event_details(event_id)
        return event
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch event: {str(e)}")
