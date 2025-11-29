from fastapi import APIRouter, HTTPException
from ..services.espn_service import espn_service
from ..services.cache_service import cache_service

router = APIRouter()


@router.get("/standings/drivers")
async def get_driver_standings(year: int = 2025):
    """
    Get driver championship standings from ESPN with SQLite caching
    """
    try:
        # Try to get from cache first
        cached_data = cache_service.get_driver_standings(year)
        if cached_data:
            return cached_data

        # If not in cache, fetch from ESPN
        espn_data = await espn_service.get_driver_standings(year)

        # Store in cache (keep the original ESPN format)
        cache_service.set_driver_standings(year, espn_data)

        return espn_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch driver standings: {str(e)}")


@router.get("/standings/constructors")
async def get_constructor_standings(year: int = 2025):
    """
    Get constructor/team championship standings from ESPN with SQLite caching
    """
    try:
        # Try to get from cache first
        cached_data = cache_service.get_constructor_standings(year)
        if cached_data:
            return cached_data

        # If not in cache, fetch from ESPN
        espn_data = await espn_service.get_constructor_standings(year)

        # Store in cache (keep the original ESPN format)
        cache_service.set_constructor_standings(year, espn_data)

        return espn_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch constructor standings: {str(e)}")
