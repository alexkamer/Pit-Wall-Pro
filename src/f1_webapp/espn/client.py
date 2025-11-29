"""ESPN F1 API client implementation."""

import requests
from typing import Optional, Dict, Any, List
from datetime import datetime


class ESPNClient:
    """Client for ESPN F1 API.

    Usage:
        client = ESPNClient()
        standings = client.get_season_standings(2024)
        driver = client.get_driver(4665)  # Max Verstappen
    """

    BASE_URL = "https://sports.core.api.espn.com/v2/sports/racing"

    def __init__(self, language: str = "en", region: str = "us"):
        """Initialize ESPN F1 API client.

        Args:
            language: Language code (default: 'en')
            region: Region code (default: 'us')
        """
        self.language = language
        self.region = region
        self.session = requests.Session()

    def _build_url(self, path: str, params: Optional[Dict[str, Any]] = None) -> str:
        """Build full URL with query parameters."""
        base = f"{self.BASE_URL}{path}"
        default_params = {"lang": self.language, "region": self.region}
        if params:
            default_params.update(params)

        param_str = "&".join([f"{k}={v}" for k, v in default_params.items()])
        return f"{base}?{param_str}"

    def _get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make GET request to ESPN API."""
        url = self._build_url(path, params)
        response = self.session.get(url, timeout=10)
        response.raise_for_status()
        return response.json()

    # Leagues & Seasons

    def get_f1_league(self) -> Dict[str, Any]:
        """Get F1 league information including current season."""
        return self._get("/leagues/f1")

    def get_seasons(self) -> Dict[str, Any]:
        """Get list of all F1 seasons."""
        return self._get("/leagues/f1/seasons")

    def get_season(self, year: int) -> Dict[str, Any]:
        """Get specific season information.

        Args:
            year: Season year (e.g., 2024)
        """
        return self._get(f"/leagues/f1/seasons/{year}")

    # Events & Races

    def get_events(self, season: Optional[int] = None, limit: int = 100) -> Dict[str, Any]:
        """Get F1 events.

        Args:
            season: Optional season year (e.g., 2024) to get all events for that season
            limit: Maximum number of events to return (default: 100)

        Returns:
            Dict containing event items
        """
        params = {"limit": limit}
        if season:
            params["dates"] = season

        return self._get("/leagues/f1/events", params=params)

    def get_event(self, event_id: str) -> Dict[str, Any]:
        """Get detailed event information.

        Args:
            event_id: Event ID (e.g., '600052107')
        """
        return self._get(f"/leagues/f1/events/{event_id}")

    def get_competition(self, event_id: str, competition_id: str) -> Dict[str, Any]:
        """Get competition (session) details.

        Args:
            event_id: Event ID
            competition_id: Competition ID (session)
        """
        return self._get(
            f"/leagues/f1/events/{event_id}/competitions/{competition_id}"
        )

    # Standings

    def get_standings_types(self, year: int) -> Dict[str, Any]:
        """Get available standings types for a season.

        Args:
            year: Season year

        Returns:
            Dict with driver (id=0) and constructor (id=1) standings
        """
        return self._get(f"/leagues/f1/seasons/{year}/types/2/standings")

    def get_driver_standings(self, year: int) -> Dict[str, Any]:
        """Get driver championship standings.

        Args:
            year: Season year (e.g., 2024)
        """
        return self._get(f"/leagues/f1/seasons/{year}/types/2/standings/0")

    def get_constructor_standings(self, year: int) -> Dict[str, Any]:
        """Get constructor championship standings.

        Args:
            year: Season year (e.g., 2024)
        """
        return self._get(f"/leagues/f1/seasons/{year}/types/2/standings/1")

    # Athletes (Drivers)

    def get_driver(self, driver_id: str) -> Dict[str, Any]:
        """Get driver profile information.

        Args:
            driver_id: Driver ID (e.g., '4665' for Verstappen)
        """
        return self._get(f"/athletes/{driver_id}")

    def get_season_drivers(self, year: int) -> Dict[str, Any]:
        """Get all drivers for a specific season.

        Args:
            year: Season year
        """
        return self._get(f"/leagues/f1/seasons/{year}/athletes")

    # Helper methods

    def get_current_season(self) -> int:
        """Get current season year."""
        league = self.get_f1_league()
        return league.get("season", {}).get("year", datetime.now().year)

    def get_driver_stats(
        self,
        driver_id: str,
        year: int,
        record_id: str = "0"
    ) -> Dict[str, Any]:
        """Get driver statistics for a season.

        Args:
            driver_id: Driver ID
            year: Season year
            record_id: Record ID (default: '0' for overall)
        """
        return self._get(
            f"/leagues/f1/seasons/{year}/types/2/athletes/{driver_id}/records/{record_id}"
        )


# Example usage
if __name__ == "__main__":
    client = ESPNClient()

    # Get current standings
    standings = client.get_driver_standings(2024)
    print(f"Driver Standings: {standings['displayName']}")

    # Get driver profile
    verstappen = client.get_driver("4665")
    print(f"\nDriver: {verstappen['fullName']}")
    print(f"Team: {verstappen['vehicles'][0]['team']}")
