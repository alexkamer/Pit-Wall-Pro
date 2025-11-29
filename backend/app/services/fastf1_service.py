import fastf1
from typing import Any
import pandas as pd


class FastF1Service:
    @staticmethod
    def get_session(year: int, race: str | int, session_type: str):
        """
        Get a session object from FastF1

        Args:
            year: Season year
            race: Race number or name
            session_type: 'FP1', 'FP2', 'FP3', 'Q', 'S' (Sprint), 'R' (Race)
        """
        session = fastf1.get_session(year, race, session_type)
        session.load()
        return session

    @staticmethod
    def get_session_results(year: int, race: str | int, session_type: str) -> dict[str, Any]:
        """Get session results as JSON-serializable dict"""
        session = FastF1Service.get_session(year, race, session_type)

        results = session.results
        if results is None or results.empty:
            return {"results": []}

        # Convert to dict and handle NaN values
        results_dict = results.fillna("").to_dict(orient="records")

        return {
            "session_name": session.name,
            "event_name": session.event['EventName'],
            "circuit": session.event['Location'],
            "date": str(session.date),
            "results": results_dict
        }

    @staticmethod
    def get_lap_times(year: int, race: str | int, session_type: str, driver: str | None = None) -> dict[str, Any]:
        """
        Get lap times for a session

        Args:
            driver: Optional driver abbreviation (e.g., 'VER', 'HAM')
        """
        session = FastF1Service.get_session(year, race, session_type)

        if driver:
            laps = session.laps.pick_driver(driver)
        else:
            laps = session.laps

        if laps is None or laps.empty:
            return {"laps": []}

        # Select relevant columns
        lap_data = laps[['Driver', 'LapNumber', 'LapTime', 'Sector1Time',
                        'Sector2Time', 'Sector3Time', 'Compound', 'TyreLife']].copy()

        # Convert timedelta to seconds for JSON serialization
        for col in ['LapTime', 'Sector1Time', 'Sector2Time', 'Sector3Time']:
            if col in lap_data.columns:
                lap_data[col] = lap_data[col].dt.total_seconds()

        lap_data = lap_data.fillna("").to_dict(orient="records")

        return {
            "session_name": session.name,
            "driver": driver,
            "laps": lap_data
        }

    @staticmethod
    def get_fastest_lap(year: int, race: str | int, session_type: str) -> dict[str, Any]:
        """Get fastest lap of the session"""
        session = FastF1Service.get_session(year, race, session_type)

        fastest_lap = session.laps.pick_fastest()
        if fastest_lap is None or fastest_lap.empty:
            return {}

        return {
            "driver": fastest_lap['Driver'],
            "team": fastest_lap['Team'],
            "lap_time": fastest_lap['LapTime'].total_seconds() if pd.notna(fastest_lap['LapTime']) else None,
            "lap_number": int(fastest_lap['LapNumber']) if pd.notna(fastest_lap['LapNumber']) else None,
            "compound": fastest_lap['Compound'] if pd.notna(fastest_lap['Compound']) else None,
        }

    @staticmethod
    def get_telemetry(year: int, race: str | int, session_type: str,
                     driver: str, lap_number: int) -> dict[str, Any]:
        """
        Get telemetry data for a specific lap

        Args:
            driver: Driver abbreviation (e.g., 'VER', 'HAM')
            lap_number: Lap number to get telemetry for
        """
        session = FastF1Service.get_session(year, race, session_type)

        lap = session.laps.pick_driver(driver).pick_lap(lap_number)
        if lap is None or lap.empty:
            return {"telemetry": []}

        telemetry = lap.get_telemetry()
        if telemetry is None or telemetry.empty:
            return {"telemetry": []}

        # Select key telemetry channels
        telem_data = telemetry[['Distance', 'Speed', 'RPM', 'nGear',
                                'Throttle', 'Brake', 'DRS']].copy()

        # Sample data to reduce size (every 10th point)
        telem_data = telem_data.iloc[::10]

        telem_dict = telem_data.fillna(0).to_dict(orient="records")

        return {
            "driver": driver,
            "lap_number": lap_number,
            "lap_time": lap['LapTime'].total_seconds() if pd.notna(lap['LapTime']) else None,
            "telemetry": telem_dict
        }

    @staticmethod
    def get_event_schedule(year: int) -> dict[str, Any]:
        """Get event schedule for a season using FastF1"""
        schedule = fastf1.get_event_schedule(year)

        if schedule is None or schedule.empty:
            return {"events": []}

        # Convert to dict
        schedule_dict = schedule.to_dict(orient="records")

        # Convert timestamps to strings
        for event in schedule_dict:
            for key, value in event.items():
                if pd.notna(value) and hasattr(value, 'isoformat'):
                    event[key] = value.isoformat()
                elif pd.isna(value):
                    event[key] = None

        return {"year": year, "events": schedule_dict}


# Singleton instance
fastf1_service = FastF1Service()
