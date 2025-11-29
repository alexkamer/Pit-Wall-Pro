from fastapi import APIRouter, HTTPException
from ..services.espn_service import espn_service

router = APIRouter()


@router.get("/standings/drivers")
async def get_driver_standings(year: int = 2025):
    """
    Get driver championship standings from ESPN
    """
    try:
        standings = await espn_service.get_driver_standings(year)
        return standings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch driver standings: {str(e)}")


@router.get("/standings/constructors")
async def get_constructor_standings(year: int = 2025):
    """
    Get constructor/team championship standings from ESPN
    """
    try:
        standings = await espn_service.get_constructor_standings(year)
        return standings
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch constructor standings: {str(e)}")
