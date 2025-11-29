import httpx
from typing import Any
from ..config.settings import get_settings

settings = get_settings()


class ESPNService:
    def __init__(self):
        self.base_url = settings.espn_api_base_url
        self.client = httpx.AsyncClient(timeout=30.0)

    async def close(self):
        await self.client.aclose()

    async def _fetch(self, endpoint: str) -> dict[str, Any]:
        """Fetch data from ESPN API endpoint"""
        url = f"{self.base_url}{endpoint}"
        response = await self.client.get(url)
        response.raise_for_status()
        return response.json()

    async def get_current_season_events(self, year: int = 2025) -> dict[str, Any]:
        """Get all events for the current season"""
        endpoint = f"/seasons/{year}/types/2/events"
        return await self._fetch(endpoint)

    async def get_event_details(self, event_id: str) -> dict[str, Any]:
        """Get detailed information for a specific event"""
        endpoint = f"/events/{event_id}"
        return await self._fetch(endpoint)

    async def get_driver_standings(self, year: int = 2025) -> dict[str, Any]:
        """Get driver championship standings with resolved athlete names"""
        endpoint = f"/seasons/{year}/types/2/standings/0"
        data = await self._fetch(endpoint)

        # Resolve athlete names from $ref URLs
        if "standings" in data:
            for entry in data["standings"]:
                if "athlete" in entry and "$ref" in entry["athlete"]:
                    athlete_url = entry["athlete"]["$ref"]
                    try:
                        athlete_data = await self.client.get(athlete_url)
                        athlete_data.raise_for_status()
                        athlete_info = athlete_data.json()
                        entry["athlete"]["fullName"] = athlete_info.get("fullName", "Unknown")
                        entry["athlete"]["displayName"] = athlete_info.get("displayName", "Unknown")
                    except Exception:
                        entry["athlete"]["fullName"] = "Unknown"
                        entry["athlete"]["displayName"] = "Unknown"

        return data

    async def get_constructor_standings(self, year: int = 2025) -> dict[str, Any]:
        """Get constructor championship standings with resolved team names"""
        endpoint = f"/seasons/{year}/types/2/standings/1"
        data = await self._fetch(endpoint)

        # Resolve manufacturer names from $ref URLs
        if "standings" in data:
            for entry in data["standings"]:
                if "manufacturer" in entry and "$ref" in entry["manufacturer"]:
                    manufacturer_url = entry["manufacturer"]["$ref"]
                    try:
                        manufacturer_data = await self.client.get(manufacturer_url)
                        manufacturer_data.raise_for_status()
                        manufacturer_info = manufacturer_data.json()
                        entry["manufacturer"]["name"] = manufacturer_info.get("name", "Unknown")
                        entry["manufacturer"]["displayName"] = manufacturer_info.get("displayName", "Unknown")
                    except Exception:
                        entry["manufacturer"]["name"] = "Unknown"
                        entry["manufacturer"]["displayName"] = "Unknown"

        return data

    async def get_calendar(self) -> dict[str, Any]:
        """Get F1 calendar information"""
        endpoint = "/calendar/ondays"
        return await self._fetch(endpoint)


# Singleton instance
espn_service = ESPNService()
