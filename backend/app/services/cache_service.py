from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Any
import json
import pandas as pd
from ..db.database import get_db
from ..db.models import (
    EventSchedule,
    Session as SessionModel,
    SessionResult,
    LapTime,
    TelemetryData,
    DriverStanding,
    ConstructorStanding,
)


class CacheService:
    """Service for caching F1 data in SQLite"""

    def __init__(self, cache_ttl_hours: int = 24):
        """
        Initialize cache service

        Args:
            cache_ttl_hours: Time to live for cache entries in hours (default 24)
        """
        self.cache_ttl = timedelta(hours=cache_ttl_hours)

    def _is_cache_valid(self, cached_at: datetime) -> bool:
        """Check if cache entry is still valid"""
        if cached_at is None:
            return False
        return datetime.utcnow() - cached_at < self.cache_ttl

    @staticmethod
    def _sanitize_value(value):
        """Convert pandas NaT, empty strings, and other problematic values to None"""
        if pd.isna(value):
            return None
        if isinstance(value, pd.Timestamp):
            return value.to_pydatetime()
        if isinstance(value, str) and value.strip() == '':
            return None
        return value

    # Event Schedule Cache

    def get_event_schedule(self, year: int) -> dict[str, Any] | None:
        """Get cached event schedule"""
        db = get_db()
        try:
            schedules = db.query(EventSchedule).filter(EventSchedule.year == year).all()

            if not schedules:
                return None

            # Check if cache is valid
            if not self._is_cache_valid(schedules[0].cached_at):
                return None

            events = []
            for schedule in schedules:
                event = {
                    "RoundNumber": schedule.round_number,
                    "EventName": schedule.event_name,
                    "Location": schedule.location,
                    "Country": schedule.country,
                    "EventDate": schedule.event_date.isoformat() if schedule.event_date else None,
                    "EventFormat": schedule.event_format,
                    "Session1": schedule.session1_date.isoformat() if schedule.session1_date else None,
                    "Session2": schedule.session2_date.isoformat() if schedule.session2_date else None,
                    "Session3": schedule.session3_date.isoformat() if schedule.session3_date else None,
                    "Qualifying": schedule.qualifying_date.isoformat() if schedule.qualifying_date else None,
                    "Sprint": schedule.sprint_date.isoformat() if schedule.sprint_date else None,
                    "Race": schedule.race_date.isoformat() if schedule.race_date else None,
                }
                events.append(event)

            return {"year": year, "events": events}
        finally:
            db.close()

    def set_event_schedule(self, year: int, schedule_data: dict[str, Any]):
        """Cache event schedule"""
        db = get_db()
        try:
            # Delete old schedule for this year
            db.query(EventSchedule).filter(EventSchedule.year == year).delete()

            # Helper function to safely parse ISO date
            def parse_iso_date(date_str):
                if not date_str:
                    return None
                try:
                    return datetime.fromisoformat(date_str)
                except (ValueError, TypeError):
                    return None

            # Insert new schedule
            for event in schedule_data.get("events", []):
                schedule = EventSchedule(
                    year=year,
                    round_number=event.get("RoundNumber"),
                    event_name=event.get("EventName"),
                    location=event.get("Location"),
                    country=event.get("Country"),
                    event_date=parse_iso_date(event.get("EventDate")),
                    event_format=event.get("EventFormat"),
                    session1_date=parse_iso_date(event.get("Session1")),
                    session2_date=parse_iso_date(event.get("Session2")),
                    session3_date=parse_iso_date(event.get("Session3")),
                    qualifying_date=parse_iso_date(event.get("Qualifying")),
                    sprint_date=parse_iso_date(event.get("Sprint")),
                    race_date=parse_iso_date(event.get("Race")),
                )
                db.add(schedule)

            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    # Session Cache

    def _get_or_create_session(self, db: Session, year: int, race: str, session_type: str) -> int:
        """Get or create session and return session_id"""
        session = db.query(SessionModel).filter(
            SessionModel.year == year,
            SessionModel.race == str(race),
            SessionModel.session_type == session_type
        ).first()

        if session:
            return session.id

        # Create new session
        session = SessionModel(
            year=year,
            race=str(race),
            session_type=session_type
        )
        db.add(session)
        db.flush()
        return session.id

    def get_session_results(self, year: int, race: str, session_type: str) -> dict[str, Any] | None:
        """Get cached session results"""
        db = get_db()
        try:
            session = db.query(SessionModel).filter(
                SessionModel.year == year,
                SessionModel.race == str(race),
                SessionModel.session_type == session_type
            ).first()

            if not session or not self._is_cache_valid(session.cached_at):
                return None

            results = db.query(SessionResult).filter(
                SessionResult.session_id == session.id
            ).order_by(SessionResult.position).all()

            if not results:
                return None

            results_list = []
            for result in results:
                result_dict = {
                    "Position": result.position,
                    "DriverNumber": result.driver_number,
                    "Abbreviation": result.driver_abbreviation,
                    "FullName": result.driver_name,
                    "TeamName": result.team_name,
                    "GridPosition": result.grid_position,
                    "Q1": result.q1_time,
                    "Q2": result.q2_time,
                    "Q3": result.q3_time,
                    "Time": result.race_time,
                    "Status": result.status,
                    "Points": result.points,
                }
                results_list.append(result_dict)

            return {
                "session_name": session.session_name,
                "event_name": session.event_name,
                "circuit": session.circuit,
                "date": session.session_date.isoformat() if session.session_date else None,
                "results": results_list
            }
        finally:
            db.close()

    def set_session_results(self, year: int, race: str, session_type: str, results_data: dict[str, Any]):
        """Cache session results"""
        db = get_db()
        try:
            session_id = self._get_or_create_session(db, year, race, session_type)

            # Update session metadata
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            session.session_name = results_data.get("session_name")
            session.event_name = results_data.get("event_name")
            session.circuit = results_data.get("circuit")
            session.session_date = datetime.fromisoformat(results_data["date"]) if results_data.get("date") else None
            session.cached_at = datetime.utcnow()

            # Delete old results
            db.query(SessionResult).filter(SessionResult.session_id == session_id).delete()

            # Insert new results
            for result in results_data.get("results", []):
                session_result = SessionResult(
                    session_id=session_id,
                    position=self._sanitize_value(result.get("Position")),
                    driver_number=self._sanitize_value(result.get("DriverNumber")),
                    driver_abbreviation=self._sanitize_value(result.get("Abbreviation")),
                    driver_name=self._sanitize_value(result.get("FullName")),
                    team_name=self._sanitize_value(result.get("TeamName")),
                    grid_position=self._sanitize_value(result.get("GridPosition")),
                    q1_time=self._sanitize_value(result.get("Q1")),
                    q2_time=self._sanitize_value(result.get("Q2")),
                    q3_time=self._sanitize_value(result.get("Q3")),
                    race_time=self._sanitize_value(result.get("Time")),
                    status=self._sanitize_value(result.get("Status")),
                    points=self._sanitize_value(result.get("Points")),
                )
                db.add(session_result)

            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    # Lap Times Cache

    def get_lap_times(self, year: int, race: str, session_type: str, driver: str | None = None) -> dict[str, Any] | None:
        """Get cached lap times"""
        db = get_db()
        try:
            session = db.query(SessionModel).filter(
                SessionModel.year == year,
                SessionModel.race == str(race),
                SessionModel.session_type == session_type
            ).first()

            if not session or not self._is_cache_valid(session.cached_at):
                return None

            query = db.query(LapTime).filter(LapTime.session_id == session.id)
            if driver:
                query = query.filter(LapTime.driver_abbreviation == driver)

            laps = query.order_by(LapTime.lap_number).all()

            if not laps:
                return None

            laps_list = []
            for lap in laps:
                lap_dict = {
                    "Driver": lap.driver_abbreviation,
                    "LapNumber": lap.lap_number,
                    "LapTime": lap.lap_time,
                    "Sector1Time": lap.sector1_time,
                    "Sector2Time": lap.sector2_time,
                    "Sector3Time": lap.sector3_time,
                    "Compound": lap.compound,
                    "TyreLife": lap.tyre_life,
                }
                laps_list.append(lap_dict)

            return {
                "session_name": session.session_name,
                "driver": driver,
                "laps": laps_list
            }
        finally:
            db.close()

    def set_lap_times(self, year: int, race: str, session_type: str, lap_data: dict[str, Any]):
        """Cache lap times"""
        db = get_db()
        try:
            session_id = self._get_or_create_session(db, year, race, session_type)

            # Update session metadata
            session = db.query(SessionModel).filter(SessionModel.id == session_id).first()
            session.session_name = lap_data.get("session_name")
            session.cached_at = datetime.utcnow()

            # Delete old lap times for this session (or driver if specified)
            delete_query = db.query(LapTime).filter(LapTime.session_id == session_id)
            if lap_data.get("driver"):
                delete_query = delete_query.filter(LapTime.driver_abbreviation == lap_data["driver"])
            delete_query.delete()

            # Insert new lap times
            for lap in lap_data.get("laps", []):
                lap_time = LapTime(
                    session_id=session_id,
                    driver_abbreviation=self._sanitize_value(lap.get("Driver")),
                    lap_number=self._sanitize_value(lap.get("LapNumber")),
                    lap_time=self._sanitize_value(lap.get("LapTime")),
                    sector1_time=self._sanitize_value(lap.get("Sector1Time")),
                    sector2_time=self._sanitize_value(lap.get("Sector2Time")),
                    sector3_time=self._sanitize_value(lap.get("Sector3Time")),
                    compound=self._sanitize_value(lap.get("Compound")),
                    tyre_life=self._sanitize_value(lap.get("TyreLife")),
                )
                db.add(lap_time)

            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    # Telemetry Cache

    def get_telemetry(self, year: int, race: str, session_type: str, driver: str, lap_number: int) -> dict[str, Any] | None:
        """Get cached telemetry"""
        db = get_db()
        try:
            session = db.query(SessionModel).filter(
                SessionModel.year == year,
                SessionModel.race == str(race),
                SessionModel.session_type == session_type
            ).first()

            if not session or not self._is_cache_valid(session.cached_at):
                return None

            telemetry = db.query(TelemetryData).filter(
                TelemetryData.session_id == session.id,
                TelemetryData.driver_abbreviation == driver,
                TelemetryData.lap_number == lap_number
            ).first()

            if not telemetry:
                return None

            return {
                "driver": telemetry.driver_abbreviation,
                "lap_number": telemetry.lap_number,
                "lap_time": telemetry.lap_time,
                "telemetry": json.loads(telemetry.telemetry_json)
            }
        finally:
            db.close()

    def set_telemetry(self, year: int, race: str, session_type: str, telemetry_data: dict[str, Any]):
        """Cache telemetry"""
        db = get_db()
        try:
            session_id = self._get_or_create_session(db, year, race, session_type)

            # Delete old telemetry
            db.query(TelemetryData).filter(
                TelemetryData.session_id == session_id,
                TelemetryData.driver_abbreviation == telemetry_data["driver"],
                TelemetryData.lap_number == telemetry_data["lap_number"]
            ).delete()

            # Insert new telemetry
            telemetry = TelemetryData(
                session_id=session_id,
                driver_abbreviation=telemetry_data["driver"],
                lap_number=telemetry_data["lap_number"],
                lap_time=telemetry_data.get("lap_time"),
                telemetry_json=json.dumps(telemetry_data.get("telemetry", []))
            )
            db.add(telemetry)

            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    # Driver Standings Cache

    def get_driver_standings(self, year: int) -> dict[str, Any] | None:
        """Get cached driver standings (returns ESPN format with standings array)"""
        db = get_db()
        try:
            # Check if we have any standings for this year
            first_standing = db.query(DriverStanding).filter(
                DriverStanding.year == year
            ).first()

            if not first_standing or not self._is_cache_valid(first_standing.cached_at):
                return None

            # Get all standings for this year
            standings = db.query(DriverStanding).filter(
                DriverStanding.year == year
            ).order_by(DriverStanding.position).all()

            # Reconstruct ESPN format
            standings_list = []
            for idx, s in enumerate(standings):
                entry = {
                    "athlete": {
                        "displayName": s.driver_name,
                        "fullName": s.driver_name,
                    },
                    "records": [{
                        "stats": [
                            {"name": "rank", "displayValue": str(s.position or idx + 1)},
                            {"name": "championshipPts", "displayValue": str(s.points or 0)},
                            {"name": "wins", "displayValue": str(s.wins or 0)},
                        ]
                    }]
                }
                standings_list.append(entry)

            return {"standings": standings_list}
        finally:
            db.close()

    def set_driver_standings(self, year: int, espn_data: dict[str, Any]):
        """Cache driver standings from ESPN format"""
        db = get_db()
        try:
            # Delete old standings
            db.query(DriverStanding).filter(DriverStanding.year == year).delete()

            # Extract and insert new standings
            if "standings" in espn_data:
                for idx, entry in enumerate(espn_data["standings"]):
                    # Extract data from ESPN format
                    records = entry.get("records", [{}])[0]
                    stats = records.get("stats", [])

                    rank_stat = next((s for s in stats if s.get("name") == "rank"), {})
                    points_stat = next((s for s in stats if s.get("name") == "championshipPts"), {})
                    wins_stat = next((s for s in stats if s.get("name") == "wins"), {})

                    position = int(rank_stat.get("displayValue", idx + 1))
                    points_val = points_stat.get("displayValue", "0")
                    wins_val = wins_stat.get("displayValue", "0")

                    driver_name = entry.get("athlete", {}).get("displayName") or entry.get("athlete", {}).get("fullName", "Unknown")

                    driver_standing = DriverStanding(
                        year=year,
                        position=position,
                        driver_name=driver_name,
                        team_name="",  # ESPN doesn't provide team in standings
                        points=float(points_val) if points_val else 0,
                        wins=int(wins_val) if wins_val else 0,
                    )
                    db.add(driver_standing)

            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()

    # Constructor Standings Cache

    def get_constructor_standings(self, year: int) -> dict[str, Any] | None:
        """Get cached constructor standings (returns ESPN format with standings array)"""
        db = get_db()
        try:
            # Check if we have any standings for this year
            first_standing = db.query(ConstructorStanding).filter(
                ConstructorStanding.year == year
            ).first()

            if not first_standing or not self._is_cache_valid(first_standing.cached_at):
                return None

            # Get all standings for this year
            standings = db.query(ConstructorStanding).filter(
                ConstructorStanding.year == year
            ).order_by(ConstructorStanding.position).all()

            # Reconstruct ESPN format
            standings_list = []
            for idx, s in enumerate(standings):
                entry = {
                    "manufacturer": {
                        "displayName": s.team_name,
                        "name": s.team_name,
                    },
                    "records": [{
                        "stats": [
                            {"name": "rank", "displayValue": str(s.position or idx + 1)},
                            {"name": "championshipPts", "displayValue": str(s.points or 0)},
                            {"name": "wins", "displayValue": str(s.wins or 0)},
                        ]
                    }]
                }
                standings_list.append(entry)

            return {"standings": standings_list}
        finally:
            db.close()

    def set_constructor_standings(self, year: int, espn_data: dict[str, Any]):
        """Cache constructor standings from ESPN format"""
        db = get_db()
        try:
            # Delete old standings
            db.query(ConstructorStanding).filter(ConstructorStanding.year == year).delete()

            # Extract and insert new standings
            if "standings" in espn_data:
                for idx, entry in enumerate(espn_data["standings"]):
                    # Extract data from ESPN format
                    records = entry.get("records", [{}])[0]
                    stats = records.get("stats", [])

                    rank_stat = next((s for s in stats if s.get("name") == "rank"), {})
                    points_stat = next((s for s in stats if s.get("name") == "championshipPts"), {})
                    wins_stat = next((s for s in stats if s.get("name") == "wins"), {})

                    position = int(rank_stat.get("displayValue", idx + 1))
                    points_val = points_stat.get("displayValue", "0")
                    wins_val = wins_stat.get("displayValue", "0")

                    team_name = entry.get("manufacturer", {}).get("displayName") or entry.get("manufacturer", {}).get("name", "Unknown")

                    constructor_standing = ConstructorStanding(
                        year=year,
                        position=position,
                        team_name=team_name,
                        points=float(points_val) if points_val else 0,
                        wins=int(wins_val) if wins_val else 0,
                    )
                    db.add(constructor_standing)

            db.commit()
        except Exception as e:
            db.rollback()
            raise e
        finally:
            db.close()


# Singleton instance
cache_service = CacheService(cache_ttl_hours=24)
