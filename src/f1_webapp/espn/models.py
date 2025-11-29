"""Data models for ESPN F1 API responses."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


@dataclass
class ESPNDriver:
    """Driver profile from ESPN API."""

    id: str
    first_name: str
    last_name: str
    full_name: str
    abbreviation: str
    number: Optional[str]
    team: Optional[str]
    nationality: Optional[str]
    date_of_birth: Optional[datetime]
    headshot_url: Optional[str]

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "ESPNDriver":
        """Create driver from API response."""
        vehicle = data.get("vehicles", [{}])[0] if data.get("vehicles") else {}

        return cls(
            id=data.get("id", ""),
            first_name=data.get("firstName", ""),
            last_name=data.get("lastName", ""),
            full_name=data.get("fullName", ""),
            abbreviation=data.get("abbreviation", ""),
            number=vehicle.get("number"),
            team=vehicle.get("team"),
            nationality=data.get("flag", {}).get("alt"),
            date_of_birth=None,  # Parse if needed
            headshot_url=data.get("headshot", {}).get("href"),
        )


@dataclass
class ESPNStandingsEntry:
    """Single standings entry."""

    position: int
    driver_id: str
    points: float
    wins: int
    poles: int
    behind: float
    starts: int
    top5: int
    top10: int
    dnf: int

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "ESPNStandingsEntry":
        """Create standings entry from API response."""
        stats = {s["name"]: s["value"] for s in data.get("records", [{}])[0].get("stats", [])}

        return cls(
            position=int(stats.get("rank", 0)),
            driver_id=data.get("athlete", {}).get("$ref", "").split("/")[-1],
            points=stats.get("championshipPts", 0),
            wins=int(stats.get("wins", 0)),
            poles=int(stats.get("poles", 0)),
            behind=stats.get("behind", 0),
            starts=int(stats.get("starts", 0)),
            top5=int(stats.get("top5", 0)),
            top10=int(stats.get("top10", 0)),
            dnf=int(stats.get("dnf", 0)),
        )


@dataclass
class ESPNStandings:
    """Championship standings."""

    year: int
    type: str
    entries: List[ESPNStandingsEntry]

    @classmethod
    def from_api(cls, data: Dict[str, Any], year: int) -> "ESPNStandings":
        """Create standings from API response."""
        entries = [
            ESPNStandingsEntry.from_api(standing)
            for standing in data.get("standings", [{}])[0].get("standings", [])
        ]

        return cls(
            year=year,
            type=data.get("displayName", ""),
            entries=entries,
        )


@dataclass
class ESPNEvent:
    """Race event/weekend."""

    id: str
    name: str
    short_name: str
    date: datetime
    end_date: datetime
    circuit_id: Optional[str]
    competitions: List[str]  # Competition IDs

    @classmethod
    def from_api(cls, data: Dict[str, Any]) -> "ESPNEvent":
        """Create event from API response."""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            short_name=data.get("shortName", ""),
            date=datetime.fromisoformat(data.get("date", "").replace("Z", "+00:00")),
            end_date=datetime.fromisoformat(data.get("endDate", "").replace("Z", "+00:00")),
            circuit_id=data.get("circuit", {}).get("$ref", "").split("/")[-1] if data.get("circuit") else None,
            competitions=[
                comp.get("id", "")
                for comp in data.get("competitions", [])
            ],
        )
